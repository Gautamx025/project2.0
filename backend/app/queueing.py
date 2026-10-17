from typing import Protocol
from fastapi import BackgroundTasks
from .config import cloud_mode, settings
from .repository import Repository

class JobQueue(Protocol):
    def submit(self, job_id: str, background: BackgroundTasks, start_stage: int = 0) -> str: ...

class BackgroundQueue:
    def submit(self, job_id: str, background: BackgroundTasks, start_stage: int = 0) -> str:
        from .pipeline import run_job
        background.add_task(run_job, job_id, start_stage)
        return 'background'

class RedisQueue:
    def __init__(self, url: str):
        from redis import Redis
        from rq import Queue
        self.redis = Redis.from_url(url, socket_connect_timeout=1, socket_timeout=2)
        self.queue = Queue('snap2store', connection=self.redis)
    def submit(self, job_id: str, background: BackgroundTasks, start_stage: int = 0) -> str:
        self.redis.ping()
        self.queue.enqueue('backend.app.worker.run_job_sync', job_id, start_stage, job_timeout=600)
        return 'redis'

def enqueue(job: dict, background: BackgroundTasks, repository: Repository, start_stage: int = 0):
    config = settings()
    if cloud_mode():
        job['queue'] = 'cloud-function'
        repository.save(job)
        BackgroundQueue().submit(job['id'], background, start_stage)
        return
    if config.redis_url:
        try:
            queue = RedisQueue(config.redis_url)
            job['queue'] = 'redis'
            repository.save(job)
            queue.submit(job['id'], background, start_stage)
            return
        except Exception:
            job['queue_warning'] = 'Redis is unavailable. This job is running with the local background queue.'
    job['queue'] = 'background'
    repository.save(job)
    BackgroundQueue().submit(job['id'], background, start_stage)
