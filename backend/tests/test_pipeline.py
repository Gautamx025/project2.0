import asyncio
import json
from pathlib import Path
import pytest
from backend.app import config, main, pipeline
from backend.app.adapters import Segmentation, Store
from backend.app.imaging import normalize_image

def test_demo_pipeline_real_images_and_measured_stages(ready, isolated_environment):
    assert ready['status'] == 'ready'
    assert [stage['key'] for stage in ready['stages']] == ['ingestion', 'isolation', 'background', 'metadata', 'pricing', 'draft']
    assert all(stage['status'] == 'completed' for stage in ready['stages'])
    assert all(stage['elapsed_ms'] >= 0 for stage in ready['stages'])
    assert ready['elapsed_ms'] >= sum(stage['elapsed_ms'] for stage in ready['stages'])
    assert ready['stages'][1]['demo'] and 'Demo mode' in ready['stages'][1]['reason']
    assert ready['store_result'] is None and not ready['result']['approved']
    assert set(ready['result']['variants']) == {'studio', 'shadow', 'lifestyle', 'color'}
    from PIL import Image
    for url in ready['result']['variants'].values():
        image = Image.open(isolated_environment.media / Path(url).name)
        assert image.size == (1000, 1000)
    assert ready['result']['translations']['hi']['title'] == 'स्टील की पानी की बोतल'
    assert ready['result']['translations']['mr']['title'] == 'स्टीलची पाण्याची बाटली'
    assert all(item['demo'] and not item['url'] for item in ready['result']['price']['sources'])

def test_invalid_inputs_rejected_without_creating_jobs(api):
    assert api.post('/api/jobs', files={'files': ('bad.txt', b'not a photo', 'text/plain')}).status_code == 422
    assert api.post('/api/jobs', files={'files': ('bad.jpg', b'not a photo', 'image/jpeg')}).status_code == 422
    assert api.post('/api/jobs', files=[('files', ('a.jpg', b'x', 'image/jpeg'))]*4).status_code == 422
    assert api.get('/api/jobs').json() == []
    with pytest.raises(ValueError, match='10 MB'):
        normalize_image(b'x'*(10*1024*1024+1))

def test_edit_roundtrip_payload_and_no_unapproved_write(api, ready, monkeypatch):
    calls = []
    async def store_publish(self, listing, channel):
        calls.append((listing['copy']['title'], listing['final_price']))
        return self.demo(listing, channel, 'Test demo store.')
    monkeypatch.setattr(Store, 'publish', store_publish)
    original = ready['result']
    copy = {**original['copy'], 'title': 'My reviewed bottle', 'tags': ['bottle', 'local'], 'description': 'Merchant-confirmed revised product description.'}
    edited = api.patch('/api/jobs/'+ready['id'], json={'copy': copy, 'final_price': 875.5, 'language': 'en', 'selected_style': 'shadow'}).json()
    payload = api.get('/api/jobs/'+ready['id']+'/payload').json()
    assert payload['product']['title'] == 'My reviewed bottle'
    assert payload['variant']['price'] == '875.50'
    assert payload['product']['status'] == 'DRAFT'
    assert payload['media'][0]['originalSource'] == 'https://catalog.example.org'+original['variants']['shadow']
    assert 'Merchant-confirmed revised' in payload['product']['descriptionHtml']
    endpoint = '/api/jobs/'+ready['id']+'/publish'
    assert api.post(endpoint, json={'channel': 'shopify', 'approved': False, 'revision': edited['revision']}).status_code == 422
    assert api.post(endpoint, json={'channel': 'shopify', 'approved': True, 'revision': ready['revision']}).status_code == 409
    assert calls == []
    request = {'channel': 'shopify', 'approved': True, 'revision': edited['revision']}
    first = api.post(endpoint, json=request).json()
    assert first['status'] == 'published' and first['store_result']['demo']
    assert first['store_result']['status'] == 'draft'
    assert api.post(endpoint, json=request).status_code == 200
    assert calls == [('My reviewed bottle', 875.5)]

