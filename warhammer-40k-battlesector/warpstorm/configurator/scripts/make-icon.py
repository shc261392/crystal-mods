#!/usr/bin/env python3
"""Warpstorm — render the configurator's app icon.

Draws an original "warp vortex" mark (no game artwork) and writes:
  branding/warpstorm.ico   multi-size Windows icon (16..256) -> csproj ApplicationIcon
  branding/warpstorm.png   256 px PNG                       -> Avalonia Window.Icon

The output is committed; re-run only to change the design:
    uv run --no-project --with pillow python scripts/make-icon.py
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent.parent / "branding"
S = 1024  # supersampled canvas; downscaled for every icon size

VOID = (22, 18, 16, 255)
GOLD = (226, 178, 74, 255)
GOLD_DIM = (150, 112, 46, 255)
WARP_A = (186, 66, 255)
WARP_B = (255, 92, 150)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def render() -> Image.Image:
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = S / 2

    # Round plate only: the corners stay fully transparent.
    pr = S * 0.47
    d.ellipse([c - pr, c - pr, c + pr, c + pr], fill=VOID)

    # Warp glow behind the vortex.
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    r = S * 0.34
    gd.ellipse([c - r, c - r, c + r, c + r], fill=(120, 30, 190, 90))
    glow = glow.filter(ImageFilter.GaussianBlur(S * 0.06))
    img.alpha_composite(glow)

    # Vortex: three spiral arms of dots, thinning toward the centre.
    vortex = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vortex)
    arms = 3
    for arm in range(arms):
        base = arm * 2 * math.pi / arms
        steps = 420
        for i in range(steps):
            t = i / steps
            radius = S * 0.34 * (1 - t) ** 1.3
            angle = base + t * 2.4 * math.pi
            x = c + radius * math.cos(angle)
            y = c + radius * math.sin(angle)
            w = S * (0.034 * (1 - t) ** 0.8 + 0.006)
            col = lerp(WARP_A, WARP_B, t)
            vd.ellipse([x - w, y - w, x + w, y + w], fill=col + (235,))
    img.alpha_composite(vortex.filter(ImageFilter.GaussianBlur(S * 0.004)))

    # Eye of the storm.
    er = S * 0.06
    d = ImageDraw.Draw(img)
    d.ellipse([c - er, c - er, c + er, c + er], fill=(255, 236, 250, 255))

    # Gilded ring.
    rr = S * 0.47
    d.ellipse([c - rr, c - rr, c + rr, c + rr], outline=GOLD, width=int(S * 0.04))
    rr2 = rr - S * 0.055
    d.ellipse([c - rr2, c - rr2, c + rr2, c + rr2], outline=GOLD_DIM, width=int(S * 0.012))
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    big = render()
    png = big.resize((256, 256), Image.LANCZOS)
    png.save(OUT / "warpstorm.png", optimize=True)
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    big.resize((256, 256), Image.LANCZOS).save(OUT / "warpstorm.ico", sizes=sizes)
    print("wrote", OUT / "warpstorm.ico", "and", OUT / "warpstorm.png")


if __name__ == "__main__":
    main()
