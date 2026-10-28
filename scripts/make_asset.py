#!/usr/bin/env python3
"""Turn a generated raster into a small transparent PNG asset.

Usage: make_asset.py in.png out.png [--size 256] [--bg auto|white|black|#rrggbb]
                     [--tol 40] [--mono "#7fe3ff"] [--colors 32]

Steps: remove background (rembg if installed, else corner-color chroma key),
optionally recolor to a single color (monocolor icons), trim, resize to fit
--size px, quantize to --colors, save optimized PNG.
Requires Pillow (pip install pillow). Optional: rembg, pngquant.
"""
import argparse, shutil, subprocess, sys
from PIL import Image

def chroma_key(img, bg, tol):
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size
    if bg == "auto":
        corners = [px[0, 0], px[w-1, 0], px[0, h-1], px[w-1, h-1]]
        bg = tuple(sum(c[i] for c in corners) // 4 for i in range(3))
    elif bg == "white": bg = (255, 255, 255)
    elif bg == "black": bg = (0, 0, 0)
    else:
        bg = tuple(int(bg.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            # Euclidean-like distance normalized across color channels
            d = max(abs(r - bg[0]), abs(g - bg[1]), abs(b - bg[2]))
            if d < tol:
                px[x, y] = (r, g, b, 0)
            elif d < tol * 2:
                px[x, y] = (r, g, b, int(255 * (d - tol) / tol))
            else:
                px[x, y] = (r, g, b, 255)
    return img

def main():
    p = argparse.ArgumentParser()
    p.add_argument("src"); p.add_argument("dst")
    p.add_argument("--size", type=int, default=256)
    p.add_argument("--bg", default="auto")
    p.add_argument("--tol", type=int, default=40)
    p.add_argument("--mono", default=None, help="recolor all opaque pixels to this hex color")
    p.add_argument("--colors", type=int, default=32)
    a = p.parse_args()

    img = Image.open(a.src)
    try:
        from rembg import remove
        img = remove(img.convert("RGBA"))
    except Exception:
        img = chroma_key(img, a.bg, a.tol)

    if a.mono:
        c = tuple(int(a.mono.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
        alpha = img.split()[3]
        # use luminance-invariant alpha: keep existing alpha, flatten color
        img = Image.new("RGBA", img.size, c + (0,))
        img.putalpha(alpha)

    bbox = img.getbbox()
    if bbox: img = img.crop(bbox)
    img.thumbnail((a.size, a.size), Image.LANCZOS)

    q = img.quantize(colors=a.colors, method=Image.FASTOCTREE).convert("RGBA") if not a.mono else img
    if not a.mono:
        q.putalpha(img.split()[3])
    q.save(a.dst, optimize=True)
    if shutil.which("pngquant"):
        subprocess.run(["pngquant", "--force", "--ext", ".png", "--quality=60-90", a.dst])
    print(f"Wrote {a.dst} {q.size}")

if __name__ == "__main__":
    sys.exit(main())
