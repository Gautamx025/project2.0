import pytest
from fastapi import BackgroundTasks
from backend.app import config, main, pipeline, queueing
from backend.app.adapters import Segmentation

def test_redis_failure_uses_background_queue_with_notice(monkeypatch, isolated_environment):
    monkeypatch.setenv('REDIS_URL', 'redis://unavailable:6379/0')
    class Unavailable:
        def __init__(self, url):
            raise ConnectionError('offline')
    monkeypatch.setattr(queueing, 'RedisQueue', Unavailable)
    job = pipeline.new_job([], 'bottle', 'studio', 'en')
    isolated_environment.save(job)
    background = BackgroundTasks()
    queueing.enqueue(job, background, isolated_environment)
    saved = isolated_environment.get(job['id'])
    assert saved['queue'] == 'background'
    assert 'Redis is unavailable' in saved['queue_warning']
    assert len(background.tasks) == 1

def test_fast_redis_worker_result_is_not_overwritten(monkeypatch, isolated_environment):
    monkeypatch.setenv('REDIS_URL', 'redis://example:6379/0')
    class ImmediateWorker:
        def __init__(self, url): pass
        def submit(self, job_id, background, start_stage=0):
            finished = isolated_environment.get(job_id)
            finished['status'] = 'ready'
            isolated_environment.save(finished)
    monkeypatch.setattr(queueing, 'RedisQueue', ImmediateWorker)
    job = pipeline.new_job([], 'bottle', 'studio', 'en')
    isolated_environment.save(job)
    queueing.enqueue(job, BackgroundTasks(), isolated_environment)
    assert isolated_environment.get(job['id'])['status'] == 'ready'

def test_failed_stage_can_recover_through_retry(api, monkeypatch):
    original = Segmentation.fallback
    async def broken(self, *args):
        raise OSError('simulated local image failure')
    monkeypatch.setattr(Segmentation, 'fallback', broken)
    created = api.post('/api/jobs/sample', json={'sample': 'bag'}).json()
    endpoint = '/api/jobs/'+created['id']
    failed = api.get(endpoint).json()
    assert failed['status'] == 'failed' and failed['stages'][1]['status'] == 'failed'
    assert api.post(endpoint+'/retry', json={'stage': 'metadata'}).status_code == 409
    monkeypatch.setattr(Segmentation, 'fallback', original)
    assert api.post(endpoint+'/retry', json={'stage': 'isolation'}).status_code == 202
    recovered = api.get(endpoint).json()
    assert recovered['status'] == 'ready'
    assert recovered['result']['copy']['title'] == 'Everyday brown backpack'
