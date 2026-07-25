#!/usr/bin/env python3
"""
bake_fonts_174.py — Bake missing Traditional-Chinese glyphs into the 1.7.4
(Unity 6) NotoSansCJK TMP font asset.

Pipeline:
  1. Parse TMP_FontAsset (sharedassets1 pid 3644) via generated IL2CPP typetree.
  2. Compute TC codepoints used by the patched resources.assets minus those
     already baked in the atlas.
  3. Render each missing glyph as an SDF (freetype + scipy) matching the atlas
     convention (edge=128, spread=padding), pack into the atlas' existing free
     rects (bottom-up, Alpha8), and blit into the atlas pixel buffer (.resS).
  4. Append glyph + character table entries and update used/free glyph rects.
  5. Serialize the modified MonoBehaviour to raw bytes (TypeTreeHelper.write_typetree)
     and write the edited .resS. A separate C# AssetsTools.NET step swaps the
     object bytes into sharedassets1.assets (UnityPy cannot re-serialize Unity 6).

Outputs (into OUT_DIR):
  - pid3644.bin                     new MonoBehaviour bytes
  - sharedassets1.assets.resS       atlas-edited copy (same size)
  - bake_report.json                summary
"""

import json
import math
import os
import struct
import sys

import freetype
import numpy as np
import UnityPy
from PIL import Image
from scipy.ndimage import distance_transform_edt
from UnityPy.helpers import TypeTreeHelper
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
from UnityPy.helpers.TypeTreeNode import TypeTreeNode

TypeTreeHelper.read_typetree_boost = False

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GAME_ROOT = os.environ.get(
    "MOD_GAME_DIR", "/mnt/d/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector"
)
DATA = os.path.join(GAME_ROOT, "Warhammer 40K Battlesector_Data")

# Prefer a pristine snapshot (MOD_BACKUP_DIR) as the vanilla font source. This
# avoids the trap of reading a stale ".vortex_backup" left over from a previous
# game version. Falls back to the in-place game files if no snapshot is set.
_BACKUP = os.environ.get("MOD_BACKUP_DIR", "")


def _vanilla_src(rel_in_data: str, fallback: str) -> str:
    if _BACKUP:
        p = os.path.join(_BACKUP, "Warhammer 40K Battlesector_Data", rel_in_data)
        if os.path.isfile(p):
            return p
    return fallback


SA_VANILLA = _vanilla_src(
    "sharedassets1.assets", os.path.join(DATA, "sharedassets1.assets.vortex_backup")
)
RESS_VANILLA = _vanilla_src(
    "sharedassets1.assets.resS", os.path.join(DATA, "sharedassets1.assets.resS")
)
FONT_OTF = os.environ.get("MOD_FONT_OTF", os.path.join(REPO, ".copilot_workspace", "fonts", "NotoSansCJKjp-Regular.otf"))
RES_PATCHED = os.path.join(REPO, "translation", "zh-TW", "dist", "resources.assets")
OUT_DIR = os.path.join(REPO, ".copilot_workspace", "font_bake_out")

FONT_PID = 3644
ATLAS_W = ATLAS_H = 2048
POINT_SIZE = 17
PADDING = 9
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
    )


