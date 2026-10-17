"""Exercise real cloud repository/pipeline; fake only HTTP and Blob boundaries."""
import json
import time
from types import SimpleNamespace
import httpx
import pytest
from fastapi.testclient import TestClient
from backend.app import cloud, config, main
from backend.app.cloud import CloudRepository, workspace


@pytest.fixture
def cloud_storage(tmp_path, monkeypatch):
    monkeypatch.setenv('CLOUD_MODE', 'true')
    monkeypatch.setenv('SESSION_SECRET', 'test-workspace-signing-key')
    monkeypatch.setenv('UPSTASH_REDIS_REST_URL', 'https://redis.example.test')
    monkeypatch.setenv('UPSTASH_REDIS_REST_TOKEN', 'test-redis-token')
    values, sorted_sets, blobs = {}, {}, {}
    def command(request):
        assert request.headers['Authorization'] == 'Bearer test-redis-token'
        verb, *args = json.loads(request.content)
        if verb == 'GET': result = values.get(args[0])
        elif verb == 'SET':
            if 'NX' in args[2:] and args[0] in values: result = None
            else: values[args[0]] = args[1]; result = 'OK'
        elif verb == 'ZADD':
            sorted_sets.setdefault(args[0], {})[args[2]] = float(args[1]); result = 1
        elif verb == 'ZREVRANGE':
            result = sorted(sorted_sets.get(args[0], {}), key=sorted_sets.get(args[0], {}).get, reverse=True)[args[1]:args[2]+1]
        elif verb == 'MGET': result = [values.get(key) for key in args]
        elif verb == 'EVAL':
            key, owner = args[2], args[3]
            result = int(values.get(key) == owner)
            if result: values.pop(key)
        else: raise AssertionError('Unexpected Redis command: '+verb)
        return httpx.Response(200, json={'result': result})
    http = httpx.Client(transport=httpx.MockTransport(command))
    monkeypatch.setattr(cloud, 'redis_client', lambda: http)
    from vercel.blob import sync as blob
    def put(name, body, **options):
        assert options['access'] == 'private'
        assert name not in blobs, 'Cloud media must use immutable names, including on retry'
        blobs[name] = body
    def get(name, **options):
        assert options['access'] == 'private'
        if name not in blobs: raise FileNotFoundError(name)
        return SimpleNamespace(body=blobs[name])
    monkeypatch.setattr(blob, 'put_blob', put)
    monkeypatch.setattr(blob, 'get_blob', get)
    monkeypatch.setattr(main, 'repository', CloudRepository(tmp_path/'instance-one'))
    yield SimpleNamespace(blobs=blobs, values=values, root=tmp_path)
    http.close()


def test_cloud_flow_survives_new_instance_and_isolates_visitors(cloud_storage, monkeypatch):
    with TestClient(main.app, base_url='https://testserver') as visitor:
        response = visitor.post('/api/jobs/sample', json={'sample': 'bottle'})
        assert response.status_code == 202, response.text
        job_id = response.json()['id']
        ready = visitor.get('/api/jobs/'+job_id).json()
        assert ready['status'] == 'ready'
        assert ready['queue'] == 'cloud-function'
        assert all(stage['status'] == 'completed' for stage in ready['stages'])
        image = ready['result']['variants']['shadow']
        edited = visitor.patch('/api/jobs/'+job_id, json={
            'copy': {**ready['result']['copy'], 'title':'Cloud-tested bottle'},
            'final_price':875.5, 'language':'en', 'selected_style':'shadow',
        })
        assert edited.status_code == 200
        ready = edited.json()
        cookie = visitor.cookies.get('s2s_workspace')
        assert cookie and 'HttpOnly' in response.headers['set-cookie']
        assert 'Secure' in response.headers['set-cookie']
        monkeypatch.setattr(main, 'repository', CloudRepository(cloud_storage.root/'cold-instance'))
        restored = visitor.get('/api/jobs/'+job_id).json()
        assert restored['result']['copy']['title'] == 'Cloud-tested bottle'
        assert restored['result']['final_price'] == 875.5
        photo = visitor.get(image)
        assert photo.status_code == 200 and photo.content.startswith(b'\x89PNG')
        assert len(visitor.get('/api/jobs').json()) == 1
        approved = visitor.post('/api/jobs/'+job_id+'/publish', json={'approved': True, 'channel': 'shopify', 'revision': ready['revision']})
        assert approved.status_code == 200
        assert approved.json()['store_result']['demo'] is True
        assert visitor.get('/api/jobs/'+job_id).json()['status'] == 'published'
        with TestClient(main.app, base_url='https://testserver') as other:
            assert other.get('/api/jobs').json() == []
            assert other.get('/api/jobs/'+job_id).status_code == 404
            assert other.get(image).status_code == 404
            other.cookies.set('s2s_workspace', cookie.split('.')[0]+'.forged')
            assert other.get('/api/jobs/'+job_id).status_code == 404


