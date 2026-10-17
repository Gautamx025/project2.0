"""Real image validation and local, explicitly labeled demo compositing."""
import io
import math
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps, UnidentifiedImageError

MAX_BYTES = 10 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 30_000_000

def normalize_image(content: bytes) -> Image.Image:
    if not content or len(content) > MAX_BYTES:
        raise ValueError('Each photo must be non-empty and no larger than 10 MB.')
    try:
        image = Image.open(io.BytesIO(content))
        if image.format not in {'JPEG', 'PNG', 'WEBP'}:
            raise ValueError('Use a JPG, PNG or WebP photo.')
        image.load()
        image = ImageOps.exif_transpose(image).convert('RGB')
        if min(image.size) < 64:
            raise ValueError('Photos must be at least 64 pixels on each side.')
        image.thumbnail((1400, 1400))
        return image
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError('This file could not be decoded as a supported photo.') from exc

def demo_cutout(source: Path, destination: Path) -> str:
    """Edge-color heuristic, never described as a SAM result."""
    image = Image.open(source).convert('RGBA')
    image.thumbnail((1000, 1000))
    rgb = image.convert('RGB')
    corners = [rgb.getpixel(p) for p in [(0, 0), (rgb.width-1, 0), (0, rgb.height-1), (rgb.width-1, rgb.height-1)]]
    background = tuple(sum(c[i] for c in corners)//4 for i in range(3))
    difference = ImageChops.difference(rgb, Image.new('RGB', rgb.size, background)).convert('L')
    alpha = difference.point(lambda value: max(0, min(255, (value-12)*8)))
    image.putalpha(alpha.filter(ImageFilter.GaussianBlur(.6)))
    image.save(destination)
    return str(destination)

def compose_variant(cutout: Path, destination: Path, style: str) -> str:
    size = 1000
    colors = {'studio': '#fdfcf8', 'shadow': '#e3ded3', 'lifestyle': '#d4d5bc', 'color': '#ddb3a2'}
    image = Image.new('RGB', (size, size), colors[style])
    draw = ImageDraw.Draw(image)
    if style == 'lifestyle':
        draw.rectangle((0, 660, 1000, 1000), fill='#bba58b')
        draw.rectangle((65, 70, 350, 530), fill='#ede7d6')
        for x in (155, 250):
            draw.line((x, 70, x, 530), fill='#bab9a1', width=9)
        draw.line((65, 300, 350, 300), fill='#bab9a1', width=9)
    shadow = Image.new('RGBA', image.size)
    ImageDraw.Draw(shadow).ellipse((240, 800, 800, 880), fill=(30, 30, 25, 50))
    image = Image.alpha_composite(image.convert('RGBA'), shadow.filter(ImageFilter.GaussianBlur(22)))
    product = Image.open(cutout).convert('RGBA')
    box = product.getbbox()
    if box:
        product = product.crop(box)
    product.thumbnail((650, 740))
    image.alpha_composite(product, ((size-product.width)//2, 830-product.height))
    image.convert('RGB').save(destination, quality=90)
    return str(destination)
