"""
Image compressor — reduces file size with minimal visible quality loss.

Usage:
    python compress_image.py input.jpg
    python compress_image.py input.jpg output.jpg
    python compress_image.py ./events/          # compress all images in a folder

Install once:
    pip install Pillow
"""

import sys
import os
from pathlib import Path
from PIL import Image, ImageOps

# ---- SETTINGS ----
MAX_WIDTH = 1600        # resize down if wider than this (px)
QUALITY = 85            # JPEG quality (85 = near-invisible loss)
PROGRESSIVE = True      # progressive JPEGs load faster on web
KEEP_METADATA = False   # strip EXIF (smaller file, more privacy)


def compress_one(src: Path, dst: Path):
    img = Image.open(src)

    # respect EXIF rotation (phones store rotation as metadata)
    img = ImageOps.exif_transpose(img)

    # convert to RGB (JPEGs can't be RGBA)
    if img.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # resize if too wide
    if img.width > MAX_WIDTH:
        ratio = MAX_WIDTH / img.width
        new_h = int(img.height * ratio)
        img = img.resize((MAX_WIDTH, new_h), Image.LANCZOS)

    # save with high-quality JPEG settings
    save_args = {
        "format": "JPEG",
        "quality": QUALITY,
        "optimize": True,
        "progressive": PROGRESSIVE,
        "subsampling": 0,      
    }

    img.save(dst, **save_args)

    orig_kb = src.stat().st_size / 1024
    new_kb = dst.stat().st_size / 1024
    saved = 100 * (1 - new_kb / orig_kb)
    print(f"  {src.name}: {orig_kb:.0f} KB -> {new_kb:.0f} KB  ({saved:.0f}% smaller)")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    src = Path(sys.argv[1])

    if src.is_dir():
        # process a whole folder
        exts = {".jpg", ".jpeg", ".png", ".webp"}
        out_dir = src / "compressed"
        out_dir.mkdir(exist_ok=True)
        files = [f for f in src.iterdir() if f.suffix.lower() in exts]
        print(f"Compressing {len(files)} images from {src} -> {out_dir}")
        for f in files:
            compress_one(f, out_dir / (f.stem + ".jpg"))
    else:
        # single file
        dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_name(src.stem + "_compressed.jpg")
        compress_one(src, dst)

    print("Done.")


if __name__ == "__main__":
    main()