def generate_sdf(face, cp):
    """Return (sdf_uint8 [h+2p, w+2p] top-down, content_w, content_h, metrics) or (None,..)."""
    render_size = POINT_SIZE * OVERSAMPLE
    face.set_pixel_sizes(0, render_size)
    try:
        face.load_char(cp, 0x0006)  # FT_LOAD_RENDER | FT_LOAD_NO_HINTING
    except Exception:
        return None, 0, 0, None
    slot = face.glyph
    advance = slot.advance.x / 64.0 / OVERSAMPLE
    bearing_x = slot.bitmap_left / OVERSAMPLE
    bearing_y = slot.bitmap_top / OVERSAMPLE
    bmp = slot.bitmap
    bw, bh = bmp.width, bmp.rows
    metrics = {
        "m_HorizontalAdvance": round(advance),
        "m_HorizontalBearingX": bearing_x,
        "m_HorizontalBearingY": bearing_y,
        "m_Width": bw / OVERSAMPLE,
        "m_Height": bh / OVERSAMPLE,
    }
    if bw == 0 or bh == 0:
        return None, 0, 0, metrics

    hi = np.frombuffer(bytes(bmp.buffer), dtype=np.uint8).reshape(bh, bw)
    binary = hi > 127
    pad_hi = PADDING * OVERSAMPLE
    binary = np.pad(binary, pad_hi, mode="constant", constant_values=False)
    dist_in = distance_transform_edt(binary)
    dist_out = distance_transform_edt(~binary)
    signed = np.where(binary, dist_in, -dist_out)
    spread = PADDING * OVERSAMPLE
    sdf = np.clip(128.0 + signed * (128.0 / spread), 0.0, 255.0).astype(np.uint8)

    target_w = int(math.ceil(bw / OVERSAMPLE))
    target_h = int(math.ceil(bh / OVERSAMPLE))
    total_w = target_w + 2 * PADDING
    total_h = target_h + 2 * PADDING
    sdf_img = Image.fromarray(sdf, mode="L").resize((total_w, total_h), Image.LANCZOS)
    return np.array(sdf_img, dtype=np.uint8), target_w, target_h, metrics


