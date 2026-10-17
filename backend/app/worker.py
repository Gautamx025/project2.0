import asyncio
import os
from redis import Redis
from rq import Worker, SimpleWorker
from .config import settings
from .pipeline import run_job

def run_job_sync(job_id: str, start_stage: int = 0):
    asyncio.run(run_job(job_id, start_stage))

if __name__ == '__main__':
    config = settings()
    if not config.redis_url:
        raise SystemExit('Set REDIS_URL before starting a worker. Without Redis the API uses BackgroundTasks.')
    worker_type = SimpleWorker if os.name == 'nt' else Worker
    worker_type(['snap2store'], connection=Redis.from_url(config.redis_url)).work()