def test_terminal_sse_contains_persisted_result(api, ready):
    response = api.get('/api/jobs/'+ready['id']+'/events')
    assert response.headers['content-type'].startswith('text/event-stream')
    lines = response.text.splitlines()
    event = json.loads(next(line[6:] for line in lines if line.startswith('data: ')))
    assert event['id'] == ready['id'] and event['status'] == 'ready'
    assert event['result']['sku'] == ready['result']['sku']

async def test_cancellation_discards_late_stage_output(isolated_environment, monkeypatch):
    repo = isolated_environment
    image = config.ROOT/'frontend/public/samples/bottle.jpg'
    job = pipeline.new_job(['/media/raw.jpg'], 'bottle', 'studio', 'en')
    (repo.media/'raw.jpg').write_bytes(image.read_bytes())
    repo.save(job)
    entered, release = asyncio.Event(), asyncio.Event()
    original = Segmentation.fallback
    async def slow(self, *args):
        entered.set()
        await release.wait()
        return await original(self, *args)
    monkeypatch.setattr(Segmentation, 'fallback', slow)
    task = asyncio.create_task(pipeline.run_job(job['id']))
    await asyncio.wait_for(entered.wait(), 5)
    cancelled = repo.get(job['id'])
    cancelled['status'] = 'cancelled'
    repo.save(cancelled)
    release.set()
    await task
    assert repo.get(job['id'])['status'] == 'cancelled'
    assert repo.get(job['id'])['result'] is None

def test_stage_retry_rebuilds_result_and_rejects_published_retry(api, ready):
    endpoint = '/api/jobs/'+ready['id']
    response = api.post(endpoint+'/retry', json={'stage': 'metadata'})
    assert response.status_code == 202
    refreshed = api.get(endpoint).json()
    assert refreshed['status'] == 'ready'
    assert refreshed['stages'][0]['elapsed_ms'] == ready['stages'][0]['elapsed_ms']
    assert refreshed['revision'] > ready['revision']
    api.post(endpoint+'/publish', json={'channel': 'woocommerce', 'approved': True, 'revision': refreshed['revision']})
    assert api.post(endpoint+'/retry', json={'stage': 'pricing'}).status_code == 409

def test_settings_keep_secrets_server_side_and_blank_preserves(api):
    result = api.put('/api/settings', json={'shopify_access_token': 'test-secret-never-return', 'shopify_domain': 'test.myshopify.com', 'demo_mode': True})
    assert result.status_code == 200
    assert 'test-secret-never-return' not in result.text
    assert result.json()['configured']['shopify_access_token'] is True
    api.put('/api/settings', json={'shopify_access_token': ''})
    assert api.get('/api/settings').json()['configured']['shopify_access_token'] is True
    assert 'test-secret-never-return' in config.ENV_FILE.read_text()
    tested = api.post('/api/settings/test', json={'channel': 'shopify'}).json()
    assert tested['demo'] and 'No live connection' in tested['message']

def test_new_jobs_do_not_reuse_previous_listing(api, ready):
    created = api.post('/api/jobs/sample', json={'sample': 'bag'}).json()
    bag = api.get('/api/jobs/'+created['id']).json()
    assert bag['id'] != ready['id']
    assert bag['result']['copy']['title'] == 'Everyday brown backpack'
    assert bag['result']['final_price'] == 1899
    assert bag['store_result'] is None

def test_saving_one_language_preserves_edits_to_other_languages(api, ready):
    listing=ready['result']
    translations=listing['translations']
    translations['en']['title']='My edited English bottle'
    translations['hi']['title']='मेरी पानी की बोतल'
    response=api.patch('/api/jobs/'+ready['id'],json={'copy':translations['mr'],'translations':translations,'language':'mr','selected_style':'studio','final_price':749})
    assert response.status_code==200
    saved=api.get('/api/jobs/'+ready['id']).json()['result']
    assert saved['translations']['en']['title']=='My edited English bottle'
    assert saved['translations']['hi']['title']=='मेरी पानी की बोतल'
    assert saved['copy']['title']=='स्टीलची पाण्याची बाटली'