def test_cloud_retry_uses_new_media_and_keeps_settings_managed(cloud_storage):
    with TestClient(main.app, base_url='https://testserver') as visitor:
        job_id = visitor.post('/api/jobs/sample', json={'sample': 'watch'}).json()['id']
        before = visitor.get('/api/jobs/'+job_id).json()
        assert visitor.post('/api/jobs/'+job_id+'/retry', json={'stage':'isolation'}).status_code == 202
        after = visitor.get('/api/jobs/'+job_id).json()
        assert after['status'] == 'ready'
        assert before['result']['variants']['studio'] != after['result']['variants']['studio']
        assert visitor.get(after['result']['variants']['studio']).status_code == 200
        assert visitor.get('/api/settings').json()['settings_readonly'] is True
        assert visitor.put('/api/settings', json={'demo_mode':False,'openai_api_key':'must-not-be-saved'}).status_code == 409
        assert config.settings().demo is True
        assert visitor.get('/api/settings').json()['configured']['openai_api_key'] is False


def test_cloud_timeout_becomes_retryable_without_interrupting_fresh_runs(cloud_storage):
    with TestClient(main.app, base_url='https://testserver') as visitor:
        job_id = visitor.post('/api/jobs/sample', json={'sample':'bottle'}).json()['id']
        key = next(key for key in cloud_storage.values if key.endswith(':job:'+job_id))
        job = json.loads(cloud_storage.values[key])
        job.update(status='processing', result=None, updated_at=time.time())
        job['stages'][4]['status'] = 'running'
        job['stages'][5]['status'] = 'pending'
        cloud_storage.values[key] = json.dumps(job)
        assert visitor.get('/api/jobs/'+job_id).json()['status'] == 'processing'
        job['updated_at'] = time.time()-400
        cloud_storage.values[key] = json.dumps(job)
        interrupted = visitor.get('/api/jobs/'+job_id).json()
        assert interrupted['status'] == 'failed'
        assert interrupted['stages'][4]['status'] == 'failed'
        assert 'hosted processing window' in interrupted['error']
        assert visitor.post('/api/jobs/'+job_id+'/retry', json={'stage':'pricing'}).status_code == 202
        assert visitor.get('/api/jobs/'+job_id).json()['status'] == 'ready'


def test_cloud_lock_is_shared_and_does_not_release_a_new_owner(cloud_storage):
    marker = workspace.set('a'*32)
    try:
        first = CloudRepository(cloud_storage.root/'lock-one')
        second = CloudRepository(cloud_storage.root/'lock-two')
        job_id = '12345678-1234-1234-1234-123456789abc'
        with first.lock(job_id):
            with pytest.raises(RuntimeError, match='being updated'):
                with second.lock(job_id):
                    pytest.fail('A second instance acquired the same lock')
        with second.lock(job_id):
            cloud_storage.values[second.key(job_id)+':lock'] = 'replacement-owner'
        assert cloud_storage.values[second.key(job_id)+':lock'] == 'replacement-owner'
    finally:
        workspace.reset(marker)
