"""Replaceable durable repository; no request state lives in an API instance."""
import json
import os
import re
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

class Repository:
    def __init__(self, root: Path):
        self.root = root
        self.jobs = root / 'jobs'
        self.media = root / 'media'
        self.cache = root / 'cache'
        for directory in (self.jobs, self.media, self.cache):
            directory.mkdir(parents=True, exist_ok=True)

    def path(self, job_id: str) -> Path:
        if not re.fullmatch(r'[a-f0-9-]{36}', job_id):
            raise FileNotFoundError(job_id)
        return self.jobs / f'{job_id}.json'

    def get(self, job_id: str) -> dict:
        try:
            return json.loads(self.path(job_id).read_text(encoding='utf-8'))
        except (FileNotFoundError, json.JSONDecodeError):
            raise FileNotFoundError(job_id)

    def save(self, job: dict) -> dict:
        job['revision'] = job.get('revision', 0) + 1
        job['updated_at'] = time.time()
        self.atomic(self.path(job['id']), job)
        return job

    @staticmethod
    def atomic(path: Path, value: dict):
        temporary = path.with_suffix(f'.{uuid.uuid4().hex}.tmp')
        temporary.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
        os.replace(temporary, path)

    def all(self) -> list[dict]:
        records = []
        for path in self.jobs.glob('*.json'):
            try:
                records.append(json.loads(path.read_text(encoding='utf-8')))
            except (OSError, json.JSONDecodeError):
                continue
        return sorted(records, key=lambda job: job['created_at'], reverse=True)[:200]

    def store_media(self, path: Path) -> None:
        pass  # Local files are already durable in the configured data directory.

    def load_media(self, name: str) -> Path:
        if Path(name).name != name or name.startswith('.'):
            raise FileNotFoundError(name)
        path = self.media / name
        if not path.is_file():
            raise FileNotFoundError(name)
        return path

    @contextmanager
    def lock(self, job_id: str):
        path = self.path(job_id).with_suffix('.lock')
        try:
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise RuntimeError('This listing is being updated. Try again in a moment.')
        try:
            os.close(descriptor)
            yield
        finally:
            path.unlink(missing_ok=True)


def create_repository(root: Path):
    from .config import cloud_mode
    if cloud_mode():
        from .cloud import CloudRepository
        return CloudRepository(root)
    return Repository(root)
