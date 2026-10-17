import asyncio
import json
import time
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from .adapters import Store, close_clients, store_payload
from .config import ROOT, public_settings, save_settings, settings
from .imaging import MAX_BYTES, normalize_image
from .models import ConnectionRequest, EditRequest, Language, PublishRequest, RetryRequest, SampleRequest, SettingsRequest, Style
from .pipeline import STAGES, new_job
from .queueing import enqueue
from .repository import Repository

@asynccontextmanager
async def lifespan(app):
    yield
    await close_clients()

app = FastAPI(title='Snap-2-Store', version='1.0.0', lifespan=lifespan)
repository = Repository(settings().data_dir)
app.mount('/media', StaticFiles(directory=repository.media), name='media')

def get_job(job_id: str) -> dict:
    try:
        return repository.get(job_id)
    except FileNotFoundError:
        raise HTTPException(404, 'Listing not found. It may belong to a different local workspace.')

@app.exception_handler(RuntimeError)
async def conflict(request: Request, exc: RuntimeError):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=409, content={'detail': str(exc)})

@app.get('/api/health')
def health():
    config = settings()
    return {'status': 'ok', 'demo_mode': config.demo, 'queue': 'redis' if config.redis_url else 'background', 'storage': 'shared-filesystem'}

@app.get('/api/settings')
def read_settings():
    return public_settings()

@app.put('/api/settings')
def update_settings(body: SettingsRequest):
    return save_settings(body.model_dump(exclude_none=True))

@app.post('/api/settings/test')
async def test_connection(body: ConnectionRequest):
    return await Store(settings()).test(body.channel)

async def create_job(contents: list[bytes], key: str, style: str, language: str, background: BackgroundTasks) -> dict:
    if not 1 <= len(contents) <= 3:
        raise HTTPException(422, 'Choose between 1 and 3 photos for one product.')
    images = []
    try:
        for content in contents:
            images.append(await asyncio.to_thread(normalize_image, content))
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    job = new_job([], key, style, language)
    for index, image in enumerate(images):
        name = f'{job["id"]}-raw-{index}.jpg'
        await asyncio.to_thread(image.save, repository.media/name, quality=90)
        job['source_images'].append('/media/'+name)
    repository.save(job)
    enqueue(job, background, repository)
    return job

@app.post('/api/jobs', status_code=202)
async def upload_job(background: BackgroundTasks, files: list[UploadFile] = File(...), style: Style = Form('studio'), language: Language = Form('en')):
    if not 1 <= len(files) <= 3:
        raise HTTPException(422, 'Choose between 1 and 3 photos for one product.')
    contents = []
    for file in files:
        if file.content_type not in {'image/jpeg', 'image/png', 'image/webp'}:
            raise HTTPException(422, 'Use JPG, PNG or WebP photos.')
        data = await file.read(MAX_BYTES+1)
        await file.close()
        contents.append(data)
    return await create_job(contents, 'custom', style, language, background)

@app.post('/api/jobs/sample', status_code=202)
async def sample_job(body: SampleRequest, background: BackgroundTasks):
    path = ROOT/'frontend'/'public'/'samples'/f'{body.sample}.jpg'
    if not path.exists():
        raise HTTPException(503, 'Sample asset is missing. Upload a photo instead.')
    return await create_job([path.read_bytes()], body.sample, body.style, body.language, background)

@app.get('/api/jobs')
def list_jobs():
    return repository.all()

@app.get('/api/jobs/{job_id}')
def read_job(job_id: str):
    return get_job(job_id)

@app.get('/api/jobs/{job_id}/events')
async def events(job_id: str, request: Request):
    get_job(job_id)
    async def stream():
        last_revision = -1
        while not await request.is_disconnected():
            job = get_job(job_id)
            if job['revision'] != last_revision:
                last_revision = job['revision']
                yield f'id: {last_revision}\nevent: progress\ndata: {json.dumps(job, ensure_ascii=False)}\n\n'
            if job['status'] in {'ready', 'published', 'failed', 'cancelled'}:
                break
            yield ': keep-alive\n\n'
            await asyncio.sleep(.15)
    return StreamingResponse(stream(), media_type='text/event-stream', headers={'Cache-Control': 'no-cache, no-transform', 'X-Accel-Buffering': 'no'})

@app.delete('/api/jobs/{job_id}')
def cancel_job(job_id: str):
    with repository.lock(job_id):
        job = get_job(job_id)
        if job['status'] == 'published':
            raise HTTPException(409, 'A synced draft cannot be reset. Create a new listing instead.')
        job.update(status='cancelled', result=None)
        return repository.save(job)

@app.post('/api/jobs/{job_id}/retry', status_code=202)
def retry_stage(job_id: str, body: RetryRequest, background: BackgroundTasks):
    with repository.lock(job_id):
        job = get_job(job_id)
        if job['status'] not in {'ready', 'failed'}:
            raise HTTPException(409, 'Wait for this run to finish or create a new listing.')
        index = next(i for i, stage in enumerate(STAGES) if stage[0] == body.stage)
        if any(stage['status'] != 'completed' for stage in job['stages'][:index]):
            raise HTTPException(409, 'Retry the earliest unfinished stage first.')
        job.update(status='queued', result=None, store_result=None)
        for stage in job['stages'][index:]:
            stage.update(status='pending', elapsed_ms=0, demo=False, reason='')
        repository.save(job)
        enqueue(job, background, repository, index)
        return job

@app.patch('/api/jobs/{job_id}')
def edit_job(job_id: str, body: EditRequest):
    with repository.lock(job_id):
        job = get_job(job_id)
        if job['status'] != 'ready' or not job['result']:
            raise HTTPException(409, 'Only a ready, unsynced draft can be edited.')
        listing = job['result']
        listing.update(copy=body.listing_copy.model_dump(), final_price=body.final_price, language=body.language, selected_style=body.selected_style, approved=False)
        listing['translations'][body.language] = body.listing_copy.model_dump()
        return repository.save(job)

@app.get('/api/jobs/{job_id}/payload')
def payload(job_id: str, channel: str = 'shopify'):
    if channel not in {'shopify', 'woocommerce'}:
        raise HTTPException(422, 'Choose Shopify or WooCommerce.')
    job = get_job(job_id)
    if not job['result']:
        raise HTTPException(409, 'Finish processing before inspecting a payload.')
    return store_payload(job['result'], channel, settings().public_url)

@app.post('/api/jobs/{job_id}/publish')
async def publish(job_id: str, body: PublishRequest):
    if not body.approved:
        raise HTTPException(422, 'Explicit approval is required before creating a store draft.')
    with repository.lock(job_id):
        job = get_job(job_id)
        if job['status'] == 'published':
            return job
        if job['status'] != 'ready' or not job['result']:
            raise HTTPException(409, 'This listing is not ready for store sync.')
        if job['revision'] != body.revision:
            raise HTTPException(409, 'The draft changed. Review the latest version and approve again.')
        started = time.perf_counter()
        try:
            result = await Store(settings()).publish(job['result'], body.channel)
        except Exception as exc:
            result = Store(settings()).demo(job['result'], body.channel, '')
            result['message'] = f'Live store request failed ({type(exc).__name__}). A local demo record was saved. Check your store admin before retrying: a partial draft may exist.'
        job['publish_elapsed_ms'] = round((time.perf_counter()-started)*1000, 2)
        job['store_result'] = result
        job['result']['approved'] = True
        job['status'] = 'published'
        return repository.save(job)
