"""Environment-only secrets. Reload explicit settings changes across API/worker processes."""
import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv, set_key

ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = Path(os.getenv('SETTINGS_ENV_FILE') or ROOT / '.env')

@dataclass(frozen=True)
class Settings:
    demo: bool
    data_dir: Path
    public_url: str
    redis_url: str
    segmentation: str
    background: str
    vision: str
    price: str
    timeout: float
    attempts: int

def settings() -> Settings:
    load_dotenv(ENV_FILE, override=True)
    return Settings(
        os.getenv('DEMO_MODE', 'true').lower() == 'true',
        Path(os.getenv('DATA_DIR', str(ROOT / 'data'))).resolve(),
        os.getenv('PUBLIC_BASE_URL', 'http://localhost:3000').rstrip('/'),
        os.getenv('REDIS_URL', ''), os.getenv('SEGMENTATION_PROVIDER', 'fal'),
        os.getenv('BACKGROUND_PROVIDER', 'fal'), os.getenv('VISION_PROVIDER', 'gemini'),
        os.getenv('PRICE_PROVIDER', 'tavily'), min(90, max(1, float(os.getenv('STAGE_TIMEOUT_SECONDS', '25')))),
        min(3, max(1, int(os.getenv('STAGE_MAX_ATTEMPTS', '2')))),
    )

SECRET_FIELDS = {'gemini_api_key', 'openai_api_key', 'fal_key', 'replicate_api_token', 'tavily_api_key', 'serpapi_api_key', 'shopify_access_token', 'woocommerce_key', 'woocommerce_secret'}
PUBLIC_FIELDS = {'demo_mode', 'vision_provider', 'price_provider', 'segmentation_provider', 'background_provider', 'gemini_model', 'shopify_domain', 'woocommerce_url'}

def public_settings() -> dict:
    config = settings()
    return {**{name: os.getenv(name.upper(), '') for name in PUBLIC_FIELDS},
            'demo_mode': config.demo, 'vision_provider': config.vision, 'price_provider': config.price,
            'segmentation_provider': config.segmentation, 'background_provider': config.background,
            'configured': {name: bool(os.getenv(name.upper())) for name in SECRET_FIELDS}}

def save_settings(values: dict) -> dict:
    ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    ENV_FILE.touch(exist_ok=True)
    for name, value in values.items():
        if name not in SECRET_FIELDS | PUBLIC_FIELDS:
            continue
        if name in SECRET_FIELDS and not value:
            continue  # Blank secret fields preserve the saved credential.
        text = str(value).lower() if isinstance(value, bool) else str(value).strip()
        set_key(str(ENV_FILE), name.upper(), text)
        os.environ[name.upper()] = text
    return public_settings()
