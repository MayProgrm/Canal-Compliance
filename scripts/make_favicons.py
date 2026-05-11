import os
from PIL import Image
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(BASE_DIR, 'static', 'images', 'gsi-logo.png')
OUT_DIR = os.path.join(BASE_DIR, 'static', 'images')
SIZES = [16, 32, 48, 180]

def make_square_icon(src_path: str, out_dir: str, size: int):
    img = Image.open(src_path).convert('RGBA')
    w, h = img.size
    scale = min(size / w, size / h)
    new_w, new_h = (int(w * scale), int(h * scale))
    resized = img.resize((new_w, new_h), Image.LANCZOS)
    canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    x = (size - new_w) // 2
    y = (size - new_h) // 2
    canvas.paste(resized, (x, y), resized)
    out_path = os.path.join(out_dir, f'favicon-{size}.png')
    canvas.save(out_path, format='PNG')
    print(f'Generated: {out_path}')

def main():
    if not os.path.exists(SRC):
        raise FileNotFoundError(f'Logo source not found: {SRC}')
    os.makedirs(OUT_DIR, exist_ok=True)
    for s in SIZES:
        make_square_icon(SRC, OUT_DIR, s)
if __name__ == '__main__':
    main()
