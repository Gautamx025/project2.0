import asyncio
import time
import uuid
from pathlib import Path
from .adapters import Background, Price, Segmentation, Vision, execute
from .config import settings
from .models import ListingCopy
from .repository import Repository

STAGES = [
    ('ingestion', 'Photo ingestion', 'Validate your photos and prepare a clean working image.'),
    ('isolation', 'Foreground isolation', 'Separate the product from the scene around it.'),
    ('background', 'Studio background', 'Develop four settings while keeping the product in frame.'),
    ('metadata', 'Product copy', 'Read the photos and write editable copy in three languages.'),
    ('pricing', 'Market pricing', 'Find comparable INR offers and show where each price came from.'),
    ('draft', 'Draft assembly', 'Package a store-ready draft. Store sync waits for your approval.'),
]

def new_job(source_urls: list[str], key: str, style: str, language: str) -> dict:
    return {'id': str(uuid.uuid4()), 'status': 'queued', 'created_at': time.time(), 'revision': 0,
            'source_images': source_urls, 'sample_key': key, 'style': style, 'language': language,
            'elapsed_ms': 0, 'queue': 'background', 'queue_warning': '', 'demo_data': False, 'error': '',
            'stages': [{'key': key, 'name': name, 'description': description, 'status': 'pending', 'elapsed_ms': 0, 'demo': False, 'reason': '', 'attempts': 0} for key, name, description in STAGES],
            'artifacts': {}, 'result': None, 'store_result': None}

class Cancelled(Exception):
    pass

async def run_job(job_id: str, start_stage: int = 0):
    config = settings()
    repository = Repository(config.data_dir)
    job = repository.get(job_id)
    if job['status'] == 'cancelled':
        return
    job.update(status='processing', error='')
    def persist():
        with repository.lock(job_id):
            if repository.get(job_id)['status'] == 'cancelled':
                raise Cancelled()
            repository.save(job)
    try:
        persist()
    except Cancelled:
        return
    started = time.perf_counter()
    base_elapsed = sum(stage['elapsed_ms'] for stage in job['stages'][:start_stage])
    def check_cancelled():
        if repository.get(job_id)['status'] == 'cancelled':
            raise Cancelled()
    sources = [repository.media / Path(url).name for url in job['source_images']]
    artifacts = job['artifacts']
    for index in range(start_stage, len(STAGES)):
        stage = job['stages'][index]
        stage.update(status='running', reason='', demo=False, attempts=0)
        try:
            persist()
            stage_start = time.perf_counter()
            def retry(attempt, reason):
                stage.update(attempts=attempt, reason=reason+' Retrying with backoff.')
                persist()
            outcome = None
            if index == 0:
                from .imaging import normalize_image
                for source in sources:
                    await asyncio.to_thread(normalize_image, source.read_bytes())
            elif index == 1:
                outcome = await execute(Segmentation(config.segmentation, job['sample_key']), config, sources[0], repository.media / f'{job_id}-cutout.png', on_retry=retry)
                artifacts['cutout'] = outcome.value
            elif index == 2:
                async def variant(style):
                    return style, await execute(Background(config.background), config, Path(artifacts['cutout']), repository.media / f'{job_id}-{style}.png', style)
                results = await asyncio.gather(*(variant(style) for style in ('studio', 'shadow', 'lifestyle', 'color')))
                artifacts['variants'] = {style: '/media/'+Path(result.value).name for style, result in results}
                artifacts['variant_provenance'] = {style: {'demo': result.demo, 'reason': result.reason, 'provider': result.provider} for style, result in results}
                outcome = next((result for _, result in results if result.demo), results[0][1])
            elif index == 3:
                outcome = await execute(Vision(config.vision), config, sources, job['sample_key'], on_retry=retry)
                artifacts['vision'] = outcome.value.model_dump()
            elif index == 4:
                outcome = await execute(Price(config.price, repository), config, artifacts['vision']['title'], job['sample_key'], on_retry=retry)
                artifacts['price'] = outcome.value.model_dump()
            elif index == 5:
                vision = artifacts['vision']
                translations = {'en': ListingCopy.model_validate({key: vision[key] for key in ListingCopy.model_fields}).model_dump(), 'hi': vision['hindi'], 'mr': vision['marathi']}
                job['result'] = {'id': job_id, 'sku': 'S2S-'+job_id[:8].upper(), 'category': vision['category'], 'material': vision['material'], 'color': vision['color'], 'translations': translations, 'language': job['language'], 'copy': translations[job['language']], 'price': artifacts['price'], 'final_price': artifacts['price']['median'], 'variants': artifacts['variants'], 'variant_provenance': artifacts['variant_provenance'], 'selected_style': job['style'], 'source_images': job['source_images'], 'demo_data': job['demo_data'], 'approved': False}
            check_cancelled()
            if outcome:
                stage.update(demo=outcome.demo, reason=outcome.reason, attempts=outcome.attempts, provider=outcome.provider)
            stage.update(status='completed', elapsed_ms=round((time.perf_counter()-stage_start)*1000, 2))
            job['demo_data'] = any(item['demo'] for item in job['stages'])
            job['elapsed_ms'] = round(base_elapsed+(time.perf_counter()-started)*1000, 2)
            persist()
        except Cancelled:
            return
        except Exception as exc:
            stage.update(status='failed', elapsed_ms=round((time.perf_counter()-stage_start)*1000, 2), reason=f'{type(exc).__name__}: stage could not finish. Retry this stage.')
            job.update(status='failed', error=stage['reason'], elapsed_ms=round(base_elapsed+(time.perf_counter()-started)*1000, 2))
            try:
                persist()
            except Cancelled:
                pass
            return
    job['result']['demo_data'] = job['demo_data']
    job['status'] = 'ready'
    try:
        persist()
    except Cancelled:
        return
