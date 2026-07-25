#!/usr/bin/env python3
"""
bake_startup_generated.py — Fix garbled TC description text (1.7.7).

Bakes the missing Traditional-Chinese glyphs directly into a STATIC TMP font
inside startup_assets_all.bundle and forces m_AtlasPopulationMode=0 (Static) so
TMP uses the pre-baked CharacterTable and never falls through to broken dynamic
glyph generation (which emits garbage glyph indices => the observed 川/屹/眉
garbling).

By default it targets BOTH fonts in the description fallback chain:
  - "Generated"   (pid -6634277187469610597)  static
  - "No Underlay" (pid  7178690147649604500)  dynamic in 1.7.7 -> forced static
Pass explicit pids as args to override:
    python3 tools/scripts/bake_startup_generated.py <pid> [<pid> ...]

This mirrors the proven pid 3644 bake (bake_fonts_174.py) but targets a bundle:
  - atlas is Alpha8 (SDF in the alpha channel), streamed inside the bundle
  - edited via UnityPy's Texture2D image API; whole bundle saved with
    env.file.save(packer="original")
  - CRC is NOT enforced for these local bundles, so catalog.bin is left untouched
    (see MOD_UPDATE_CATALOG below).

Env: MOD_GAME_DIR, MOD_DIST_DIR (defaults match the repo layout).
"""

import math
import os
import struct
import sys
import zlib

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
DIST_DIR = os.environ.get("MOD_DIST_DIR", os.path.join(REPO, "translation", "zh-TW", "dist"))
FONT_OTF = os.environ.get("MOD_FONT_OTF", os.path.join(REPO, ".copilot_workspace", "fonts", "NotoSansCJKjp-Regular.otf"))
RES_PATCHED = os.path.join(DIST_DIR, "resources.assets")

BUNDLE_DIST = os.path.join(DIST_DIR, "startup_assets_all.bundle")
CATALOG_DIST = os.path.join(DIST_DIR, "catalog.bin")

GENERATED_FONT_PID = -6634277187469610597
NO_UNDERLAY_FONT_PID = 7178690147649604500
DEFAULT_FONT_PIDS = [GENERATED_FONT_PID, NO_UNDERLAY_FONT_PID]
# Fonts that cannot fit all glyphs get this full-coverage static font as fallback.
FALLBACK_TARGET_PID = GENERATED_FONT_PID

OVERSAMPLE = 4
UNITY_VERSION = "6000.0.62f1"
BUNDLE_DATA_OFFSET = 160
CATALOG_CRC_OFFSET = 173069

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


def generate_sdf(face, cp, point_size, padding):
    """Return (sdf_uint8 [top-down], content_w, content_h, metrics) or (None,...)."""
    render_size = point_size * OVERSAMPLE
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
    """Guillotine best-area-fit over free rects (Unity bottom-up atlas coords)."""

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


def tc_used_codepoints():
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
    return used


