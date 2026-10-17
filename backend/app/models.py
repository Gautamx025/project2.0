from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

Language = Literal['en', 'hi', 'mr']
Style = Literal['studio', 'shadow', 'lifestyle', 'color']
StageKey = Literal['ingestion', 'isolation', 'background', 'metadata', 'pricing', 'draft']

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')

class ListingCopy(StrictModel):
    title: str = Field(min_length=3, max_length=160)
    tags: list[str] = Field(min_length=1, max_length=12)
    bullet_points: list[str] = Field(min_length=1, max_length=6)
    description: str = Field(min_length=10, max_length=3000)
    seo_title: str = Field(min_length=3, max_length=100)
    seo_description: str = Field(min_length=10, max_length=320)

class VisionOutput(ListingCopy):
    material: str = Field(min_length=1, max_length=120)
    color: str = Field(min_length=1, max_length=80)
    category: str = Field(min_length=1, max_length=120)
    hindi: ListingCopy
    marathi: ListingCopy

class Comparable(StrictModel):
    title: str
    url: str
    price: float = Field(gt=0)
    currency: Literal['INR'] = 'INR'
    demo: bool = False

class PriceRange(StrictModel):
    low: float = Field(gt=0)
    median: float = Field(gt=0)
    high: float = Field(gt=0)
    currency: Literal['INR'] = 'INR'
    sources: list[Comparable]
    cached: bool = False

class SampleRequest(StrictModel):
    sample: Literal['bottle', 'watch', 'bag'] = 'bottle'
    style: Style = 'studio'
    language: Language = 'en'

class EditRequest(StrictModel):
    listing_copy: ListingCopy = Field(alias='copy')
    final_price: float = Field(gt=0, le=10_000_000)
    language: Language = 'en'
    selected_style: Style = 'studio'

class PublishRequest(StrictModel):
    channel: Literal['shopify', 'woocommerce']
    approved: bool = False
    revision: int

class RetryRequest(StrictModel):
    stage: StageKey

class ConnectionRequest(StrictModel):
    channel: Literal['shopify', 'woocommerce']

class SettingsRequest(StrictModel):
    demo_mode: bool | None = None
    vision_provider: Literal['gemini', 'openai'] | None = None
    price_provider: Literal['tavily', 'serpapi'] | None = None
    segmentation_provider: Literal['fal', 'replicate', 'rembg'] | None = None
    background_provider: Literal['fal', 'replicate'] | None = None
    gemini_model: str | None = Field(default=None, max_length=100)
    shopify_domain: str | None = Field(default=None, max_length=200)
    woocommerce_url: str | None = Field(default=None, max_length=300)
    shopify_access_token: str | None = Field(default=None, max_length=500)
    woocommerce_key: str | None = Field(default=None, max_length=500)
    woocommerce_secret: str | None = Field(default=None, max_length=500)
    gemini_api_key: str | None = Field(default=None, max_length=500)
    openai_api_key: str | None = Field(default=None, max_length=500)
    fal_key: str | None = Field(default=None, max_length=500)
    replicate_api_token: str | None = Field(default=None, max_length=500)
    tavily_api_key: str | None = Field(default=None, max_length=500)
    serpapi_api_key: str | None = Field(default=None, max_length=500)
