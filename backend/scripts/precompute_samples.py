"""One-time asset preparation, never invoked by the offline demo at runtime."""
import io
import os
from pathlib import Path
from rembg import new_session, remove
from backend.app.imaging import normalize_image

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault('U2NET_HOME', str(ROOT/'data'/'models'))

if __name__ == '__main__':
    session = new_session('u2netp', providers=['CPUExecutionProvider'])
    for key in ('bottle', 'watch', 'bag'):
        source = ROOT/'frontend'/'public'/'samples'/f'{key}.jpg'
        image = normalize_image(source.read_bytes())
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        output = remove(buffer.getvalue(), session=session)
        destination = source.with_name(key+'-cutout.png')
        destination.write_bytes(output)
        print(f'{destination.name}: {len(output)} bytes', flush=True)