def bake_one(env, byid, tmp_node, font_pid, all_used, face):
    """Bake missing codepoints into font `font_pid`, forcing Static. Returns count."""
    fobj = byid[font_pid]
    # UnityPy read-cache workaround: dummy save so later save_typetree sticks.
    fobj.save_typetree(fobj.read_typetree(tmp_node, check_read=False), tmp_node)
    tree = fobj.read_typetree(tmp_node, check_read=False)

    name = tree.get("m_Name", "")
    pop = int(tree.get("m_AtlasPopulationMode", 0))
    point_size = int(round(tree["m_FaceInfo"]["m_PointSize"]))
    padding = int(tree["m_AtlasPadding"])
    aw, ah = int(tree["m_AtlasWidth"]), int(tree["m_AtlasHeight"])
    tex_pid = (tree["m_AtlasTextures"] or [])[0]["m_PathID"]
    print(
        f"\n[{name}] pid={font_pid} pop={pop} pointSize={point_size} pad={padding} "
        f"atlas={aw}x{ah} texpid={tex_pid} chars={len(tree['m_CharacterTable'])} "
        f"free={len(tree.get('m_FreeGlyphRects') or [])}"
    )
    if pop != 0:
        print(f"  forcing Static (pop {pop} -> 0)")
        tree["m_AtlasPopulationMode"] = 0

    baked = {int(c["m_Unicode"]) for c in tree["m_CharacterTable"]}
    todo = sorted(set(all_used) - baked)
    print(f"  missing here: {len(todo)}")
    next_index = max(int(g["m_Index"]) for g in tree["m_GlyphTable"]) + 1

    tex = byid[tex_pid].read()
    rgba = np.array(tex.image)
    assert rgba.shape[:2] == (ah, aw), f"atlas {rgba.shape} != {ah}x{aw}"
    plane = rgba[:, :, 3].copy()

    rendered = []
    for cp in todo:
        sdf, cw, ch, metrics = generate_sdf(face, cp, point_size, padding)
        if sdf is None:
            continue
        rendered.append((cp, sdf, cw, ch, metrics))
    rendered.sort(key=lambda r: -(r[1].shape[0] * r[1].shape[1]))

    # Pass 1: compute placements. By default (MOD_EXPAND_ATLAS unset) glyphs are
    # only placed in the atlas's existing free space; any that don't fit stay
    # unplaced and are covered by the Generated fallback added below (TMP
    # multi-material fallback — no material changes needed). Set MOD_EXPAND_ATLAS=1
    # to instead grow the atlas in 2048 steps so the font holds ALL glyphs itself
    # (NOTE: growing the atlas also requires syncing the font MATERIAL's
    # _TextureHeight, which this script does NOT do — use only if the material is
    # handled separately).
    EXPAND = os.environ.get("MOD_EXPAND_ATLAS", "0") == "1"
    MAX_ATLAS_H = 8192
    packer = RectPacker(tree["m_FreeGlyphRects"] or [])
    cur_h = ah
    placements = []  # (cp, sdf, cw, ch, metrics, px, py_bu)
    unplaced = []
    for cp, sdf, cw, ch, metrics in rendered:
        ph, pw = sdf.shape
        pos = packer.place(pw, ph)
        if pos is None and EXPAND and cur_h + 2048 <= MAX_ATLAS_H:
            # Add a new free region at the top (bottom-up y in [cur_h, cur_h+2048)).
            packer.free.append(dict(x=0, y=cur_h, w=aw, h=2048))
            cur_h += 2048
            packer.free.sort(key=lambda r: -(r["w"] * r["h"]))
            pos = packer.place(pw, ph)
        if pos is None:
            unplaced.append(cp)
            continue
        placements.append((cp, sdf, cw, ch, metrics, pos[0], pos[1]))

    # Expand the pixel plane if the atlas grew. Top-down convention: existing
    # content stays at the BOTTOM (rows [cur_h-ah, cur_h)); the new free area is
    # the top rows [0, cur_h-ah). Bottom-up glyph coords are preserved.
    if cur_h != ah:
        new_plane = np.zeros((cur_h, aw), dtype=np.uint8)
        new_plane[cur_h - ah :, :] = plane
        plane = new_plane
        ah = cur_h
        tree["m_AtlasWidth"] = aw
        tree["m_AtlasHeight"] = ah

    # Pass 2: write pixels + glyph/char entries using the FINAL atlas height.
    new_glyphs, new_chars, new_used = [], [], []
    for cp, sdf, cw, ch, metrics, px, py_bu in placements:
        ph, pw = sdf.shape
        top = ah - py_bu - ph  # top-down row of the footprint
        plane[top : top + ph, px : px + pw] = sdf
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
                    "m_Y": py_bu + padding,
                    "m_Width": cw,
                    "m_Height": ch,
                },
                "m_Scale": 1.0,
                "m_AtlasIndex": 0,
                "m_ClassDefinitionType": 0,
            }
        )
        new_chars.append({"m_ElementType": 1, "m_Unicode": cp, "m_GlyphIndex": gi, "m_Scale": 1.0})
        new_used.append({"m_X": px, "m_Y": py_bu, "m_Width": pw, "m_Height": ph})
    print(f"  placed {len(new_glyphs)}  unplaced {len(unplaced)}  final_atlas={aw}x{ah}")

    tree["m_GlyphTable"].extend(new_glyphs)
    tree["m_CharacterTable"].extend(new_chars)
    tree["m_CharacterTable"].sort(key=lambda c: int(c["m_Unicode"]))
    tree["m_GlyphTable"].sort(key=lambda g: int(g["m_Index"]))
    tree["m_UsedGlyphRects"] = (tree.get("m_UsedGlyphRects") or []) + new_used
    tree["m_FreeGlyphRects"] = packer.remaining()

    # If this font could not fit every glyph in its own atlas (e.g. No Underlay's
    # atlas is full at pointSize 35), guarantee coverage by adding the
    # full-coverage static Generated font as a fallback. TMP will resolve any
    # glyph missing from THIS font via Generated (which has all TC glyphs).
    if font_pid != FALLBACK_TARGET_PID and (unplaced or todo):
        fb = tree.get("m_FallbackFontAssetTable") or []
        has = any(int(f.get("m_PathID", 0)) == FALLBACK_TARGET_PID for f in fb)
        if not has:
            fb.insert(0, {"m_FileID": 0, "m_PathID": FALLBACK_TARGET_PID})
            tree["m_FallbackFontAssetTable"] = fb
            print(f"  + added Generated (pid {FALLBACK_TARGET_PID}) as fallback")

    fobj.save_typetree(tree, tmp_node)

    if new_glyphs:
        out = np.zeros((ah, aw, 4), dtype=np.uint8)
        out[:, :, 3] = plane
        tex.image = Image.fromarray(out, mode="RGBA")
        tex.save()
    return len(new_glyphs)


