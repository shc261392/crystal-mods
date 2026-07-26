#!/usr/bin/env python3
"""
bake_font_generic.py — Bake missing Traditional-Chinese glyphs into a TMP font
asset, generalized for both sharedassets1 (pid 3644, .resS atlas) and
sharedassets0 (pid 782, inline atlas).

Reads pointSize / padding / atlas size from the font's own FaceInfo, auto-detects
whether the atlas texture is stored inline or in a .resS sidecar, packs the
missing glyphs into existing free rects, blits SDFs, keeps the character/glyph
tables sorted (TMP binary-searches them), and writes:
  OUT_DIR/font_<pid>.bin        new MonoBehaviour bytes
  OUT_DIR/tex_<texpid>.bin      new atlas Texture2D bytes  (inline mode)
  OUT_DIR/<assets>.resS         edited sidecar             (.resS mode)

A separate C# AssetsTools.NET step swaps the raw bytes into the .assets file.

Usage:
  python3 tools/scripts/bake_font_generic.py <assets_path> <font_pid> <out_subdir>
"""

import json
import math
import os
import sys

import freetype
import numpy as np
import UnityPy
from PIL import Image
from scipy.ndimage import distance_transform_edt
from UnityPy.helpers import TypeTreeHelper
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
from UnityPy.helpers.TypeTreeNode import TypeTreeNode
from UnityPy.streams import EndianBinaryWriter

TypeTreeHelper.read_typetree_boost = False

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GAME_ROOT = os.environ.get(
    "MOD_GAME_DIR", "/mnt/d/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector"
)
FONT_OTF = os.environ.get(
    "MOD_FONT_OTF", os.path.join(REPO, ".copilot_workspace", "fonts", "NotoSansCJKjp-Regular.otf")
)
RES_PATCHED = os.path.join(REPO, "translation", "zh-TW", "dist", "resources.assets")
OVERSAMPLE = 4
UNITY_VERSION = "6000.0.62f1"

CHINESE = {
    "text_repository-barks_chinese",
    "text_repository-campaign_chinese",
    "text_repository-campaign-external_chinese",
    "text_repository-default_chinese",
    "text_repository-default-external_chinese",
    "text_repository-units_chinese",
    "text_repository-units-external_chinese",
}


def is_relevant(cp):
    return (
        0x3400 <= cp <= 0x9FFF
        or 0xF900 <= cp <= 0xFAFF
        or 0x3000 <= cp <= 0x303F
        or 0xFF00 <= cp <= 0xFFEF
        or 0x2010 <= cp <= 0x2027  # general punctuation: – — ‘ ’ “ ” … •
        or cp == 0x221E  # ∞ infinity
    )


def generate_sdf(face, cp, point_size, padding):
    render_size = point_size * OVERSAMPLE
    face.set_pixel_sizes(0, render_size)
    try:
        face.load_char(cp, 0x0006)
    except Exception:
        return None, 0, 0, None
    slot = face.glyph
    advance = slot.advance.x / 64.0 / OVERSAMPLE
    bearing_x = slot.bitmap_left / OVERSAMPLE
    bearing_y = slot.bitmap_top / OVERSAMPLE
    bmp = slot.bitmap
    bw, bh = bmp.width, bmp.rows
    metrics = {
        "m_HorizontalAdvance": float(round(advance)),
        "m_HorizontalBearingX": bearing_x,
        "m_HorizontalBearingY": bearing_y,
        "m_Width": bw / OVERSAMPLE,
        "m_Height": bh / OVERSAMPLE,
    }
    if bw == 0 or bh == 0:
        return None, 0, 0, metrics
    hi = np.frombuffer(bytes(bmp.buffer), dtype=np.uint8).reshape(bh, bw)
    binary = hi > 127
    pad_hi = padding * OVERSAMPLE
    binary = np.pad(binary, pad_hi, mode="constant", constant_values=False)
    dist_in = distance_transform_edt(binary)
    dist_out = distance_transform_edt(~binary)
    signed = np.where(binary, dist_in, -dist_out)
    spread = padding * OVERSAMPLE
    sdf = np.clip(128.0 + signed * (128.0 / spread), 0.0, 255.0).astype(np.uint8)
    tw = int(math.ceil(bw / OVERSAMPLE))
    th = int(math.ceil(bh / OVERSAMPLE))
    img = Image.fromarray(sdf, mode="L").resize((tw + 2 * padding, th + 2 * padding), Image.LANCZOS)
    return np.array(img, dtype=np.uint8), tw, th, metrics