class RectPacker:
    """Guillotine best-area-fit over a list of free rects (atlas pixel coords)."""

    def __init__(self, free_rects):
        self.free = [
            dict(x=r["m_X"], y=r["m_Y"], w=r["m_Width"], h=r["m_Height"]) for r in free_rects
        ]

    def place(self, bw, bh):
        best = None
        best_area = None
        for fr in self.free:
            if fr["w"] >= bw and fr["h"] >= bh:
                area = fr["w"] * fr["h"]
                if best_area is None or area < best_area:
                    best_area, best = area, fr
        if best is None:
            return None
        x, y = best["x"], best["y"]
        rx, ry, rw, rh = best["x"], best["y"], best["w"], best["h"]
        self.free.remove(best)
        right = dict(x=rx + bw, y=ry, w=rw - bw, h=bh)
        bottom = dict(x=rx, y=ry + bh, w=rw, h=rh - bh)
        if right["w"] > 0 and right["h"] > 0:
            self.free.append(right)
        if bottom["w"] > 0 and bottom["h"] > 0:
            self.free.append(bottom)
        return x, y

    def remaining(self):
        return [
            {"m_X": r["x"], "m_Y": r["y"], "m_Width": r["w"], "m_Height": r["h"]} for r in self.free
        ]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    gen = TypeTreeGenerator(UNITY_VERSION)
    gen.load_local_game(GAME_ROOT)
    base = gen.get_nodes("Unity.TextMeshPro", "TMPro.TMP_FontAsset")
    node = TypeTreeNode.from_list(
        [TypeTreeNode(b.m_Level, b.m_Type, b.m_Name, 0, 0, m_MetaFlag=b.m_MetaFlag) for b in base]
    )

    env = UnityPy.load(SA_VANILLA)
    obj = next(o for o in env.objects if o.path_id == FONT_PID)
    tree = obj.read_typetree(node, check_read=False)

    baked = {int(c["m_Unicode"]) for c in tree["m_CharacterTable"]}
    used_indices = {int(g["m_Index"]) for g in tree["m_GlyphTable"]}
    next_index = max(used_indices) + 1

    # Needed TC codepoints from patched resources.assets
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
                cp = ord(ch)
                if is_relevant(cp):
                    used.add(cp)
    missing = sorted(used - baked)
    print(f"Missing glyphs to bake: {len(missing)}")

    # Atlas pixel buffer from .resS (bottom-up, Alpha8)
    with open(RESS_VANILLA, "rb") as f:
        ress = bytearray(f.read())
    atlas = (
        np.frombuffer(bytes(ress[: ATLAS_W * ATLAS_H]), dtype=np.uint8)
        .reshape(ATLAS_H, ATLAS_W)
        .copy()
    )

    face = freetype.Face(FONT_OTF)

    # Pre-render to get sizes, then pack largest-first.
    rendered = []
    for cp in missing:
        sdf, cw, ch, metrics = generate_sdf(face, cp)
        if sdf is None:
            # zero-size (rare); still add a char entry mapping to a space-like glyph? skip glyph, skip char.
            continue
        rendered.append((cp, sdf, cw, ch, metrics))
    rendered.sort(key=lambda r: -(r[1].shape[0] * r[1].shape[1]))

    packer = RectPacker(tree["m_FreeGlyphRects"] or [])
    new_glyphs = []
    new_chars = []
    new_used_rects = []
    placed = 0
    unplaced = []
    for cp, sdf, cw, ch, metrics in rendered:
        ph, pw = sdf.shape  # padded footprint
        pos = packer.place(pw, ph)
        if pos is None:
            unplaced.append(cp)
            continue
        px, py = pos
        # blit flipped (top-down sdf -> bottom-up atlas)
        atlas[py : py + ph, px : px + pw] = np.flipud(sdf)
        # glyphRect = content box (exclude padding), Y from bottom
        gr = {"m_X": px + PADDING, "m_Y": py + PADDING, "m_Width": cw, "m_Height": ch}
        gi = next_index
        next_index += 1
        new_glyphs.append(
            {
                "m_Index": gi,
                "m_Metrics": {
                    "m_Width": metrics["m_Width"],
                    "m_Height": metrics["m_Height"],
                    "m_HorizontalBearingX": metrics["m_HorizontalBearingX"],
                    "m_HorizontalBearingY": metrics["m_HorizontalBearingY"],
                    "m_HorizontalAdvance": float(metrics["m_HorizontalAdvance"]),
                },
                "m_GlyphRect": gr,
                "m_Scale": 1.0,
                "m_AtlasIndex": 0,
                "m_ClassDefinitionType": 0,
            }
        )
        new_chars.append({"m_ElementType": 1, "m_Unicode": cp, "m_GlyphIndex": gi, "m_Scale": 1.0})
        new_used_rects.append({"m_X": px, "m_Y": py, "m_Width": pw, "m_Height": ph})
        placed += 1

    print(f"Placed: {placed}  Unplaced: {len(unplaced)}")

    # Update tables
    tree["m_GlyphTable"].extend(new_glyphs)
    tree["m_CharacterTable"].extend(new_chars)
    # TMP binary-searches these tables, so they MUST stay sorted:
    #   m_CharacterTable by m_Unicode, m_GlyphTable by m_Index.
    # Appended entries break the sort (our CJK unicodes are < some existing
    # entries), so re-sort both after extending.
    tree["m_CharacterTable"].sort(key=lambda c: int(c["m_Unicode"]))
    tree["m_GlyphTable"].sort(key=lambda g: int(g["m_Index"]))
    tree["m_UsedGlyphRects"] = (tree.get("m_UsedGlyphRects") or []) + new_used_rects
    tree["m_FreeGlyphRects"] = packer.remaining()

    # Serialize modified MonoBehaviour to bytes
    from UnityPy.streams import EndianBinaryWriter

    endian = "<"
    w = EndianBinaryWriter(endian=endian)
    TypeTreeHelper.write_typetree(tree, node, w)
    new_bytes = bytes(w.bytes)
    with open(os.path.join(OUT_DIR, "pid3644.bin"), "wb") as f:
        f.write(new_bytes)
    print(f"pid3644.bin: {len(new_bytes):,} bytes (was 6,271,524)")

    # Write edited .resS (atlas region replaced in place, same total size)
    ress[: ATLAS_W * ATLAS_H] = atlas.tobytes()
    out_ress = os.path.join(OUT_DIR, "sharedassets1.assets.resS")
    with open(out_ress, "wb") as f:
        f.write(ress)
    print(f".resS written: {len(ress):,} bytes")

    report = {
        "missing": len(missing),
        "placed": placed,
        "unplaced": len(unplaced),
        "unplaced_chars": "".join(chr(c) for c in unplaced),
        "new_glyphs": len(new_glyphs),
        "font_bytes": len(new_bytes),
    }
    with open(os.path.join(OUT_DIR, "bake_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("Report:", report)


if __name__ == "__main__":
    main()
