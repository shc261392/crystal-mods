#!/usr/bin/env python3
"""Warpstorm — draw the chapter badge stencils for the bundled scheme packs.

Each badge is a white shape on transparent, 512x512, written to
schemes/<id>/badge.png. They are simplified, original stencil drawings in the
spirit of the chapter symbols (no game or GW artwork is used).

    uv run --no-project --with pillow python schemes/make-badges.py [--sheet out.png]
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
S = 1024  # drawing canvas; saved at 512


def canvas():
    img = Image.new("L", (S, S), 0)
    return img, ImageDraw.Draw(img)


def P(*pts):
    """Points given on a 0..100 grid."""
    return [(x * S / 100, y * S / 100) for x, y in pts]


def mirror(pts):
    """Close a left-half outline by mirroring it around x=50."""
    return pts + [(100 - x, y) for x, y in reversed(pts)]


def cut(img, shape_fn):
    hole, d = canvas()
    shape_fn(d)
    return ImageChops.subtract(img, hole)


# ---------------------------------------------------------------- badges

def fist(d):
    # clenched fist seen from the front: four knuckle bars, thumb, wrist
    for i in range(4):
        x = 24 + i * 13.5
        d.rounded_rectangle(P((x, 18), (x + 12, 52)), radius=S * 0.05, fill=255)
    d.rounded_rectangle(P((22, 40), (78, 74)), radius=S * 0.06, fill=255)
    d.polygon(P((22, 52), (12, 42), (10, 56), (24, 70)), fill=255)          # thumb
    d.rounded_rectangle(P((34, 72), (66, 92)), radius=S * 0.03, fill=255)   # wrist


def fist_cuts(d):
    for i in range(3):
        x = 36 + i * 13.5
        d.line(P((x - 0.6, 20), (x - 0.6, 46)), fill=255, width=int(S * 0.012))
    d.line(P((26, 56), (74, 56)), fill=255, width=int(S * 0.012))


def lightning(d):
    d.polygon(P((60, 6), (24, 54), (46, 54), (34, 94), (78, 40), (54, 40), (70, 6)), fill=255)


def templar_cross(d):
    # cross pattée: arms narrow at the centre, flaring to wide, slightly concave ends
    c = 50
    for a in range(4):
        ang = a * math.pi / 2
        def rot(x, y):
            dx, dy = x - c, y - c
            return (c + dx * math.cos(ang) - dy * math.sin(ang), c + dx * math.sin(ang) + dy * math.cos(ang))
        arm = [rot(46, 50), rot(30, 4), rot(40, 8), rot(50, 6), rot(60, 8), rot(70, 4), rot(54, 50)]
        d.polygon(P(*arm), fill=255)
    d.rectangle(P((45, 45), (55, 55)), fill=255)


def templar_cuts(d):
    pass


def cog(d):
    teeth = 10
    for i in range(teeth):
        a = i * 2 * math.pi / teeth
        cx, cy = 50 + 36 * math.cos(a), 50 + 36 * math.sin(a)
        w = 9
        pts = []
        for k in range(4):
            aa = a + math.pi / 4 + k * math.pi / 2
            pts.append((cx + w * math.cos(aa), cy + w * math.sin(aa)))
        d.polygon(P(*pts), fill=255)
    d.ellipse(P((17, 17), (83, 83)), fill=255)


def cog_cuts(d):
    d.ellipse(P((31, 31), (69, 69)), fill=255)


def iron_hand(d):
    cog(d)


def iron_hand_cuts(d):
    cog_cuts(d)


def iron_hand_palm(d):
    # open hand centred in the cog's hole
    d.rounded_rectangle(P((41, 47), (61, 64)), radius=S * 0.03, fill=255)
    for x, top in [(41, 37), (46.5, 34), (52, 35), (57.5, 38)]:
        d.rounded_rectangle(P((x, top), (x + 4.2, 50)), radius=S * 0.018, fill=255)
    d.polygon(P((41, 54), (35, 47), (34.5, 51), (40.5, 61)), fill=255)


def wolf(d):
    # snarling wolf head, front view: ears, brow, muzzle, jaw
    left = [(50, 26), (40, 24), (30, 6), (22, 30), (16, 40), (20, 50), (14, 58), (26, 64),
            (34, 78), (42, 90), (50, 94)]
    d.polygon(P(*mirror(left)), fill=255)


def wolf_cuts(d):
    d.polygon(P((28, 44), (42, 48), (36, 54)), fill=255)          # eyes
    d.polygon(P((72, 44), (58, 48), (64, 54)), fill=255)
    d.polygon(P((44, 68), (56, 68), (50, 76)), fill=255)          # nose
    d.polygon(P((30, 16), (35, 28), (27, 31)), fill=255)          # inner ears
    d.polygon(P((70, 16), (65, 28), (73, 31)), fill=255)


def salamander(d):
    # drake head in profile facing left, crest of horns behind
    d.polygon(P((8, 58), (22, 44), (44, 36), (60, 26), (72, 10), (74, 26), (86, 16), (84, 34),
                (96, 32), (88, 48), (90, 66), (78, 84), (60, 92), (46, 88), (36, 76), (22, 72),
                (8, 66)), fill=255)


def salamander_cuts(d):
    d.polygon(P((40, 46), (54, 42), (50, 50)), fill=255)          # eye
    d.line(P((10, 62), (34, 64), (44, 74)), fill=255, width=int(S * 0.025))  # mouth line
    d.polygon(P((16, 50), (20, 48), (19, 53)), fill=255)          # nostril


def raven(d):
    # stylised raven: spread wings with head and tail, symmetric
    left = [(50, 18), (44, 22), (40, 30), (28, 26), (14, 18), (4, 22), (14, 32), (6, 38),
            (20, 44), (12, 52), (28, 54), (38, 56), (42, 66), (46, 86), (50, 92)]
    d.polygon(P(*mirror(left)), fill=255)


def raven_cuts(d):
    d.polygon(P((47, 26), (50, 34), (53, 26)), fill=255)          # beak notch


def winged_sword(d):
    # sword pointing down with spread wings (Dark Angels style)
    d.polygon(P((47, 4), (53, 4), (54, 70), (50, 96), (46, 70)), fill=255)    # blade
    d.rounded_rectangle(P((34, 22), (66, 28)), radius=S * 0.01, fill=255)     # guard
    d.ellipse(P((45.5, 0), (54.5, 9)), fill=255)                              # pommel
    for sign in (-1, 1):
        def m(x):
            return 50 + sign * (x - 50)
        feathers = [((m(56), 34), (m(96), 26), (m(88), 36)),
                    ((m(56), 40), (m(92), 40), (m(84), 48)),
                    ((m(56), 46), (m(86), 52), (m(78), 58)),
                    ((m(56), 52), (m(78), 62), (m(70), 66))]
        for f in feathers:
            d.polygon(P(*f), fill=255)


def blood_drop_wings(d):
    # winged blood drop (Blood Ravens style)
    d.ellipse(P((36, 46), (64, 76)), fill=255)
    d.polygon(P((50, 20), (37, 56), (63, 56)), fill=255)
    for sign in (-1, 1):
        def m(x):
            return 50 + sign * (x - 50)
        feathers = [((m(60), 46), (m(98), 30), (m(90), 42)),
                    ((m(61), 52), (m(94), 44), (m(86), 54)),
                    ((m(61), 58), (m(88), 58), (m(80), 66)),
                    ((m(60), 64), (m(80), 72), (m(72), 76))]
        for f in feathers:
            d.polygon(P(*f), fill=255)


def drop_cuts(d):
    d.ellipse(P((43, 58), (49, 66)), fill=255)                    # highlight


BADGES = {
    "salamanders": (salamander, salamander_cuts),
    "space-wolves": (wolf, wolf_cuts),
    "imperial-fists": (fist, fist_cuts),
    "white-scars": (lightning, None),
    "dark-angels": (winged_sword, None),
    "raven-guard": (raven, raven_cuts),
    "iron-hands": (iron_hand, None),
    "black-templars": (templar_cross, None),
    "crimson-fists": (fist, fist_cuts),
    "blood-ravens": (blood_drop_wings, drop_cuts),
}


def render(name: str) -> Image.Image:
    shape, cuts = BADGES[name]
    img, d = canvas()
    shape(d)
    if cuts:
        img = cut(img, cuts)
    if name == "iron-hands":
        img = cut(img, iron_hand_cuts)
        palm, pd = canvas()
        iron_hand_palm(pd)
        img = ImageChops.lighter(img, palm)
    img = img.filter(ImageFilter.GaussianBlur(1.2))
    alpha = img.resize((512, 512), Image.LANCZOS)
    out = Image.new("RGBA", (512, 512), (255, 255, 255, 0))
    out.putalpha(alpha)
    return out


def main() -> None:
    images = {}
    for name in BADGES:
        img = render(name)
        dest = HERE / name / "badge.png"
        dest.parent.mkdir(parents=True, exist_ok=True)
        img.save(dest, optimize=True)
        images[name] = img
    if "--sheet" in sys.argv:
        out = Path(sys.argv[sys.argv.index("--sheet") + 1])
        sheet = Image.new("RGBA", (5 * 220, 2 * 240), (40, 40, 48, 255))
        d = ImageDraw.Draw(sheet)
        for i, (name, img) in enumerate(images.items()):
            x, y = (i % 5) * 220 + 10, (i // 5) * 240 + 10
            sheet.alpha_composite(img.resize((200, 200)), (x, y))
            d.text((x, y + 205), name, fill=(240, 240, 240, 255))
        sheet.save(out)
        print("sheet ->", out)
    print("wrote", len(images), "badges")


if __name__ == "__main__":
    main()
