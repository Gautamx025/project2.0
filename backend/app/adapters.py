"""Provider boundaries. Live calls are bounded; every fallback carries its reason."""
import asyncio
import base64
import hashlib
import html
import json
import os
import re
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlparse
import httpx
from PIL import Image, ImageChops
from .config import Settings
from .demo import demo_prices, demo_vision
from .imaging import compose_variant, demo_cutout
from .models import Comparable, PriceRange, VisionOutput
from .repository import Repository
from .config import ROOT

class SegmentationProvider(Protocol):
    async def live(self, source: Path, destination: Path) -> str: ...
    async def fallback(self, source: Path, destination: Path) -> str: ...

class BackgroundProvider(Protocol):
    async def live(self, source: Path, destination: Path, style: str) -> str: ...
    async def fallback(self, source: Path, destination: Path, style: str) -> str: ...

class VisionProvider(Protocol):
    async def live(self, sources: list[Path], key: str) -> VisionOutput: ...
    async def fallback(self, sources: list[Path], key: str) -> VisionOutput: ...

class PriceProvider(Protocol):
    async def live(self, title: str, key: str) -> PriceRange: ...
    async def fallback(self, title: str, key: str) -> PriceRange: ...

class StoreProvider(Protocol):
    async def publish(self, listing: dict, channel: str) -> dict: ...
    async def test(self, channel: str) -> dict: ...

_clients: dict[asyncio.AbstractEventLoop, httpx.AsyncClient] = {}

def client() -> httpx.AsyncClient:
    loop = asyncio.get_running_loop()
    if loop not in _clients:
        _clients[loop] = httpx.AsyncClient(timeout=22, follow_redirects=True)
    return _clients[loop]

async def close_clients():
    for instance in list(_clients.values()):
        await instance.aclose()
    _clients.clear()

def data_uri(path: Path) -> str:
    mime = 'image/png' if path.suffix == '.png' else 'image/jpeg'
    return f'data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}'

async def download(url: str, destination: Path) -> str:
    response = await client().get(url)
    response.raise_for_status()
    # Decode to verify a provider didn't return an HTML error page.
    import io
    image = Image.open(io.BytesIO(response.content)).convert('RGBA')
    image.thumbnail((1400, 1400))
    await asyncio.to_thread(image.save, destination)
    return str(destination)

async def replicate(input_data: dict, *, model: str = '', version: str = '') -> Any:
    headers = {'Authorization': f'Bearer {os.getenv("REPLICATE_API_TOKEN", "")}', 'Prefer': 'wait=10'}
    url = f'https://api.replicate.com/v1/models/{model}/predictions' if model else 'https://api.replicate.com/v1/predictions'
    response = await client().post(url, headers=headers, json={'input': input_data, **({'version': version} if version else {})})
    response.raise_for_status()
    prediction = response.json()
    try:
        while prediction.get('status') not in {'succeeded', 'failed', 'canceled'}:
            await asyncio.sleep(.7)
            response = await client().get(prediction['urls']['get'], headers=headers)
            response.raise_for_status()
            prediction = response.json()
        if prediction['status'] != 'succeeded':
            raise ValueError('Hosted model did not produce an image.')
        return prediction['output']
    except asyncio.CancelledError:
        if prediction.get('urls', {}).get('cancel'):
            try:
                await client().post(prediction['urls']['cancel'], headers=headers)
            except httpx.HTTPError:
                pass
        raise

@dataclass
class Result:
    value: Any
    demo: bool
    provider: str
    reason: str = ''
    attempts: int = 0