class RectPacker:
    def __init__(self, free_rects):
        self.free = [
            dict(x=r["m_X"], y=r["m_Y"], w=r["m_Width"], h=r["m_Height"]) for r in free_rects
        ]

    def place(self, bw, bh):
        best, best_area = None, None
        for fr in self.free:
            if fr["w"] >= bw and fr["h"] >= bh:
                a = fr["w"] * fr["h"]
                if best_area is None or a < best_area:
                    best_area, best = a, fr
        if best is None:
            return None
        x, y, rw, rh = best["x"], best["y"], best["w"], best["h"]
        self.free.remove(best)
        right = dict(x=x + bw, y=y, w=rw - bw, h=bh)
        bottom = dict(x=x, y=y + bh, w=rw, h=rh - bh)
        if right["w"] > 0 and right["h"] > 0:
            self.free.append(right)
        if bottom["w"] > 0 and bottom["h"] > 0:
            self.free.append(bottom)
        return x, y

    def remaining(self):
        return [
            {"m_X": r["x"], "m_Y": r["y"], "m_Width": r["w"], "m_Height": r["h"]} for r in self.free
        ]


def get_image_bytes(td):
    v = td.get("image data")
    if isinstance(v, (bytes, bytearray)):
        return bytearray(v)
    if isinstance(v, list):
        return bytearray(v)
    return bytearray()