def main():
    if not os.path.isfile(BUNDLE_DIST):
        print(f"ERROR: bundle not found: {BUNDLE_DIST}", file=sys.stderr)
        sys.exit(1)

    pids = [int(a) for a in sys.argv[1:]] or DEFAULT_FONT_PIDS

    gen = TypeTreeGenerator(UNITY_VERSION)
    gen.load_local_game(GAME_ROOT)
    base = gen.get_nodes("Unity.TextMeshPro", "TMPro.TMP_FontAsset")
    tmp_node = TypeTreeNode.from_list(
        [TypeTreeNode(b.m_Level, b.m_Type, b.m_Name, 0, 0, m_MetaFlag=b.m_MetaFlag) for b in base]
    )

    env = UnityPy.load(BUNDLE_DIST)
    byid = {o.path_id: o for o in env.objects}
    all_used = sorted(tc_used_codepoints())
    print(f"TC codepoints used: {len(all_used)}")
    face = freetype.Face(FONT_OTF)

    total = 0
    for pid in pids:
        if pid not in byid:
            print(f"WARNING: font pid {pid} not in bundle; skipping.", file=sys.stderr)
            continue
        total += bake_one(env, byid, tmp_node, pid, all_used, face)

    print(f"\nSaving bundle (total glyphs added: {total})...")
    env.file.dataflags = type(env.file.dataflags)(579)
    env.file._block_info_flags = 64
    bundle_bytes = env.file.save(packer="original")
    with open(BUNDLE_DIST, "wb") as f:
        f.write(bundle_bytes)
    print(f"Bundle saved: {len(bundle_bytes):,} bytes")

    # Addressables CRC handling.
    # NOTE (1.7.7): the game does NOT enforce the local bundle CRC — the proven
    # 1.7.4 deploy shipped the patched bundle WITHOUT any catalog change
    # ("Leave Addressables catalog files untouched"). Also, the hardcoded
    # CATALOG_CRC_OFFSET from the old pipeline is NOT valid for 1.7.7's catalog
    # (the stored value there is unrelated to the startup bundle). So by default
    # we do NOT touch catalog.bin. Set MOD_UPDATE_CATALOG=1 only if a future game
    # version is found to enforce the CRC AND the correct offset is verified.
    new_crc = zlib.crc32(bundle_bytes[BUNDLE_DATA_OFFSET:]) & 0xFFFFFFFF
    if os.environ.get("MOD_UPDATE_CATALOG", "0") == "1" and os.path.isfile(CATALOG_DIST):
        catalog = bytearray(open(CATALOG_DIST, "rb").read())
        old_crc = struct.unpack_from("<I", catalog, CATALOG_CRC_OFFSET)[0]
        struct.pack_into("<I", catalog, CATALOG_CRC_OFFSET, new_crc)
        with open(CATALOG_DIST, "wb") as f:
            f.write(catalog)
        print(f"catalog.bin CRC @0x{CATALOG_CRC_OFFSET:X}: 0x{old_crc:08X} -> 0x{new_crc:08X}")
    else:
        print(
            f"catalog.bin left UNTOUCHED (CRC not enforced for local bundles). "
            f"Patched bundle CRC=0x{new_crc:08X}."
        )


if __name__ == "__main__":
    main()