async def execute(adapter: Any, config: Settings, *args, on_retry=None) -> Result:
    if config.demo or not adapter.available:
        reason = 'Demo mode is on.' if config.demo else f'{adapter.name} credentials are missing.'
        return Result(await adapter.fallback(*args), True, adapter.name, reason)
    last_reason = ''
    for attempt in range(1, config.attempts + 1):
        try:
            value = await asyncio.wait_for(adapter.live(*args), timeout=config.timeout)
            return Result(value, False, adapter.name, attempts=attempt)
        except (httpx.HTTPError, ValueError, KeyError, TypeError, OSError, TimeoutError) as exc:
            # Never surface raw request bodies/URLs because they can contain secrets.
            code = f' HTTP {exc.response.status_code}' if isinstance(exc, httpx.HTTPStatusError) else ''
            last_reason = f'{adapter.name} failed ({type(exc).__name__}{code}).'
            if on_retry:
                on_retry(attempt, last_reason)
            if attempt < config.attempts:
                await asyncio.sleep(.35 * 2**(attempt-1))
    return Result(await adapter.fallback(*args), True, adapter.name, last_reason + ' Local demo fallback used.', config.attempts)

class Segmentation:
    def __init__(self, provider: str, sample_key: str = 'custom'):
        self.name = provider + ' / foreground isolation'
        self.provider = provider
        self.sample_key = sample_key
        self.available = bool(os.getenv('FAL_KEY')) if provider == 'fal' else bool(os.getenv('REPLICATE_API_TOKEN') and os.getenv('REPLICATE_SAM_VERSION')) if provider == 'replicate' else True

    async def live(self, source: Path, destination: Path) -> str:
        if self.provider == 'rembg':
            try:
                from rembg import remove, new_session
            except ImportError as exc:
                raise ValueError('Install optional rembg requirements first.') from exc
            global _rembg_session
            if '_rembg_session' not in globals():
                os.environ.setdefault('U2NET_HOME', str(ROOT/'data'/'models'))
                _rembg_session = await asyncio.to_thread(new_session, os.getenv('REMBG_MODEL', 'u2netp'))
            result = await asyncio.to_thread(remove, source.read_bytes(), session=_rembg_session)
            destination.write_bytes(result)
            return str(destination)
        if self.provider == 'fal':
            image = Image.open(source)
            response = await client().post('https://fal.run/' + os.getenv('FAL_SAM_MODEL', 'fal-ai/sam2/image'), headers={'Authorization': f'Key {os.getenv("FAL_KEY")}'}, json={'image_url': data_uri(source), 'prompts': [{'x': image.width//2, 'y': image.height//2, 'label': 1}], 'apply_mask': True, 'output_format': 'png'})
            response.raise_for_status()
            return await download(response.json()['image']['url'], destination)
        output = await replicate({'image': data_uri(source)}, version=os.getenv('REPLICATE_SAM_VERSION', ''))
        masks = output.get('individual_masks', [])
        if not masks:
            raise ValueError('SAM returned no foreground mask.')
        # Prefer the mask covering the image center rather than a colored visualization.
        import io
        original = Image.open(source).convert('RGBA')
        candidates = []
        for url in masks[:12]:
            response = await client().get(url)
            response.raise_for_status()
            mask = Image.open(io.BytesIO(response.content)).convert('L').resize(original.size)
            if mask.getpixel((mask.width//2, mask.height//2)) > 127:
                candidates.append(mask)
        if not candidates:
            raise ValueError('No mask covers the product center.')
        mask = min(candidates, key=lambda item: sum(item.histogram()[128:]))
        original.putalpha(mask)
        original.save(destination)
        return str(destination)

    async def fallback(self, source: Path, destination: Path) -> str:
        precomputed = ROOT/'frontend'/'public'/'samples'/f'{self.sample_key}-cutout.png'
        if self.sample_key in {'bottle', 'watch', 'bag'} and precomputed.exists():
            import shutil
            await asyncio.to_thread(shutil.copyfile, precomputed, destination)
            return str(destination)
        # Prefer true local rembg if installed and the hosted path is unavailable.
        if self.provider != 'rembg' and os.getenv('DEMO_MODE', 'true').lower() != 'true':
            try:
                return await asyncio.wait_for(Segmentation('rembg').live(source, destination), timeout=15)
            except (ValueError, OSError, TimeoutError):
                pass
        return await asyncio.to_thread(demo_cutout, source, destination)

STYLE_PROMPTS = {
    'studio': 'clean warm white studio, neutral seamless paper, accurate product, no text',
    'shadow': 'warm stone surface, soft natural shadow, editorial studio photograph, no text',
    'lifestyle': 'sunlit small home interior, wood tabletop, soft window light, no text',
    'color': 'muted terracotta paper backdrop, clean studio lighting, no text',
}

class Background:
    def __init__(self, provider: str):
        self.provider = provider
        self.name = provider + ' / FLUX background'
        self.available = bool(os.getenv('FAL_KEY' if provider == 'fal' else 'REPLICATE_API_TOKEN'))

    async def live(self, source: Path, destination: Path, style: str) -> str:
        prompt = f'Preserve the exact product shape, label and color. Replace only its surroundings with {STYLE_PROMPTS[style]}.'
        if self.provider == 'fal':
            response = await client().post('https://fal.run/' + os.getenv('FAL_BACKGROUND_MODEL', 'fal-ai/flux-pro/kontext'), headers={'Authorization': f'Key {os.getenv("FAL_KEY")}'}, json={'image_url': data_uri(source), 'prompt': prompt, 'output_format': 'png', 'num_images': 1})
            response.raise_for_status()
            url = response.json()['images'][0]['url']
        else:
            output = await replicate({'input_image': data_uri(source), 'prompt': prompt, 'output_format': 'png'}, model=os.getenv('REPLICATE_BACKGROUND_MODEL', 'black-forest-labs/flux-kontext-pro'))
            url = output[0] if isinstance(output, list) else output
        return await download(url, destination)

    async def fallback(self, source: Path, destination: Path, style: str) -> str:
        return await asyncio.to_thread(compose_variant, source, destination, style)

class Vision:
    def __init__(self, provider: str):
        self.provider = provider
        self.name = provider + ' / vision copy'
        self.available = bool(os.getenv('GEMINI_API_KEY' if provider == 'gemini' else 'OPENAI_API_KEY'))

    async def live(self, sources: list[Path], key: str) -> VisionOutput:
        prompt = 'Write an accurate product listing from these photos. Do not invent brand, capacity, certification or performance claims. Mark uncertain material/specs as needing seller confirmation. Return strict JSON matching the schema. Currency is INR. Main fields in English, hindi and marathi fields translated faithfully. Use 3–6 tags and 3 bullet_points. Keep seo_description under 160 characters.'
        schema = VisionOutput.model_json_schema()
        if self.provider == 'gemini':
            model = os.getenv('GEMINI_MODEL') or 'gemini-3.8-flash'
            parts = [{'text': prompt}] + [{'inlineData': {'mimeType': 'image/jpeg', 'data': base64.b64encode(path.read_bytes()).decode()}} for path in sources]
            response = await client().post(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent', headers={'x-goog-api-key': os.getenv('GEMINI_API_KEY', '')}, json={'contents': [{'parts': parts}], 'generationConfig': {'responseFormat': {'text': {'mimeType': 'application/json', 'schema': schema}}, 'temperature': .2}})
            response.raise_for_status()
            text = ''.join(part.get('text', '') for part in response.json()['candidates'][0]['content']['parts'])
        else:
            response = await client().post('https://api.openai.com/v1/chat/completions', headers={'Authorization': f'Bearer {os.getenv("OPENAI_API_KEY")}'}, json={'model': os.getenv('OPENAI_MODEL', 'gpt-4o'), 'messages': [{'role': 'user', 'content': [{'type': 'text', 'text': prompt}] + [{'type': 'image_url', 'image_url': {'url': data_uri(path)}} for path in sources]}], 'response_format': {'type': 'json_schema', 'json_schema': {'name': 'product_listing', 'strict': True, 'schema': schema}}})
            response.raise_for_status()
            text = response.json()['choices'][0]['message']['content']
        return VisionOutput.model_validate_json(text)

    async def fallback(self, sources: list[Path], key: str) -> VisionOutput:
        return demo_vision(key)

def extract_inr(text: str) -> float | None:
    # Only explicit INR values. Do not interpret ratings, USD prices, counts or model numbers as prices.
    match = re.search(r'(?:₹|\bINR\s*|\bRs\.?\s*)(\d[\d,]*(?:\.\d{1,2})?)', text, re.I)
    if not match:
        return None
    value = float(match.group(1).replace(',', ''))
    return value if 0 < value < 10_000_000 else None

class Price:
    def __init__(self, provider: str, repository: Repository):
        self.provider = provider
        self.repository = repository
        self.name = provider + ' / marketplace search'
        self.available = bool(os.getenv('TAVILY_API_KEY' if provider == 'tavily' else 'SERPAPI_API_KEY'))

    async def live(self, title: str, key: str) -> PriceRange:
        digest = hashlib.sha256(f'{self.provider}:{title.lower().strip()}'.encode()).hexdigest()
        cache_path = self.repository.cache / f'{digest}.json'
        if cache_path.exists():
            cached = json.loads(cache_path.read_text())
            if time.time()-cached['saved_at'] < int(os.getenv('PRICE_CACHE_TTL_SECONDS', '3600')):
                return PriceRange(**{**cached['value'], 'cached': True})
        query = f'{title} buy India price INR'
        if self.provider == 'tavily':
            response = await client().post('https://api.tavily.com/search', headers={'Authorization': f'Bearer {os.getenv("TAVILY_API_KEY")}'}, json={'query': query, 'search_depth': 'basic', 'max_results': 8, 'include_answer': False})
            response.raise_for_status()
            items = [{'title': item['title'], 'url': item['url'], 'text': item.get('content', '')} for item in response.json()['results']]
        else:
            response = await client().get('https://serpapi.com/search.json', params={'engine': 'google_shopping', 'q': query, 'gl': 'in', 'hl': 'en', 'api_key': os.getenv('SERPAPI_API_KEY')})
            response.raise_for_status()
            items = [{'title': item['title'], 'url': item.get('product_link', item.get('link', '')), 'text': item.get('price', '')} for item in response.json().get('shopping_results', [])]
        sources = []
        seen = set()
        for item in items:
            value = extract_inr(item['text'])
            if value and item['url'].startswith('https://') and item['url'] not in seen:
                sources.append(Comparable(title=item['title'], url=item['url'], price=value))
                seen.add(item['url'])
        if len(sources) < 2:
            raise ValueError('Not enough explicit INR offers to form a price range.')
        prices = [item.price for item in sources]
        result = PriceRange(low=min(prices), median=statistics.median(prices), high=max(prices), sources=sources)
        Repository.atomic(cache_path, {'saved_at': time.time(), 'value': result.model_dump()})
        return result

    async def fallback(self, title: str, key: str) -> PriceRange:
        return demo_prices(key)

def store_payload(listing: dict, channel: str, public_url: str) -> dict:
    copy = listing['copy']
    body = '<p>'+html.escape(copy['description'])+'</p><ul>'+''.join('<li>'+html.escape(point)+'</li>' for point in copy['bullet_points'])+'</ul>'
    image = public_url + listing['variants'][listing['selected_style']]
    if channel == 'shopify':
        return {'product': {'title': copy['title'], 'descriptionHtml': body, 'productType': listing['category'], 'tags': copy['tags'], 'status': 'DRAFT', 'seo': {'title': copy['seo_title'], 'description': copy['seo_description']}}, 'media': [{'originalSource': image, 'mediaContentType': 'IMAGE', 'alt': copy['title']}], 'variant': {'price': f'{listing["final_price"]:.2f}', 'inventoryItem': {'sku': listing['sku']}}}
    return {'name': copy['title'], 'type': 'simple', 'status': 'draft', 'sku': listing['sku'], 'regular_price': f'{listing["final_price"]:.2f}', 'description': body, 'short_description': html.escape(copy['seo_description']), 'images': [{'src': image, 'alt': copy['title']}], 'attributes': [{'name': 'Material', 'visible': True, 'options': [listing['material']]}, {'name': 'Color', 'visible': True, 'options': [listing['color']]}], 'meta_data': [{'key': '_snap2store_seo_title', 'value': copy['seo_title']}, {'key': '_snap2store_seo_description', 'value': copy['seo_description']}, {'key': '_snap2store_keywords', 'value': ', '.join(copy['tags'])}, {'key': '_snap2store_category', 'value': listing['category']}]}

def shopify_url() -> str:
    domain = os.getenv('SHOPIFY_DOMAIN', '').lower().removeprefix('https://').rstrip('/')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*\.myshopify\.com', domain):
        raise ValueError('Use your store-name.myshopify.com domain.')
    version = os.getenv('SHOPIFY_API_VERSION', '2026-07')
    return f'https://{domain}/admin/api/{version}/graphql.json'

def woo_url() -> str:
    url = os.getenv('WOOCOMMERCE_URL', '').rstrip('/')
    parsed = urlparse(url)
    if parsed.scheme != 'https' and not (parsed.scheme == 'http' and parsed.hostname in {'localhost', '127.0.0.1', 'woocommerce'}):
        raise ValueError('WooCommerce requires HTTPS, except for a local test store.')
    if parsed.username or parsed.password or not parsed.hostname:
        raise ValueError('Use a store URL without embedded credentials.')
    return url + '/wp-json/wc/v3'

class Store:
    def __init__(self, config: Settings):
        self.config = config

    def available(self, channel: str) -> bool:
        keys = ('SHOPIFY_DOMAIN', 'SHOPIFY_ACCESS_TOKEN') if channel == 'shopify' else ('WOOCOMMERCE_URL', 'WOOCOMMERCE_KEY', 'WOOCOMMERCE_SECRET')
        return all(os.getenv(key) for key in keys)

    async def graphql(self, query: str, variables: dict) -> dict:
        response = await client().post(shopify_url(), headers={'X-Shopify-Access-Token': os.getenv('SHOPIFY_ACCESS_TOKEN', '')}, json={'query': query, 'variables': variables})
        response.raise_for_status()
        data = response.json()
        if data.get('errors'):
            raise ValueError('Shopify rejected the GraphQL operation.')
        return data['data']

    async def test(self, channel: str) -> dict:
        if self.config.demo or not self.available(channel):
            return {'ok': True, 'demo': True, 'message': 'Demo store ready. No live connection was tested; demo mode is on or credentials are missing.'}
        try:
            if channel == 'shopify':
                data = await self.graphql('query { shop { name currencyCode } }', {})
                if data['shop']['currencyCode'] != 'INR':
                    return {'ok': False, 'demo': False, 'message': 'Store currency must be INR for these drafts.'}
            else:
                response = await client().get(woo_url()+'/settings/general/woocommerce_currency', auth=(os.getenv('WOOCOMMERCE_KEY', ''), os.getenv('WOOCOMMERCE_SECRET', '')))
                response.raise_for_status()
                if response.json().get('value') != 'INR':
                    return {'ok': False, 'demo': False, 'message': 'Set the WooCommerce store currency to INR first.'}
            return {'ok': True, 'demo': False, 'message': 'Live store connection verified. Draft writes still require approval.'}
        except (httpx.HTTPError, ValueError, KeyError):
            return {'ok': False, 'demo': False, 'message': 'Connection failed. Check URL, token permissions, API version and store currency.'}

    async def publish(self, listing: dict, channel: str) -> dict:
        if self.config.demo or not self.available(channel):
            return self.demo(listing, channel, 'Demo mode is on.' if self.config.demo else 'Store credentials are missing.')
        # Validate before any create operation; never retry non-idempotent store creation.
        test = await self.test(channel)
        if not test['ok']:
            return self.demo(listing, channel, test['message'])
        payload = store_payload(listing, channel, self.config.public_url)
        # Shopify and WooCommerce cannot fetch localhost images.
        parsed = urlparse(self.config.public_url)
        if parsed.scheme != 'https' or parsed.hostname in {'localhost', '127.0.0.1'}:
            return self.demo(listing, channel, 'A publicly reachable HTTPS PUBLIC_BASE_URL is required for store image imports.')
        if channel == 'shopify':
            data = await self.graphql('mutation CreateDraft($product: ProductCreateInput!, $media: [CreateMediaInput!]) { productCreate(product: $product, media: $media) { product { id status variants(first: 1) { nodes { id } } } userErrors { field message } } }', {'product': payload['product'], 'media': payload['media']})
            created = data['productCreate']
            if created['userErrors'] or not created['product']:
                raise ValueError('Shopify rejected the product draft.')
            product = created['product']
            identifier = product['id'].split('/')[-1]
            link = 'https://'+os.getenv('SHOPIFY_DOMAIN', '').removeprefix('https://').rstrip('/')+'/admin/products/'+identifier
            result = {'id': product['id'], 'url': link, 'channel': channel, 'demo': False, 'status': 'draft', 'message': 'A draft was created in Shopify. It is not visible to shoppers.', 'price_synced': True}
            try:
                updated = await self.graphql('mutation PriceDraft($productId: ID!, $variants: [ProductVariantsBulkInput!]!) { productVariantsBulkUpdate(productId: $productId, variants: $variants) { productVariants { id price } userErrors { field message } } }', {'productId': product['id'], 'variants': [{'id': product['variants']['nodes'][0]['id'], **payload['variant']}]})
                if updated['productVariantsBulkUpdate']['userErrors']:
                    raise ValueError('Variant update rejected.')
            except (httpx.HTTPError, KeyError, ValueError):
                result.update(price_synced=False, message='Draft created, but price/SKU update failed. Open this draft and correct it; do not create another.')
            return result
        auth = (os.getenv('WOOCOMMERCE_KEY', ''), os.getenv('WOOCOMMERCE_SECRET', ''))
        # Woo product taxonomy accepts IDs, not names. Resolve/create only after approval.
        tag_ids = []
        for tag in dict.fromkeys(listing['copy']['tags']):
            response = await client().get(woo_url()+'/products/tags', auth=auth, params={'search': tag, 'per_page': 100})
            response.raise_for_status()
            existing = next((term for term in response.json() if html.unescape(term['name']).casefold() == tag.casefold()), None)
            if existing is None:
                response = await client().post(woo_url()+'/products/tags', auth=auth, json={'name': tag})
                response.raise_for_status()
                existing = response.json()
            tag_ids.append({'id': existing['id']})
        payload['tags'] = tag_ids
        response = await client().post(woo_url()+'/products', auth=auth, json=payload)
        response.raise_for_status()
        product = response.json()
        if product.get('status') != 'draft':
            raise ValueError('Store response did not confirm draft status; check your admin.')
        return {'id': str(product['id']), 'url': os.getenv('WOOCOMMERCE_URL', '').rstrip('/')+'/wp-admin/post.php?post='+str(product['id'])+'&action=edit', 'channel': channel, 'demo': False, 'status': 'draft', 'price_synced': True, 'message': 'A draft was created in WooCommerce. It is not visible to shoppers.'}

    def demo(self, listing: dict, channel: str, reason: str) -> dict:
        return {'id': 'DEMO-'+listing['sku'], 'url': '/create?job='+listing['id'], 'channel': channel, 'demo': True, 'status': 'draft', 'price_synced': True, 'message': reason+' Demo draft saved locally; no live store operation was attempted.'}
