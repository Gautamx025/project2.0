from dataclasses import replace
import json
import httpx
import pytest
from pydantic import ValidationError
from backend.app import adapters, config
from backend.app.adapters import Price, Store, execute, extract_inr, store_payload
from backend.app.demo import demo_vision
from backend.app.models import VisionOutput

def test_strict_vision_schema_rejects_missing_extra_and_wrong_types():
    valid = demo_vision('watch').model_dump()
    assert VisionOutput.model_validate(valid).category == 'Watches'
    for changed in ({**valid, 'tags': 'watch'}, {**valid, 'unexpected': True}, {key: value for key, value in valid.items() if key != 'hindi'}):
        with pytest.raises(ValidationError):
            VisionOutput.model_validate(changed)

async def test_failure_retries_then_falls_back_with_visible_reason():
    class Broken:
        name, available, count = 'test-provider', True, 0
        async def live(self):
            self.count += 1
            raise httpx.ConnectError('secret raw content should not be returned')
        async def fallback(self):
            return 'offline result'
    adapter = Broken()
    notices = []
    result = await execute(adapter, replace(config.settings(), demo=False), on_retry=lambda attempt, reason: notices.append(attempt))
    assert result.value == 'offline result' and result.demo
    assert adapter.count == 2 and notices == [1, 2]
    assert result.attempts == 2 and 'Local demo fallback' in result.reason
    assert 'secret raw content' not in result.reason

async def test_missing_key_never_calls_live_provider():
    class Missing:
        name, available = 'missing', False
        async def live(self):
            raise AssertionError('Must not call paid provider without a key')
        async def fallback(self):
            return 42
    result = await execute(Missing(), replace(config.settings(), demo=False))
    assert result.demo and result.value == 42 and 'missing' in result.reason

@pytest.mark.parametrize('text,expected', [('₹1,299.50', 1299.5), ('Rs. 749', 749), ('INR 2,999', 2999), ('$25 4.8 rating', None), ('bottle 750 ml', None)])
def test_price_parser_only_explicit_inr(text, expected):
    assert extract_inr(text) == expected

async def test_price_sources_median_and_cache(isolated_environment, monkeypatch):
    calls = []
    async def handler(request):
        calls.append(request)
        return httpx.Response(200, json={'results': [{'title': 'Offer A', 'url': 'https://shop-a.example/bottle', 'content': 'Buy at ₹500'}, {'title': 'Offer B', 'url': 'https://shop-b.example/bottle', 'content': 'Price INR 900'}, {'title': 'No price', 'url': 'https://shop-c.example', 'content': '4.8 stars; 750 ml'}]})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        monkeypatch.setattr(adapters, 'client', lambda: http)
        price = Price('tavily', isolated_environment)
        first = await price.live('Steel bottle', 'bottle')
        second = await price.live('Steel bottle', 'bottle')
    assert (first.low, first.median, first.high) == (500, 700, 900)
    assert len(first.sources) == 2 and all(not source.demo for source in first.sources)
    assert second.cached and len(calls) == 1

def test_draft_payloads_escape_copy_and_keep_explicit_status(ready):
    listing = ready['result']
    listing['copy']['description'] = '<script>alert(1)</script>'
    shopify = store_payload(listing, 'shopify', 'https://catalog.example.org')
    woo = store_payload(listing, 'woocommerce', 'https://catalog.example.org')
    assert shopify['product']['status'] == 'DRAFT' and woo['status'] == 'draft'
    assert '<script>' not in shopify['product']['descriptionHtml']
    assert '&lt;script&gt;' in woo['description']
    assert woo['regular_price'] == '749.00'

async def test_real_shopify_contract_creates_draft_then_sets_variant(ready, monkeypatch):
    monkeypatch.setenv('DEMO_MODE', 'false')
    monkeypatch.setenv('SHOPIFY_DOMAIN', 'neuralshift-test.myshopify.com')
    monkeypatch.setenv('SHOPIFY_ACCESS_TOKEN', 'test-token')
    seen = []
    async def handler(request):
        body = json.loads(request.content)
        seen.append(body)
        if body['query'].startswith('query'):
            return httpx.Response(200, json={'data': {'shop': {'name': 'Test shop', 'currencyCode': 'INR'}}})
        if 'CreateDraft' in body['query']:
            assert body['variables']['product']['status'] == 'DRAFT'
            return httpx.Response(200, json={'data': {'productCreate': {'product': {'id': 'gid://shopify/Product/123', 'status': 'DRAFT', 'variants': {'nodes': [{'id': 'gid://shopify/ProductVariant/456'}]}}, 'userErrors': []}}})
        assert body['variables']['variants'][0]['price'] == '749.00'
        return httpx.Response(200, json={'data': {'productVariantsBulkUpdate': {'productVariants': [{'id': '456', 'price': '749.00'}], 'userErrors': []}}})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        monkeypatch.setattr(adapters, 'client', lambda: http)
        result = await Store(config.settings()).publish(ready['result'], 'shopify')
    assert not result['demo'] and result['id'] == 'gid://shopify/Product/123'
    assert result['price_synced'] and len(seen) == 3

async def test_woocommerce_contract_posts_only_draft(ready, monkeypatch):
    monkeypatch.setenv('DEMO_MODE', 'false')
    monkeypatch.setenv('WOOCOMMERCE_URL', 'https://shop.example.org')
    monkeypatch.setenv('WOOCOMMERCE_KEY', 'ck_test')
    monkeypatch.setenv('WOOCOMMERCE_SECRET', 'cs_test')
    calls = []
    async def handler(request):
        calls.append(request)
        if request.url.path.endswith('/products/tags'):
            return httpx.Response(200, json=[{'id': 42, 'name': request.url.params['search']}])
        if request.method == 'GET':
            return httpx.Response(200, json={'value': 'INR'})
        body = json.loads(request.content)
        assert body['status'] == 'draft' and body['regular_price'] == '749.00'
        assert body['tags'] == [{'id': 42}, {'id': 42}, {'id': 42}]
        assert request.headers['Authorization'].startswith('Basic ')
        return httpx.Response(201, json={'id': 77, 'status': 'draft'})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        monkeypatch.setattr(adapters, 'client', lambda: http)
        result = await Store(config.settings()).publish(ready['result'], 'woocommerce')
    assert not result['demo'] and result['id'] == '77' and len(calls) == 5
