#!/usr/bin/env python3
"""Turn a downloaded icon image into Android launcher PNGs for all densities.

Usage: python3 scripts/make_icons.py <image-file>
Removes the adaptive-icon XML so the custom PNGs are used on every API level.
"""
import os, sys
from PIL import Image, ImageDraw, ImageOps

src = sys.argv[1]
img = Image.open(src).convert("RGBA")
img = ImageOps.fit(img, (512, 512), Image.LANCZOS)  # center-crop to square

dens = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
base = "app/src/main/res"
for d, size in dens.items():
    out = os.path.join(base, f"mipmap-{d}")
    os.makedirs(out, exist_ok=True)
    icon = img.resize((size, size), Image.LANCZOS)
    icon.save(os.path.join(out, "ic_launcher.png"))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size, size], fill=255)
    rnd = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    rnd.paste(icon, (0, 0), mask)
    rnd.save(os.path.join(out, "ic_launcher_round.png"))

for f in ("ic_launcher.xml", "ic_launcher_round.xml"):
    p = os.path.join(base, "mipmap-anydpi-v26", f)
    if os.path.exists(p):
        os.remove(p)
print("custom icons generated for all densities")
