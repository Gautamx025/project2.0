"""Cloud persistence: Redis records/locks and immutable, private Blob media."""
import hashlib
import hmac
import json
import os
import re
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from functools import lru_cache
from http.cookies import SimpleCookie
from pathlib import Path

import httpx
from .repository import Repository

workspace = ContextVar('cloud_workspace', default='')


@lru_cache(maxsize=1)
def redis_client():
    return httpx.Client(timeout=15)


def redis(*command):
    url = os.getenv('KV_REST_API_URL') or os.getenv('UPSTASH_REDIS_REST_URL')
    token = os.getenv('KV_REST_API_TOKEN') or os.getenv('UPSTASH_REDIS_REST_TOKEN')
    if not url or not token:
        raise RuntimeError('Cloud storage is not configured. Connect the managed Redis store.')
    response = redis_client().post(url, headers={'Authorization': 'Bearer '+token}, json=list(command))
    response.raise_for_status()
    result = response.json()
    if result.get('error'):
        raise RuntimeError('Cloud storage could not complete the operation.')
    return result['result']


class VisitorWorkspace:
    """A signed, anonymous browser workspace, propagated to background tasks."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        from .config import cloud_mode
        if not cloud_mode():
            return await self.app(scope, receive, send)
        secret = os.getenv('SESSION_SECRET', '')
        if not secret:
            raise RuntimeError('The cloud workspace signing key is not configured.')
        cookies = SimpleCookie()
        try:
            cookies.load(dict(scope.get('headers', [])).get(b'cookie', b'').decode())
        except Exception:
            pass
        value = cookies['s2s_workspace'].value if 's2s_workspace' in cookies else ''
        identifier, _, signature = value.partition('.')
        def sign(identifier):
            return hmac.new(secret.encode(), identifier.encode(), hashlib.sha256).hexdigest()
        valid = bool(re.fullmatch(r'[a-f0-9]{32}', identifier)) and hmac.compare_digest(signature, sign(identifier))
        if not valid:
            identifier = uuid.uuid4().hex
        marker = workspace.set(identifier)
        async def with_cookie(message):
            if message['type'] == 'http.response.start':
                headers = list(message.get('headers', []))
                headers.append((b'cache-control', b'private, no-store'))
                if not valid:
                    cookie = f's2s_workspace={identifier}.{sign(identifier)}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=2592000'
                    headers.append((b'set-cookie', cookie.encode()))
                message = {**message, 'headers': headers}
            await send(message)
        try:
            await self.app(scope, receive, with_cookie)
        finally:
            workspace.reset(marker)


class CloudRepository(Repository):
    @property
    def prefix(self):
        scope = workspace.get()
        if not re.fullmatch(r'[a-f0-9]{32}', scope):
            raise RuntimeError('A browser workspace is required.')
        return 'snap2store:'+os.getenv('VERCEL_ENV', 'development')+':'+scope+':'

    def key(self, job_id):
        self.path(job_id)  # Keep the same UUID validation as local persistence.
        return self.prefix+'job:'+job_id

    def get(self, job_id):
        result = redis('GET', self.key(job_id))
        if result is None:
            raise FileNotFoundError(job_id)
        return json.loads(result)

    def save(self, job):
        job['revision'] = job.get('revision', 0)+1
        job['updated_at'] = time.time()
        redis('SET', self.key(job['id']), json.dumps(job, ensure_ascii=False))
        redis('ZADD', self.prefix+'jobs', job['created_at'], job['id'])
        return job

    def all(self):
        ids = redis('ZREVRANGE', self.prefix+'jobs', 0, 199)
        if not ids:
            return []
        values = redis('MGET', *[self.key(identifier) for identifier in ids])
        return [json.loads(value) for value in values if value is not None]

    @contextmanager
    def lock(self, job_id):
        key = self.key(job_id)+':lock'
        owner = uuid.uuid4().hex
        if redis('SET', key, owner, 'NX', 'EX', 300) != 'OK':
            raise RuntimeError('This listing is being updated. Try again in a moment.')
        try:
            yield
        finally:
            redis('EVAL', "if redis.call('get',KEYS[1]) == ARGV[1] then return redis.call('del',KEYS[1]) else return 0 end", 1, key, owner)

    def media_key(self, name):
        if not re.fullmatch(r'[a-f0-9-]{36}-[a-z0-9-]+\.(jpg|png)', name):
            raise FileNotFoundError(name)
        return self.prefix.replace(':', '/')+'media/'+name

    def store_media(self, path: Path):
        from vercel.blob import sync as blob
        blob.put_blob(self.media_key(path.name), path.read_bytes(), access='private',
                      content_type='image/png' if path.suffix == '.png' else 'image/jpeg')

    def load_media(self, name: str):
        from vercel.blob import sync as blob
        key = self.media_key(name)
        self.get(name[:36])  # Authorize ownership before consulting the warm local cache.
        path = self.media/name
        if not path.is_file():
            try:
                content = blob.get_blob(key, access='private').body
            except blob.BlobNotFoundError:
                raise FileNotFoundError(name)
            temporary = path.with_suffix('.'+uuid.uuid4().hex+'.tmp')
            temporary.write_bytes(content)
            os.replace(temporary, path)
        return path