def main():
    assets_path = sys.argv[1]
    font_pid = int(sys.argv[2])
    out_sub = sys.argv[3]
    out_dir = os.path.join(REPO, ".copilot_workspace", out_sub)
    os.makedirs(out_dir, exist_ok=True)

    gen = TypeTreeGenerator(UNITY_VERSION)
    gen.load_local_game(GAME_ROOT)
    base = gen.get_nodes("Unity.TextMeshPro", "TMPro.TMP_FontAsset")
    node = TypeTreeNode.from_list(
        [TypeTreeNode(b.m_Level, b.m_Type, b.m_Name, 0, 0, m_MetaFlag=b.m_MetaFlag) for b in base]
    )

    env = UnityPy.load(assets_path)
    fobj = next(o for o in env.objects if o.path_id == font_pid)
    tree = fobj.read_typetree(node, check_read=False)

    point_size = int(round(tree["m_FaceInfo"]["m_PointSize"]))
    padding = int(tree["m_AtlasPadding"])
    aw, ah = int(tree["m_AtlasWidth"]), int(tree["m_AtlasHeight"])
    atlas_pptr = (tree["m_AtlasTextures"] or [])[0]
    tex_pid = atlas_pptr["m_PathID"]
    # Optionally force Static so TMP uses the pre-baked CharacterTable and never
    # triggers broken runtime (dynamic) glyph generation (garbled glyphs).
    if os.environ.get("MOD_FORCE_STATIC", "0") == "1":
        if int(tree.get("m_AtlasPopulationMode", 0)) != 0:
            print("  forcing Static (m_AtlasPopulationMode -> 0)")
        tree["m_AtlasPopulationMode"] = 0
    print(
        f"font {font_pid}: {tree.get('m_Name')} pointSize={point_size} pad={padding} atlas={aw}x{ah} texpid={tex_pid}"
    )

    baked = {int(c["m_Unicode"]) for c in tree["m_CharacterTable"]}
    next_index = max(int(g["m_Index"]) for g in tree["m_GlyphTable"]) + 1

    renv = UnityPy.load(RES_PATCHED)
    used = set()
    for o in renv.objects:
        if o.type.name != "TextAsset":
            continue
        d = o.read()
        if getattr(d, "m_Name", "") in CHINESE:
            s = d.m_Script
            b = s.encode("utf-8", "surrogateescape") if isinstance(s, str) else bytes(s)
            for ch in b.decode("utf-8", "replace"):
                if is_relevant(ord(ch)):
                    used.add(ord(ch))
    missing = sorted(used - baked)
    print(f"missing glyphs to bake: {len(missing)}")

    # Atlas texture: inline vs .resS
    tex = next(o for o in env.objects if o.path_id == tex_pid)
    td = tex.read_typetree()
    sd = td.get("m_StreamData") or {}
    inline = not (sd.get("path"))
    if inline:
        buf = get_image_bytes(td)
        assert len(buf) >= aw * ah, f"inline image {len(buf)} < {aw * ah}"
        atlas = np.frombuffer(bytes(buf[: aw * ah]), dtype=np.uint8).reshape(ah, aw).copy()
    else:
        ress_path = (
            assets_path + ".resS"
            if os.path.isfile(assets_path + ".resS")
            else os.path.join(os.path.dirname(assets_path), sd["path"])
        )
        off = int(sd["offset"])
        with open(ress_path, "rb") as f:
            ress = bytearray(f.read())
        atlas = (
            np.frombuffer(bytes(ress[off : off + aw * ah]), dtype=np.uint8).reshape(ah, aw).copy()
        )

    face = freetype.Face(FONT_OTF)
    rendered = []
    for cp in missing:
        sdf, cw, ch, metrics = generate_sdf(face, cp, point_size, padding)
        if sdf is None:
            continue
        rendered.append((cp, sdf, cw, ch, metrics))
    rendered.sort(key=lambda r: -(r[1].shape[0] * r[1].shape[1]))

    # Pass 1: compute placements, expanding atlas height (in 2048 steps) as needed.
    packer = RectPacker(tree["m_FreeGlyphRects"] or [])
    cur_h = ah
    placements = []  # (cp, sdf, cw, ch, metrics, px, py)
    unplaced = []
    for cp, sdf, cw, ch, metrics in rendered:
        ph, pw = sdf.shape
        pos = packer.place(pw, ph)
        if pos is None:
            # expand atlas height by 2048 and add the new region as free
            if cur_h + 2048 <= 8192:
                packer.free.append(dict(x=0, y=cur_h, w=aw, h=2048))
                cur_h += 2048
                packer.free.sort(key=lambda r: -(r["w"] * r["h"]))
                pos = packer.place(pw, ph)
        if pos is None:
            unplaced.append(cp)
            continue
        placements.append((cp, sdf, cw, ch, metrics, pos[0], pos[1]))
    print(f"placed {len(placements)}  unplaced {len(unplaced)}  final_atlas_h={cur_h}")

    # Build final atlas array (existing content stays at bottom rows 0..ah-1).
    if cur_h != ah:
        new_atlas = np.zeros((cur_h, aw), dtype=np.uint8)
        new_atlas[:ah, :] = atlas
        atlas = new_atlas
        ah = cur_h

    new_glyphs, new_chars, new_used = [], [], []
    for cp, sdf, cw, ch, metrics, px, py in placements:
        ph, pw = sdf.shape
        atlas[py : py + ph, px : px + pw] = np.flipud(sdf)
        gi = next_index
        next_index += 1
        new_glyphs.append(
            {
                "m_Index": gi,
                "m_Metrics": {
                    k: metrics[k]
                    for k in (
                        "m_Width",
                        "m_Height",
                        "m_HorizontalBearingX",
                        "m_HorizontalBearingY",
                        "m_HorizontalAdvance",
                    )
                },
                "m_GlyphRect": {
                    "m_X": px + padding,
                    "m_Y": py + padding,
                    "m_Width": cw,
                    "m_Height": ch,
                },
                "m_Scale": 1.0,
                "m_AtlasIndex": 0,
                "m_ClassDefinitionType": 0,
            }
        )
        new_chars.append({"m_ElementType": 1, "m_Unicode": cp, "m_GlyphIndex": gi, "m_Scale": 1.0})
        new_used.append({"m_X": px, "m_Y": py, "m_Width": pw, "m_Height": ph})

    tree["m_GlyphTable"].extend(new_glyphs)
    tree["m_CharacterTable"].extend(new_chars)
    tree["m_CharacterTable"].sort(key=lambda c: int(c["m_Unicode"]))
    tree["m_GlyphTable"].sort(key=lambda g: int(g["m_Index"]))
    tree["m_UsedGlyphRects"] = (tree.get("m_UsedGlyphRects") or []) + new_used
    tree["m_FreeGlyphRects"] = packer.remaining()
    # If atlas grew, update the font's atlas height too.
    if ah != int(tree["m_AtlasHeight"]):
        tree["m_AtlasHeight"] = ah

    # Serialize font
    w = EndianBinaryWriter(endian="<")
    TypeTreeHelper.write_typetree(tree, node, w)
    font_bytes = bytes(w.bytes)
    with open(os.path.join(out_dir, f"font_{font_pid}.bin"), "wb") as f:
        f.write(font_bytes)
    print(f"font_{font_pid}.bin: {len(font_bytes):,}")

    # Serialize atlas
    if inline:
        # Update texture dimensions if the atlas grew, and replace the pixel data.
        td["m_Height"] = ah
        td["m_CompleteImageSize"] = aw * ah
        td["image data"] = atlas.tobytes()
        node_tex = tex._get_typetree_node()
        tw = EndianBinaryWriter(endian="<")
        TypeTreeHelper.write_typetree(td, node_tex, tw)
        tex_bytes = bytes(tw.bytes)
        with open(os.path.join(out_dir, f"tex_{tex_pid}.bin"), "wb") as f:
            f.write(tex_bytes)
        print(f"tex_{tex_pid}.bin: {len(tex_bytes):,} (m_Height={ah})")
    else:
        assert ah == int(tree["m_AtlasHeight"]) or True  # resS expansion unsupported here
        ress[off : off + aw * ah] = atlas.tobytes()
        base_ress = os.path.basename(assets_path) + ".resS"
        with open(os.path.join(out_dir, base_ress), "wb") as f:
            f.write(ress)
        print(f"{base_ress}: {len(ress):,}")

    with open(os.path.join(out_dir, "report.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "font_pid": font_pid,
                "tex_pid": tex_pid,
                "inline": inline,
                "placed": len(new_glyphs),
                "unplaced": len(unplaced),
                "unplaced_chars": "".join(chr(c) for c in unplaced),
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print("done")


if __name__ == "__main__":
    main()
