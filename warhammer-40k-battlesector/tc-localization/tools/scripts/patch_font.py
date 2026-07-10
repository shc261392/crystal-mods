#!/usr/bin/env python3
"""
patch_font.py — Patch TMP font assets in the Addressables bundle for TC support.

Strategy (Attempt 4 — pre-bake):
  TMP does NOT dynamically generate glyphs when a Dynamic font is used as a
  *fallback* (only the primary font on a text component gets dynamic generation).

  The campaign/mode description text uses:
    futura No Underlay  →  [Generated, No Underlay, Roboto No Underlay]  (all in unknownassets)

  The Generated font has 3295 pre-baked chars (SC + 1246 TC).  Those 1246 TC
  chars render fine.  The remaining ~754 TC chars that are NOT in Generated fall
  through to No Underlay, which currently has 0 chars → □ boxes.

  Fix:
    1. Generated font: set pop=1, multi=1, src=local NotoSansCJK  (unchanged from before)
    2. No Underlay atlas: pre-bake the 754 missing TC chars using freetype-py SDF
    3. No Underlay font:  set pop=0 (Static), update char/glyph tables

  When futura looks up a missing TC char:
    → Generated: not found (no dynamic generation via fallback)
    → No Underlay: found in pre-baked table  →  renders ✓
"""

import hashlib
import math
import os
import struct
import sys
import tempfile
import zlib

import UnityPy

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
DIST_DIR = os.path.join(REPO_ROOT, "translation/zh-TW/dist")
PATCHED_DIR = os.path.join(REPO_ROOT, "translation/zh-TW/patched")

DEFAULT_GAME_DIR = "/mnt/d/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector"
GAME_DIR = os.environ.get("MOD_GAME_DIR", DEFAULT_GAME_DIR)
MOD_BACKUP_DIR = os.environ.get("MOD_BACKUP_DIR", os.path.join(GAME_DIR, ".zh-tw-mod-backup"))
SA_REL = os.path.join("Warhammer 40K Battlesector_Data", "StreamingAssets")

BUNDLE_CANDIDATES = [
    "startup_assets_all.bundle",
    "unknownassets_assets_all_12cf1b4aeb7c9355f8487758e37a43d2.bundle",
]


def _resolve_bundle_name() -> str:
    for candidate in BUNDLE_CANDIDATES:
        if os.path.isfile(os.path.join(DIST_DIR, candidate)):
            return candidate
        if os.path.isfile(os.path.join(MOD_BACKUP_DIR, SA_REL, candidate)):
            return candidate
        if os.path.isfile(os.path.join(GAME_DIR, SA_REL, candidate)):
            return candidate
    return BUNDLE_CANDIDATES[0]


BUNDLE_NAME = _resolve_bundle_name()
BUNDLE_DIST = os.path.join(DIST_DIR, BUNDLE_NAME)
CATALOG_DIST = os.path.join(DIST_DIR, "catalog.bin")
CATALOG_HASH_DIST = os.path.join(DIST_DIR, "catalog.hash")

BUNDLE_DATA_OFFSET = 160
CATALOG_CRC_OFFSET = 173069

# path_ids in unknownassets bundle
NOTO_FONT_OBJECT_PATH_ID  = -951123113223942216   # NotoSansCJKjp-Regular Font (binary)
GENERATED_FONT_PATH_ID    = -6634277187469610597   # Generated TMP font asset
NO_UNDERLAY_FONT_PATH_ID  =  7178690147649604500   # No Underlay TMP font asset
NO_UNDERLAY_ATLAS_PATH_ID =  4927299259637123988   # No Underlay atlas Texture2D
GEN_ATLAS_PATH_ID         = -4456131424548392549   # Generated atlas Texture2D (2048×2048 streaming)
ROBOTO_FONT_PATH_ID       =  6858071789788628647   # Roboto-Medium SDF - No Underlay TMP font

# TMP atlas / SDF parameters (read from m_FaceInfo / m_AtlasPadding of Generated font)
ATLAS_W   = 2048
ATLAS_H   = 2048
POINT_SIZE = 17          # m_PointSize from FaceInfo
PADDING    = 9           # m_AtlasPadding
OVERSAMPLE = 4           # oversample factor for SDF quality


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_noto_font_bytes(env) -> bytes:
    """Return the raw TTF/OTF bytes of the embedded NotoSansCJKjp-Regular Font."""
    for obj in env.objects:
        if obj.path_id == NOTO_FONT_OBJECT_PATH_ID:
            tt = obj.read_typetree()
            data = tt.get("m_FontData", b"")
            if data:
                return bytes(data)
    raise RuntimeError("NotoSansCJKjp Font object not found in bundle")


def _get_generated_chars(env) -> set:
    """Return the set of Unicode codepoints pre-baked in the Generated font."""
    for obj in env.objects:
        if obj.path_id == GENERATED_FONT_PATH_ID:
            tt = obj.read_typetree()
            return {int(e["m_Unicode"]) for e in tt.get("m_CharacterTable", [])}
    return set()


def _is_tc_font_relevant_char(cp: int) -> bool:
    """Return True if codepoint should be included in TC glyph coverage.

    We intentionally include CJK ideographs + common CJK punctuation/spacing
    blocks used by UI copy. Restricting to only U+3400..U+9FFF misses frequent
    full-width punctuation and symbols, causing tofu boxes in description text.
    """
    return (
        # CJK ideographs
        (0x3400 <= cp <= 0x4DBF) or      # CJK Ext A
        (0x4E00 <= cp <= 0x9FFF) or      # CJK Unified
        (0xF900 <= cp <= 0xFAFF) or      # CJK Compatibility Ideographs
        (0x20000 <= cp <= 0x2EBEF) or    # CJK Ext B..F / IICore ranges
        (0x2F800 <= cp <= 0x2FA1F) or    # CJK Compatibility Ideographs Supplement
        # CJK punctuation/symbol blocks commonly present in TC UI strings
        (0x3000 <= cp <= 0x303F) or      # CJK Symbols and Punctuation
        (0xFF00 <= cp <= 0xFFEF) or      # Halfwidth and Fullwidth Forms
        (0x3100 <= cp <= 0x312F) or      # Bopomofo
        (0x31A0 <= cp <= 0x31BF) or      # Bopomofo Extended
        (0x2000 <= cp <= 0x206F)         # General Punctuation (EN/EM dash, etc.)
    )


def _collect_relevant_chars_from_text(text: str, out: set) -> None:
    for ch in text:
        cp = ord(ch)
        if _is_tc_font_relevant_char(cp):
            out.add(cp)


def _get_tc_chars_needed() -> set:
    """Return all TC CJK codepoints present in patched text files AND in the
    patched resources.assets (which carries campaign/default text the sharedassets1
    patched/*.txt files do not cover)."""
    tc = set()
    for fname in ("missions.txt", "ui.txt", "units.txt", "barks.txt"):
        fpath = os.path.join(PATCHED_DIR, fname)
        if not os.path.exists(fpath):
            continue
        _collect_relevant_chars_from_text(open(fpath, encoding="utf-8").read(), tc)

    for assets_name in ("resources.assets", "sharedassets1.assets"):
        assets_path = os.path.join(DIST_DIR, assets_name)
        if not os.path.isfile(assets_path):
            continue
        try:
            assets_env = UnityPy.load(assets_path)
            for obj in assets_env.objects:
                if obj.type.name != "TextAsset":
                    continue
                ta = obj.read()
                s = ta.m_Script
                text = s.decode("utf-8", "replace") if isinstance(s, (bytes, bytearray)) else (s or "")
                _collect_relevant_chars_from_text(text, tc)
        except Exception as e:
            print(f"  WARN: scanning {assets_path} for TC chars failed: {e}", file=sys.stderr)
    return tc


def _generate_sdf(face, char_code: int, point_size: int, padding: int, oversample: int):
    """
    Generate a greyscale SDF image for one character.

    Returns (sdf_img, glyph_w, glyph_h, metrics) where:
      sdf_img  – 2D numpy uint8, shape (glyph_h+2*padding, glyph_w+2*padding),
                 in TOP-DOWN row order (flip before saving to Unity atlas).
      glyph_w / glyph_h – integer pixel dims of the content area (no padding).
      metrics  – dict with float keys: width, height, bearingX, bearingY, advance.

    Returns (None, 0, 0, metrics) for invisible / zero-size glyphs.
    """
    import numpy as np
    from scipy.ndimage import distance_transform_edt
    from PIL import Image

    render_size = point_size * oversample
    face.set_pixel_sizes(0, render_size)
    try:
        face.load_char(char_code, 0x0006)   # FT_LOAD_RENDER | FT_LOAD_NO_HINTING
    except Exception:
        return None, 0, 0, {"advance": 0.0, "bearingX": 0.0, "bearingY": 0.0,
                            "width": 0.0, "height": 0.0}

    slot = face.glyph
    advance  = slot.advance.x / 64.0 / oversample
    bearing_x = slot.bitmap_left / oversample
    bearing_y = slot.bitmap_top  / oversample

    bmp = slot.bitmap
    bw, bh = bmp.width, bmp.rows

    if bw == 0 or bh == 0:
        return None, 0, 0, {
            "advance": advance, "bearingX": bearing_x, "bearingY": bearing_y,
            "width": 0.0, "height": 0.0,
        }

    # High-res bitmap → binary mask, padded so the SDF gradient extends into
    # the padding region (otherwise outside pixels are hard 0 = no anti-aliasing).
    hi = np.frombuffer(bytes(bmp.buffer), dtype=np.uint8).reshape(bh, bw)
    binary_unpad = hi > 127
    pad_hi = padding * oversample
    binary = np.pad(binary_unpad, pad_hi, mode="constant", constant_values=False)

    # Euclidean signed distance field on the padded mask
    dist_in  = distance_transform_edt(binary)    # inside pixels → dist to nearest outside
    dist_out = distance_transform_edt(~binary)   # outside pixels → dist to nearest inside
    signed   = np.where(binary, dist_in, -dist_out)

    # Normalise to [0,255] with spread = padding * oversample
    spread = padding * oversample
    sdf_padded = np.clip(128.0 + signed * (128.0 / spread), 0.0, 255.0).astype(np.float32)

    # Target size in the atlas
    target_w = int(math.ceil(bw / oversample))
    target_h = int(math.ceil(bh / oversample))
    total_w  = target_w + 2 * padding
    total_h  = target_h + 2 * padding

    # Downsample to target resolution
    pil_img  = Image.fromarray(sdf_padded.astype(np.uint8), mode="L")
    pil_res  = pil_img.resize((total_w, total_h), Image.LANCZOS)
    sdf_out  = np.array(pil_res, dtype=np.uint8)

    metrics = {
        "advance":  advance,
        "bearingX": bearing_x,
        "bearingY": bearing_y,
        "width":    float(bw) / oversample,
        "height":   float(bh) / oversample,
    }
    return sdf_out, target_w, target_h, metrics


def _bake_chars_into_no_underlay(env, chars_to_bake: list, noto_bytes: bytes) -> tuple:
    """
    Pre-bake chars_to_bake into the No Underlay TMP font asset and its atlas.

    Returns (num_baked, baked_chars_list, baked_glyphs_list).
    baked_chars_list and baked_glyphs_list are the Character/Glyph dicts added.
    """
    import numpy as np
    import freetype

    if not chars_to_bake:
        print("  No Underlay: nothing to bake (all TC chars already in Generated).")
        return (0, [], [], b"")

    # Write font binary to a temp file (FreeType needs a file path)
    with tempfile.NamedTemporaryFile(suffix=".ttf", delete=False) as tmp:
        tmp.write(noto_bytes)
        font_path = tmp.name

    try:
        face = freetype.Face(font_path)

        # --- Render all glyphs and build the atlas ---
        atlas    = np.zeros((ATLAS_H, ATLAS_W), dtype=np.uint8)
        char_entries  = []
        glyph_entries = []
        used_rects    = []

        ax, ay, row_h = 0, 0, 0   # packer state (top-down Y)
        _used_gi = set()
        _seq_gi  = 1

        packed = 0
        for cp in chars_to_bake:
            # Allocate real NotoSansCJKjp glyph ID; fall back to sequential on collision/miss
            real_gi = face.get_char_index(cp)
            if real_gi == 0 or real_gi in _used_gi:
                while _seq_gi in _used_gi:
                    _seq_gi += 1
                real_gi = _seq_gi
            _used_gi.add(real_gi)
            glyph_idx = real_gi

            sdf, gw, gh, metrics = _generate_sdf(face, cp, POINT_SIZE, PADDING, OVERSAMPLE)

            if sdf is None or gw == 0:
                # Invisible / whitespace – add to char table with a zero-rect glyph
                char_entries.append({
                    "m_ElementType": 1,
                    "m_Unicode": cp,
                    "m_GlyphIndex": glyph_idx,
                    "m_Scale": 1.0,
                })
                glyph_entries.append({
                    "m_Index": glyph_idx,
                    "m_Metrics": {
                        "m_Width": 0.0, "m_Height": 0.0,
                        "m_HorizontalBearingX": 0.0, "m_HorizontalBearingY": 0.0,
                        "m_HorizontalAdvance": metrics["advance"],
                    },
                    "m_GlyphRect": {"m_X": 0, "m_Y": 0, "m_Width": 0, "m_Height": 0},
                    "m_Scale": 1.0, "m_AtlasIndex": 0, "m_ClassDefinitionType": 0,
                })
                continue

            full_w = gw + 2 * PADDING   # = sdf.shape[1]
            full_h = gh + 2 * PADDING   # = sdf.shape[0]

            # Shelf packing: advance to next row if needed
            if ax + full_w > ATLAS_W:
                ax   = 0
                ay  += row_h
                row_h = 0

            if ay + full_h > ATLAS_H:
                print(f"  WARNING: atlas full after {packed} chars – {len(chars_to_bake) - packed} skipped")
                break

            # Write SDF into atlas (top-down coordinate space)
            atlas[ay : ay + full_h, ax : ax + full_w] = sdf

            # Convert pack position to Unity's bottom-up Y convention
            # UsedGlyphRect covers the full slot (including padding), bottom-up.
            used_y_bu = ATLAS_H - (ay + full_h)
            used_rects.append({
                "m_X": ax, "m_Y": used_y_bu,
                "m_Width": full_w, "m_Height": full_h,
            })

            # GlyphRect stores the content area only (no padding), bottom-up.
            glyph_x_bu = ax + PADDING
            glyph_y_bu = used_y_bu + PADDING

            char_entries.append({
                "m_ElementType": 1,
                "m_Unicode": cp,
                "m_GlyphIndex": glyph_idx,
                "m_Scale": 1.0,
            })
            glyph_entries.append({
                "m_Index": glyph_idx,
                "m_Metrics": {
                    "m_Width":  metrics["width"],
                    "m_Height": metrics["height"],
                    "m_HorizontalBearingX": metrics["bearingX"],
                    "m_HorizontalBearingY": metrics["bearingY"],
                    "m_HorizontalAdvance":  metrics["advance"],
                },
                "m_GlyphRect": {
                    "m_X": glyph_x_bu, "m_Y": glyph_y_bu,
                    "m_Width": gw, "m_Height": gh,
                },
                "m_Scale": 1.0, "m_AtlasIndex": 0, "m_ClassDefinitionType": 0,
            })

            ax    += full_w
            row_h  = max(row_h, full_h)
            packed    += 1

        # Free-glyph rect: the unused portion of the atlas (below current rows)
        free_y_top  = ay + row_h   # first unused row in top-down space
        free_h_bu   = ATLAS_H - free_y_top  # height of free region in bottom-up
        free_rects  = (
            [{"m_X": 0, "m_Y": 0, "m_Width": ATLAS_W, "m_Height": free_h_bu}]
            if free_h_bu > 0 else []
        )

        # Flip atlas to Unity's bottom-up row order before saving
        atlas_bytes = np.flipud(atlas).tobytes()

        # --- Update No Underlay TMP font asset ---
        for obj in env.objects:
            if obj.path_id != NO_UNDERLAY_FONT_PATH_ID:
                continue
            tt = obj.read_typetree()
            tt["m_AtlasPopulationMode"]       = 0   # Static — use pre-baked data directly
            tt["m_IsMultiAtlasTexturesEnabled"] = 0
            tt["m_CharacterTable"]            = char_entries
            tt["m_GlyphTable"]                = glyph_entries
            tt["m_UsedGlyphRects"]            = used_rects
            tt["m_FreeGlyphRects"]            = free_rects
            tt["m_AtlasTextureIndex"]         = 0
            obj.save_typetree(tt)
            break

        # --- Update No Underlay atlas Texture2D ---
        for obj in env.objects:
            if obj.path_id != NO_UNDERLAY_ATLAS_PATH_ID:
                continue
            tt = obj.read_typetree()
            tt["image data"]          = atlas_bytes
            tt["m_Width"]             = ATLAS_W
            tt["m_Height"]            = ATLAS_H
            tt["m_TextureFormat"]     = 1       # Alpha8
            tt["m_IsReadable"]        = True    # MUST be True for fallback atlas compatibility
            tt["m_CompleteImageSize"] = ATLAS_W * ATLAS_H
            tt["m_MipCount"]          = 1
            tt["m_StreamData"]        = {"offset": 0, "size": 0, "path": ""}
            obj.save_typetree(tt)
            break

        print(f"  No Underlay: pre-baked {packed} TC chars ({len(char_entries)} total entries)")
        return (packed, char_entries, glyph_entries, atlas_bytes)

    finally:
        os.unlink(font_path)


def _inject_missing_chars_into_generated(env) -> int:
    """
    Attempt 5b: Copy the pre-baked chars from the No Underlay font into the
    Generated font, referencing the No Underlay atlas as a secondary atlas
    (m_AtlasIndex=1). ALSO sets m_AtlasTextureIndex=nu_atlas_index so TextCore
    treats atlas[1] as a valid pre-baked atlas (not just a future overflow slot).

    Returns 1 if anything was changed, 0 if already fully up-to-date.
    """
    # Read No Underlay font: get its pre-baked chars/glyphs
    nu_chars = []
    nu_glyphs = []
    for obj in env.objects:
        if obj.path_id == NO_UNDERLAY_FONT_PATH_ID:
            tt = obj.read_typetree()
            nu_chars  = tt.get("m_CharacterTable", [])
            nu_glyphs = tt.get("m_GlyphTable", [])
            break

    if not nu_chars:
        print("  Generated inject: No Underlay font has no chars, skipping.")
        return 0

    # Read Generated font
    gen_obj = None
    for obj in env.objects:
        if obj.path_id == GENERATED_FONT_PATH_ID:
            gen_obj = obj
            break

    if gen_obj is None:
        print("  Generated inject: Generated font not found, skipping.")
        return 0

    tt_gen = gen_obj.read_typetree()
    gen_char_set = {e["m_Unicode"] for e in tt_gen.get("m_CharacterTable", [])}
    gen_glyph_ids = {e["m_Index"] for e in tt_gen.get("m_GlyphTable", [])}

    # Determine / ensure the No Underlay atlas is the secondary atlas in Generated
    existing_atlases = [a.get("m_PathID", 0) for a in tt_gen.get("m_AtlasTextures", [])]
    if NO_UNDERLAY_ATLAS_PATH_ID in existing_atlases:
        nu_atlas_index = existing_atlases.index(NO_UNDERLAY_ATLAS_PATH_ID)
    else:
        nu_atlas_index = len(existing_atlases)
        tt_gen["m_AtlasTextures"] = tt_gen.get("m_AtlasTextures", []) + [
            {"m_FileID": 0, "m_PathID": NO_UNDERLAY_ATLAS_PATH_ID}
        ]

    # Attempt 5b: set m_AtlasTextureIndex to the highest valid atlas index.
    # Hypothesis: TextCore uses this field to know which atlases are pre-baked
    # and valid for lookup (atlases 0..m_AtlasTextureIndex are accepted).
    need_ati = tt_gen.get("m_AtlasTextureIndex", 0) != nu_atlas_index
    if need_ati:
        tt_gen["m_AtlasTextureIndex"] = nu_atlas_index

    # Check if chars need injecting
    to_inject = [c for c in nu_chars if c["m_Unicode"] not in gen_char_set]
    if not to_inject and not need_ati:
        print("  Generated inject: already complete (chars + m_AtlasTextureIndex), skipping.")
        return 0

    if not to_inject:
        # Only m_AtlasTextureIndex needed updating
        gen_obj.save_typetree(tt_gen)
        print(f"  Generated inject: set m_AtlasTextureIndex={nu_atlas_index} (chars already present)")
        return 1

    # Build a map from No Underlay glyph index → glyph entry
    nu_glyph_map = {g["m_Index"]: g for g in nu_glyphs}

    # Pick new glyph indices not conflicting with existing Generated glyphs
    next_idx = max(gen_glyph_ids) + 1 if gen_glyph_ids else 10000

    new_char_entries  = list(tt_gen.get("m_CharacterTable", []))
    new_glyph_entries = list(tt_gen.get("m_GlyphTable", []))

    injected = 0
    for ce in to_inject:
        cp       = ce["m_Unicode"]
        nu_gi    = ce["m_GlyphIndex"]
        nu_glyph = nu_glyph_map.get(nu_gi)
        if nu_glyph is None:
            continue

        new_gi = next_idx
        next_idx += 1

        new_char_entries.append({
            "m_ElementType": 1,
            "m_Unicode":     cp,
            "m_GlyphIndex":  new_gi,
            "m_Scale":       1.0,
        })
        new_glyph_entries.append({
            "m_Index":   new_gi,
            "m_Metrics": nu_glyph["m_Metrics"],
            "m_GlyphRect": nu_glyph["m_GlyphRect"],
            "m_Scale":       1.0,
            "m_AtlasIndex":  nu_atlas_index,
            "m_ClassDefinitionType": 0,
        })
        injected += 1

    tt_gen["m_CharacterTable"] = new_char_entries
    tt_gen["m_GlyphTable"]     = new_glyph_entries
    gen_obj.save_typetree(tt_gen)

    print(f"  Generated inject: added {injected} chars, m_AtlasTextureIndex={nu_atlas_index}")
    return 1


def _make_no_underlay_atlas_streaming(env, atlas_bytes_fresh=None) -> int:
    """
    Convert NoUnderlay atlas Texture2D from inline 'image data' to streaming
    storage (.resS) so Step 5g can read its pixels for atlas repack.

    `atlas_bytes_fresh` is the just-baked bottom-up Alpha8 pixel buffer returned
    by Step 2. We use it instead of reading `tt["image data"]` because UnityPy's
    typetree cache returns the pre-bake (original SC) atlas bytes after a save,
    not the freshly written ones.

    Returns 1 if changes were made, 0 if already streaming or no data to write.
    """
    RES_S_KEY        = "CAB-be8dbf1298107e31652b994c6db02e50.resS"
    CAB_ARCHIVE_PATH = ("archive:/CAB-be8dbf1298107e31652b994c6db02e50/"
                        "CAB-be8dbf1298107e31652b994c6db02e50.resS")
    from UnityPy.helpers.ResourceReader import EndianBinaryReader

    # ── 1. Read NoUnderlay atlas Texture2D ───────────────────────────────────
    nu_atlas_obj = None
    for obj in env.objects:
        if obj.path_id == NO_UNDERLAY_ATLAS_PATH_ID:
            nu_atlas_obj = obj
            break
    if nu_atlas_obj is None:
        print("  Streaming 5e: NoUnderlay atlas object not found — skipping.")
        return 0

    tt     = nu_atlas_obj.read_typetree()
    stream = tt.get("m_StreamData", {})

    # Idempotency: already using streaming from our .resS?
    if stream.get("size", 0) > 0 and "resS" in stream.get("path", ""):
        print(f"  Streaming 5e: NoUnderlay atlas already streaming at offset "
              f"{stream['offset']:,} — skipping.")
        return 0

    inline_data = bytes(atlas_bytes_fresh) if atlas_bytes_fresh else bytes(tt.get("image data", b""))
    if not inline_data:
        print("  Streaming 5e: NoUnderlay atlas has no inline image data — skipping.")
        return 0

    # ── 2. Read current .resS ────────────────────────────────────────────────
    res_s_reader = env.file.files.get(RES_S_KEY)
    if res_s_reader is None:
        print("  Streaming 5e: .resS not in bundle files — skipping.")
        return 0

    original_flags = getattr(res_s_reader, "flags", 0)
    res_s_reader.Position = 0
    res_s_data = bytearray(res_s_reader.read())

    # ── 3. Append NoUnderlay atlas pixels at end of .resS ────────────────────
    new_offset = len(res_s_data)
    res_s_data.extend(inline_data)

    # ── 4. Update NoUnderlay atlas Texture2D to use streaming ────────────────
    tt["image data"]          = b""
    tt["m_CompleteImageSize"] = len(inline_data)
    tt["m_StreamData"] = {
        "offset": new_offset,
        "size":   len(inline_data),
        "path":   CAB_ARCHIVE_PATH,
    }
    nu_atlas_obj.save_typetree(tt)

    # ── 5. Write extended .resS back into bundle ──────────────────────────────
    new_reader        = EndianBinaryReader(bytearray(res_s_data))
    new_reader.flags  = original_flags
    env.file.files[RES_S_KEY] = new_reader

    print(f"  Streaming 5e: NoUnderlay atlas converted — appended "
          f"{len(inline_data):,} bytes at .resS offset {new_offset:,}")
    return 1



    """
    Attempt 5d: Copy the 754 missing TC glyph bitmaps directly into the free
    space of the Generated atlas (.resS streaming texture) and register the new
    glyphs in the Generated font's char/glyph tables at m_AtlasIndex=0.

    This is the definitive approach: only m_AtlasIndex=0 in the streaming atlas
    is confirmed to render correctly in this Unity 6 / IL2CPP title.

    Returns 1 if anything was changed, 0 if already up-to-date.
    """
    import io
    import numpy as np
    from UnityPy.helpers.ResourceReader import EndianBinaryReader

    PAD          = PADDING
    RES_S_KEY    = "CAB-be8dbf1298107e31652b994c6db02e50.resS"
    GEN_OFFSET   = 65244496
    GEN_SIZE     = 4194304    # 2048 × 2048 Alpha8

    # ── 1. Read .resS bytes ──────────────────────────────────────────────────
    res_s_reader = env.file.files.get(RES_S_KEY)
    if res_s_reader is None:
        print("  Composite 5d: .resS not found in bundle files — skipping.")
        return 0

    original_flags = getattr(res_s_reader, "flags", 0)
    res_s_reader.Position = 0
    res_s_data = bytearray(res_s_reader.read())

    # 1D numpy view of the Generated atlas slice (writable copy)
    gen_np = np.frombuffer(
        res_s_data[GEN_OFFSET : GEN_OFFSET + GEN_SIZE], dtype=np.uint8
    ).copy()

    # ── 2. Read NoUnderlay inline atlas & font ───────────────────────────────
    nu_atlas_bytes = None
    nu_chars       = []
    nu_glyphs_map  = {}
    for obj in env.objects:
        if obj.path_id == NO_UNDERLAY_ATLAS_PATH_ID:
            tt = obj.read_typetree()
            nu_atlas_bytes = bytes(tt.get("image data", b""))
        elif obj.path_id == NO_UNDERLAY_FONT_PATH_ID:
            tt = obj.read_typetree()
            nu_chars      = tt.get("m_CharacterTable", [])
            nu_glyphs_map = {g["m_Index"]: g for g in tt.get("m_GlyphTable", [])}

    if not nu_atlas_bytes:
        print("  Composite 5d: NoUnderlay atlas has no inline image data — skipping.")
        return 0
    if not nu_chars:
        print("  Composite 5d: NoUnderlay font has no chars — skipping.")
        return 0

    nu_np = np.frombuffer(nu_atlas_bytes, dtype=np.uint8)

    # ── 3. Read Generated font ───────────────────────────────────────────────
    gen_font_obj = None
    for obj in env.objects:
        if obj.path_id == GENERATED_FONT_PATH_ID:
            gen_font_obj = obj
            break
    if gen_font_obj is None:
        print("  Composite 5d: Generated font not found — skipping.")
        return 0

    gen_tt       = gen_font_obj.read_typetree()
    gen_char_set = {e["m_Unicode"] for e in gen_tt.get("m_CharacterTable", [])}
    gen_glyph_ids = {e["m_Index"] for e in gen_tt.get("m_GlyphTable", [])}

    # ── 4. Build occupancy map (bottom-up convention, same as Atlas bytes) ───
    # occupied[y, x] = True  →  that pixel is part of a glyph slot (content + pad)
    occupied = np.zeros((ATLAS_H, ATLAS_W), dtype=bool)
    for g in gen_tt.get("m_GlyphTable", []):
        gr = g["m_GlyphRect"]
        x, y, w, h = gr["m_X"], gr["m_Y"], gr["m_Width"], gr["m_Height"]
        if w == 0 or h == 0:
            continue
        y0 = max(0, y - PAD);  y1 = min(ATLAS_H, y + h + PAD)
        x0 = max(0, x - PAD);  x1 = min(ATLAS_W, x + w + PAD)
        occupied[y0:y1, x0:x1] = True

    # ── 5. Determine which chars still need injection ────────────────────────
    to_inject = [c for c in nu_chars if c["m_Unicode"] not in gen_char_set]
    if not to_inject:
        print("  Composite 5d: all chars already in Generated — nothing to inject.")
        return 0

    # ── 6. Shelf-pack glyphs into free space ─────────────────────────────────
    next_gi    = max(gen_glyph_ids) + 1 if gen_glyph_ids else 10000
    new_chars  = list(gen_tt.get("m_CharacterTable", []))
    new_glyphs = list(gen_tt.get("m_GlyphTable",     []))

    scan_x  = 0
    scan_y  = 0
    shelf_h = 0
    placed  = 0
    skipped = 0

    for ce in to_inject:
        cp    = ce["m_Unicode"]
        nu_gi = ce["m_GlyphIndex"]
        nu_g  = nu_glyphs_map.get(nu_gi)
        if nu_g is None:
            skipped += 1
            continue

        gr         = nu_g["m_GlyphRect"]
        gw, gh     = gr["m_Width"], gr["m_Height"]
        nu_gx, nu_gy = gr["m_X"], gr["m_Y"]

        if gw == 0 or gh == 0:
            # Invisible / whitespace — register with zero rect, no pixel copy
            new_chars.append({
                "m_ElementType": 1, "m_Unicode": cp,
                "m_GlyphIndex": next_gi, "m_Scale": 1.0,
            })
            new_glyphs.append({
                "m_Index": next_gi,
                "m_Metrics":   nu_g["m_Metrics"],
                "m_GlyphRect": {"m_X": 0, "m_Y": 0, "m_Width": 0, "m_Height": 0},
                "m_Scale": 1.0, "m_AtlasIndex": 0, "m_ClassDefinitionType": 0,
            })
            next_gi += 1
            placed  += 1
            continue

        slot_w = gw + 2 * PAD
        slot_h = gh + 2 * PAD

        found = False
        while not found:
            # End of current row → start a new shelf
            if scan_x + slot_w > ATLAS_W:
                scan_y += shelf_h if shelf_h else slot_h
                scan_x  = 0
                shelf_h = 0

            if scan_y + slot_h > ATLAS_H:
                print(f"  Composite 5d WARNING: atlas full — placed {placed}, "
                      f"skipped U+{cp:04X} and {len(to_inject) - placed - skipped - 1} more")
                skipped = len(to_inject) - placed   # mark rest as skipped
                break

            # Check if the candidate slot is entirely free
            region = occupied[scan_y : scan_y + slot_h, scan_x : scan_x + slot_w]
            if not np.any(region):
                # ── Copy pixels (slot includes padding) ──
                nu_sx = nu_gx - PAD   # source slot left edge in NoUnderlay atlas
                nu_sy = nu_gy - PAD   # source slot bottom edge (bottom-up)
                for dy in range(slot_h):
                    src_row = nu_sy + dy
                    dst_row = scan_y + dy
                    if 0 <= src_row < ATLAS_H:
                        src_off = src_row * ATLAS_W + nu_sx
                        dst_off = dst_row * ATLAS_W + scan_x
                        gen_np[dst_off : dst_off + slot_w] = \
                            nu_np[src_off : src_off + slot_w]

                # Mark slot as occupied
                occupied[scan_y : scan_y + slot_h, scan_x : scan_x + slot_w] = True

                # Register glyph (content rect, no padding)
                new_gx = scan_x + PAD
                new_gy = scan_y + PAD
                new_chars.append({
                    "m_ElementType": 1, "m_Unicode": cp,
                    "m_GlyphIndex": next_gi, "m_Scale": 1.0,
                })
                new_glyphs.append({
                    "m_Index": next_gi,
                    "m_Metrics":   nu_g["m_Metrics"],
                    "m_GlyphRect": {
                        "m_X": new_gx, "m_Y": new_gy,
                        "m_Width": gw,  "m_Height": gh,
                    },
                    "m_Scale": 1.0, "m_AtlasIndex": 0, "m_ClassDefinitionType": 0,
                })
                next_gi += 1
                placed  += 1
                shelf_h  = max(shelf_h, slot_h)
                scan_x  += slot_w
                found    = True
            else:
                # Skip past the rightmost conflicting column in this row band
                col_any  = np.any(region, axis=0)
                last_occ = int(np.where(col_any)[0][-1])
                scan_x  += last_occ + 1

    if placed == 0:
        print("  Composite 5d: no glyphs placed — aborting.")
        return 0

    # ── 7. Write modified atlas bytes back into .resS ────────────────────────
    res_s_data[GEN_OFFSET : GEN_OFFSET + GEN_SIZE] = gen_np.tobytes()

    new_reader        = EndianBinaryReader(bytearray(res_s_data))
    new_reader.flags  = original_flags
    env.file.files[RES_S_KEY] = new_reader

    # ── 8. Update Generated font char/glyph tables ──────────────────────────
    # CRITICAL: Sort CharacterTable by Unicode value for binary search lookup
    gen_tt["m_CharacterTable"] = sorted(new_chars, key=lambda c: c.get("m_Unicode", 0))
    gen_tt["m_GlyphTable"]     = new_glyphs
    gen_font_obj.save_typetree(gen_tt)

    print(f"  Composite 5d: {placed}/{len(to_inject)} glyphs packed into Generated atlas (.resS)")
    return 1


def _clean_generated_secondary_atlas(env) -> int:
    """
    Attempt 5c: Remove the 754 injected chars (m_AtlasIndex > 0) from Generated
    and strip the No Underlay atlas reference.

    With Generated left as a clean Static font (3291 original chars at atlas[0]
    only), TextCore returns "not found" for the 754 missing CJK chars, causing
    TMP to continue down the fallback chain and reach NoUnderlay (fallback[1]),
    which has all 754 chars pre-baked at atlas[0].

    This is different from Attempt 4a/4b (where Generated was Dynamic): a Static
    font simply says "not here" whereas Dynamic was consuming the requests by
    attempting on-the-fly generation, then silently failing without propagating.

    Returns 1 if changes were made, 0 if already clean.
    """
    gen_obj = None
    for obj in env.objects:
        if obj.path_id == GENERATED_FONT_PATH_ID:
            gen_obj = obj
            break
    if gen_obj is None:
        print("  Clean Generated: font not found, skipping.")
        return 0

    tt_gen = gen_obj.read_typetree()
    glyphs = tt_gen.get("m_GlyphTable", [])
    chars  = tt_gen.get("m_CharacterTable", [])
    atlases = tt_gen.get("m_AtlasTextures", [])

    # Identify injected glyph indices (those referencing atlas[1])
    injected_glyph_ids = {g["m_Index"] for g in glyphs if g.get("m_AtlasIndex", 0) > 0}

    if not injected_glyph_ids:
        # Check whether the secondary atlas ref also needs removing
        if NO_UNDERLAY_ATLAS_PATH_ID not in [a.get("m_PathID", 0) for a in atlases]:
            print("  Clean Generated: already clean (no injected chars, no secondary atlas).")
            return 0

    new_glyphs  = [g for g in glyphs if g["m_Index"] not in injected_glyph_ids]
    new_chars   = [c for c in chars  if c.get("m_GlyphIndex", 0) not in injected_glyph_ids]
    new_atlases = [a for a in atlases if a.get("m_PathID", 0) != NO_UNDERLAY_ATLAS_PATH_ID]

    removed_chars  = len(chars)  - len(new_chars)
    removed_glyphs = len(glyphs) - len(new_glyphs)
    removed_atlases = len(atlases) - len(new_atlases)

    tt_gen["m_CharacterTable"]          = new_chars
    tt_gen["m_GlyphTable"]              = new_glyphs
    tt_gen["m_AtlasTextures"]           = new_atlases
    tt_gen["m_AtlasTextureIndex"]       = 0
    gen_obj.save_typetree(tt_gen)

    print(f"  Clean Generated: removed {removed_chars} chars, {removed_glyphs} glyphs, "
          f"{removed_atlases} atlas ref(s). Now: {len(new_chars)} chars at atlas[0] only.")
    return 1


def _repack_all_glyphs_into_new_atlas(env, nu_chars_fresh=None, nu_glyphs_fresh=None) -> int:
    """
    Attempt 5g: Extract ALL glyph bitmaps from the Generated font (atlas[0] from
    the Generated streaming atlas, atlas[1] from the NoUnderlay streaming atlas)
    plus any NoUnderlay chars not yet in Generated, then pack them all into a
    single new 4096×2048 streaming atlas placed exclusively at atlas[0].

    `nu_chars_fresh`/`nu_glyphs_fresh` are the in-memory NoUnderlay tables as
    produced by Step 2's bake; passing them avoids reading NoUnderlay's stale
    typetree (UnityPy returns the pre-bake cached version after save).

    Root cause of all prior failures (5b/5c/5e/5f):
      Unity 6 IL2CPP TMP only renders glyphs from atlas[0] because that is the
      only atlas with a pre-created Material.  atlas[1] entries (even streaming,
      even with m_IsMultiAtlasTexturesEnabled=1) are silently ignored at render
      time.  The fallback chain beyond Generated (e.g. NoUnderlay as fallback[1])
      is also never reached for chars that TMP considers "handled" by Generated.

    This function creates a clean single-atlas font where every char lives at
    atlas[0] — the only confirmed-working render path in this title.

    Returns 1 if changed, 0 if already repacked (idempotent).
    """
    import numpy as np
    from UnityPy.helpers.ResourceReader import EndianBinaryReader

    RES_S_KEY  = "CAB-be8dbf1298107e31652b994c6db02e50.resS"
    CAB_PATH   = ("archive:/CAB-be8dbf1298107e31652b994c6db02e50/"
                  "CAB-be8dbf1298107e31652b994c6db02e50.resS")
    GEN_OFFSET = 65244496
    GEN_SIZE   = ATLAS_W * ATLAS_H        # 4 194 304 (2048×2048 Alpha8)
    NU_OFFSET  = 346746656                # appended by step 5e
    NU_SIZE    = ATLAS_W * ATLAS_H
    NEW_W      = 4096
    NEW_H      = 2048
    PAD        = PADDING

    # ── 1. Locate required objects ────────────────────────────────────────────
    gen_font_obj = gen_atlas_obj = nu_font_obj = None
    for obj in env.objects:
        if   obj.path_id == GENERATED_FONT_PATH_ID:   gen_font_obj  = obj
        elif obj.path_id == GEN_ATLAS_PATH_ID:         gen_atlas_obj = obj
        elif obj.path_id == NO_UNDERLAY_FONT_PATH_ID:  nu_font_obj   = obj

    if not all([gen_font_obj, gen_atlas_obj, nu_font_obj]):
        print("  5g: Required objects missing — skipping.")
        return 0

    # ── 2. Idempotency: already repacked? ─────────────────────────────────────
    gen_atlas_tt = gen_atlas_obj.read_typetree()
    if gen_atlas_tt.get("m_Width") == NEW_W and gen_atlas_tt.get("m_Height") == NEW_H:
        print(f"  5g: Generated atlas already {NEW_W}×{NEW_H} — skipping.")
        return 0

    # ── 3. Load .resS and extract atlas pixel arrays ──────────────────────────
    res_s_reader = env.file.files.get(RES_S_KEY)
    if res_s_reader is None:
        print("  5g: .resS not in bundle files — skipping.")
        return 0

    orig_flags = getattr(res_s_reader, "flags", 0)
    res_s_reader.Position = 0
    res_s_bytes = bytearray(res_s_reader.read())

    if len(res_s_bytes) < NU_OFFSET + NU_SIZE:
        print(f"  5g: .resS too short ({len(res_s_bytes):,} bytes) — "
              "NoUnderlay atlas not appended yet (step 5e must run first).")
        return 0

    # Both atlases are stored in Unity bottom-up row order:
    #   arr[y, x]  ↔  GlyphRect position (x, y)  (y=0 = bottom row)
    gen_img = np.frombuffer(
        bytes(res_s_bytes[GEN_OFFSET : GEN_OFFSET + GEN_SIZE]),
        dtype=np.uint8).reshape(ATLAS_H, ATLAS_W)
    nu_img  = np.frombuffer(
        bytes(res_s_bytes[NU_OFFSET  : NU_OFFSET  + NU_SIZE]),
        dtype=np.uint8).reshape(ATLAS_H, ATLAS_W)

    # ── 4. Read glyph/char tables ─────────────────────────────────────────────
    gen_tt = gen_font_obj.read_typetree()
    nu_tt  = nu_font_obj.read_typetree()

    gen_glyphs   = gen_tt.get("m_GlyphTable", [])
    gen_chars    = gen_tt.get("m_CharacterTable", [])
    gen_char_set = {c["m_Unicode"] for c in gen_chars}

    # Prefer caller-provided in-memory NoUnderlay tables (Step 2 just baked
    # them); nu_tt as returned by read_typetree() is the pre-bake cached snapshot.
    nu_chars_use  = nu_chars_fresh  if nu_chars_fresh  is not None else nu_tt.get("m_CharacterTable", [])
    nu_glyphs_use = nu_glyphs_fresh if nu_glyphs_fresh is not None else nu_tt.get("m_GlyphTable", [])

    nu_glyph_map = {g["m_Index"]: g for g in nu_glyphs_use}
    nu_char_map  = {c["m_Unicode"]: c for c in nu_chars_use}

    # ── 5. Shelf-pack into new NEW_W×NEW_H bottom-up atlas ───────────────────
    new_img = np.zeros((NEW_H, NEW_W), dtype=np.uint8)
    ax, ay, row_h = 0, 0, 0
    glyph_new_rect = {}   # original glyph index → new GlyphRect dict

    def pack_one(gi, src_img, src_x, src_y, src_w, src_h):
        nonlocal ax, ay, row_h
        if src_w == 0 or src_h == 0:
            glyph_new_rect[gi] = {"m_X": 0, "m_Y": 0, "m_Width": 0, "m_Height": 0}
            return True
        slot_w = src_w + 2 * PAD
        slot_h = src_h + 2 * PAD
        if ax + slot_w > NEW_W:
            ay += row_h;  ax = 0;  row_h = 0
        if ay + slot_h > NEW_H:
            return False  # atlas full
        # Read with padding clamped to source bounds
        sy0 = max(0, src_y - PAD);  sy1 = min(ATLAS_H, src_y + src_h + PAD)
        sx0 = max(0, src_x - PAD);  sx1 = min(ATLAS_W, src_x + src_w + PAD)
        region = src_img[sy0:sy1, sx0:sx1]
        dy = PAD - (src_y - sy0)
        dx = PAD - (src_x - sx0)
        new_img[ay + dy : ay + dy + region.shape[0],
                ax + dx : ax + dx + region.shape[1]] = region
        glyph_new_rect[gi] = {
            "m_X": ax + PAD, "m_Y": ay + PAD,
            "m_Width": src_w, "m_Height": src_h,
        }
        ax += slot_w
        row_h = max(row_h, slot_h)
        return True

    # Pack existing Generated glyphs:
    #   atlas[0] → pixels live in gen_img (Generated streaming atlas)
    #   atlas[1] → pixels live in nu_img  (NoUnderlay streaming atlas, appended by 5e)
    for g in gen_glyphs:
        gr  = g["m_GlyphRect"]
        src = gen_img if g.get("m_AtlasIndex", 0) == 0 else nu_img
        if not pack_one(g["m_Index"], src,
                        gr["m_X"], gr["m_Y"], gr["m_Width"], gr["m_Height"]):
            print(f"  5g ERROR: atlas full at existing glyph idx={g['m_Index']}")
            return 0

    # Pack any NoUnderlay chars not yet in Generated (should be 0 if 5f ran,
    # but handled here for robustness / running 5g without 5f)
    max_idx  = max((g["m_Index"] for g in gen_glyphs), default=0)
    next_idx = max_idx + 1
    new_char_entries  = []
    new_glyph_entries = []

    # Look up real font glyph IDs for new chars: TextCore validates m_GlyphIndex
    # against m_SourceFontFile at load time and silently rejects mismatches.
    # NoUnderlay's m_GlyphIndex values are sequential (1, 2, 3...) and do not
    # match the font binary's real IDs.
    import io as _io
    import freetype as _freetype
    _ft_face = None
    for _o in env.objects:
        if _o.path_id == NOTO_FONT_OBJECT_PATH_ID:
            _fo = _o.read()
            _ft_face = _freetype.Face(_io.BytesIO(bytes(_fo.m_FontData)))
            break
    if _ft_face is None:
        print("  5g: NotoSansCJK font binary not found — cannot assign real glyph IDs.")
        return 0
    _orig_glyph_ids = {g["m_Index"] for g in gen_glyphs}
    _used_real_ids  = set(_orig_glyph_ids)

    for unicode_val, ce in sorted(nu_char_map.items()):
        if unicode_val in gen_char_set:
            continue
        nu_gi = ce.get("m_GlyphIndex", 0)
        nu_g  = nu_glyph_map.get(nu_gi)
        if nu_g is None:
            continue
        # Resolve real font glyph ID; fall back to next_idx if not in font.
        real_gi = _ft_face.get_char_index(unicode_val)
        if real_gi == 0 or real_gi in _used_real_ids:
            real_gi = next_idx
            next_idx += 1
        _used_real_ids.add(real_gi)
        gr = nu_g["m_GlyphRect"]
        gi = real_gi
        if not pack_one(gi, nu_img,
                        gr["m_X"], gr["m_Y"], gr["m_Width"], gr["m_Height"]):
            print(f"  5g ERROR: atlas full at new char U+{unicode_val:04X}")
            return 0
        new_char_entries.append({
            "m_ElementType": 1,
            "m_Unicode":     unicode_val,
            "m_GlyphIndex":  gi,
            "m_Scale":       ce.get("m_Scale", 1.0),
        })
        new_glyph_entries.append({
            "m_Index":               gi,
            "m_Metrics":             dict(nu_g["m_Metrics"]),
            "m_GlyphRect":           glyph_new_rect[gi],
            "m_Scale":               nu_g.get("m_Scale", 1.0),
            "m_AtlasIndex":          0,
            "m_ClassDefinitionType": 0,
        })

    # ── 6. Append new atlas to .resS ──────────────────────────────────────────
    # new_img is already in bottom-up row order — no flipud needed
    new_offset      = len(res_s_bytes)
    new_atlas_bytes = new_img.tobytes()
    res_s_bytes.extend(new_atlas_bytes)

    # ── 7. Update Generated atlas Texture2D (pid=GEN_ATLAS_PATH_ID) ──────────
    gen_atlas_tt["m_Width"]             = NEW_W
    gen_atlas_tt["m_Height"]            = NEW_H
    gen_atlas_tt["m_CompleteImageSize"] = NEW_W * NEW_H
    gen_atlas_tt["image data"]          = b""
    gen_atlas_tt["m_StreamData"]        = {
        "offset": new_offset,
        "size":   NEW_W * NEW_H,
        "path":   CAB_PATH,
    }
    gen_atlas_obj.save_typetree(gen_atlas_tt)

    # ── 8. Update Generated font (pid=GENERATED_FONT_PATH_ID) ────────────────
    # Rebuild GlyphTable: all existing glyphs with updated GlyphRects at atlas[0]
    # CRITICAL: Assign sequential indices (0, 1, 2, ...) to all glyphs.
    # mode=0 (Static) bypasses TMP's GID validation so sequential IDs are safe.
    # DO NOT use real NotoSansCJKjp GIDs here: with mode=1 + GUID, TMP validates
    # each m_GlyphIndex against the font binary — sequential IDs fail (177 errors).
    # With mode=0, sequential IDs work fine and keep the table compact (118 errors).
    old_to_new_glyph_idx = {}  # map old glyph index → new sequential index
    updated_glyphs = []
    seq_idx = 0

    for g in gen_glyphs:
        old_gi = g["m_Index"]
        ng = dict(g)
        ng["m_Index"]      = seq_idx
        ng["m_GlyphRect"]  = glyph_new_rect[old_gi]
        ng["m_AtlasIndex"] = 0
        old_to_new_glyph_idx[old_gi] = seq_idx
        updated_glyphs.append(ng)
        seq_idx += 1

    # Update new_glyph_entries indices too and map old→new for new char lookup
    for entry in new_glyph_entries:
        old_gi = entry["m_Index"]  # currently has real font glyph ID
        entry["m_Index"] = seq_idx
        old_to_new_glyph_idx[old_gi] = seq_idx  # map for use in char table
        seq_idx += 1
    updated_glyphs.extend(new_glyph_entries)

    # CharacterTable: update all glyph indices to new sequential values
    updated_chars = []
    for c in gen_chars:
        old_gi = c.get("m_GlyphIndex", -1)
        if old_gi in old_to_new_glyph_idx:
            nc = dict(c)
            nc["m_GlyphIndex"] = old_to_new_glyph_idx[old_gi]
            updated_chars.append(nc)

    # Fix new character entries: update their glyph indices to new sequential values
    for entry in new_char_entries:
        old_gi = entry.get("m_GlyphIndex", -1)
        if old_gi in old_to_new_glyph_idx:
            entry["m_GlyphIndex"] = old_to_new_glyph_idx[old_gi]
    
    # Add new character entries
    updated_chars.extend(new_char_entries)
    # TMP uses binary search on m_CharacterTable sorted by m_Unicode — must sort!
    updated_chars.sort(key=lambda c: c["m_Unicode"])

    # Shelf state after packing
    last_row_top = ay + row_h
    free_h       = NEW_H - last_row_top

    gen_tt["m_GlyphTable"]                = updated_glyphs
    gen_tt["m_CharacterTable"]            = updated_chars
    gen_tt["m_AtlasTextures"]             = [{"m_FileID": 0, "m_PathID": GEN_ATLAS_PATH_ID}]
    gen_tt["m_AtlasTextureIndex"]         = 0
    gen_tt["m_AtlasWidth"]                = NEW_W
    gen_tt["m_AtlasHeight"]               = NEW_H
    gen_tt["m_AtlasPopulationMode"]       = 0   # Static — use pre-baked data directly (mode=1 with sequential GIDs causes 177 failures)
    gen_tt["m_IsMultiAtlasTexturesEnabled"] = 0   # match original backup
    # leave m_SourceFontFile at original {pathID:0}; setting it to NotoSansCJK
    # activates TextCore glyph-index validation and silently rejects our sequential entries.
    gen_tt["m_FreeGlyphRects"] = (
        [{"m_X": 0, "m_Y": last_row_top, "m_Width": NEW_W, "m_Height": free_h}]
        if free_h > 0 else []
    )
    gen_tt["m_UsedGlyphRects"] = [
        {"m_X": 0, "m_Y": 0, "m_Width": NEW_W, "m_Height": last_row_top}
    ]
    gen_font_obj.save_typetree(gen_tt)

    # ── 8b. Update Material _TextureWidth/_TextureHeight to match new atlas ──
    # TMP SDF shader uses these for per-texel sampling distance. If they
    # disagree with the actual texture size, SDF gradients are computed at the
    # wrong scale → entire glyphs render as solid blocks (boxes).
    gen_mat_pid = gen_tt.get("m_Material", {}).get("m_PathID", 0) if isinstance(gen_tt.get("m_Material"), dict) else 0
    if gen_mat_pid:
        for mat_obj in env.objects:
            if mat_obj.path_id != gen_mat_pid or mat_obj.type.name != "Material":
                continue
            mt = mat_obj.read_typetree()
            saved = mt.get("m_SavedProperties", {})
            floats = saved.get("m_Floats", [])
            updated_w = updated_h = False
            for i, entry in enumerate(floats):
                # entries may be tuples or dicts depending on UnityPy version
                if isinstance(entry, (list, tuple)):
                    key = entry[0]
                    if key == "_TextureWidth":
                        floats[i] = (key, float(NEW_W)); updated_w = True
                    elif key == "_TextureHeight":
                        floats[i] = (key, float(NEW_H)); updated_h = True
                elif isinstance(entry, dict):
                    key = entry.get("first", entry.get("key"))
                    if key == "_TextureWidth":
                        if "first" in entry: entry["second"] = float(NEW_W)
                        else: entry["value"] = float(NEW_W)
                        updated_w = True
                    elif key == "_TextureHeight":
                        if "first" in entry: entry["second"] = float(NEW_H)
                        else: entry["value"] = float(NEW_H)
                        updated_h = True
            saved["m_Floats"] = floats
            mt["m_SavedProperties"] = saved
            mat_obj.save_typetree(mt)
            print(f"  5g: Material _TextureWidth→{NEW_W} _TextureHeight→{NEW_H} (w={updated_w} h={updated_h})")
            break

    # ── 9. Write extended .resS back into bundle ──────────────────────────────
    new_reader       = EndianBinaryReader(bytearray(res_s_bytes))
    new_reader.flags = orig_flags
    env.file.files[RES_S_KEY] = new_reader

    total_packed = len(gen_glyphs) + len(new_glyph_entries)
    print(f"  5g: Repacked {total_packed} glyphs "
          f"({len(gen_glyphs)} existing + {len(new_glyph_entries)} new from NoUnderlay) "
          f"→ new {NEW_W}×{NEW_H} atlas[0] at .resS offset {new_offset:,} "
          f"({new_offset + NEW_W * NEW_H:,} bytes total)")
    return 1


# ── Futura atlas direct-bake (extends futura's own atlas[0]) ──────────────────

def _restore_futura_fallbacks(env) -> int:
    """Restore Futura's original 3-fallback chain: Generated → NotoNU → Roboto.

    _bake_tc_into_futura bakes TC glyphs with synthetic indices (100000+) and
    strips all fallbacks. Unity 6 TextCore cannot resolve those glyph indices
    at runtime despite correct CharacterTable data (confirmed: 79 chars fail
    with 'was not found' even though they ARE in the table). Restoring the
    fallback chain lets TMP fall through to Generated (4236 TC chars, real
    glyph IDs, zero Player.log errors) → description box renders correctly.
    Returns 1 if changed, 0 if already correct (idempotent)."""
    futura_obj = None
    for obj in env.objects:
        if obj.path_id == FUTURA_TMP_PID:
            futura_obj = obj
            break
    if not futura_obj:
        print("  Futura fallback restore: futura not found — skipping.")
        return 0

    futura_tt = futura_obj.read_typetree()
    current_fb = futura_tt.get("m_FallbackFontAssetTable", [])
    current_pids = {f.get("m_PathID", 0) for f in current_fb if isinstance(f, dict)}
    expected_pids = {GENERATED_FONT_PATH_ID, NO_UNDERLAY_FONT_PATH_ID, ROBOTO_FONT_PATH_ID}
    if expected_pids.issubset(current_pids):
        print(f"  Futura fallback restore: already has {len(current_fb)} fallbacks — skipping.")
        return 0

    futura_tt["m_FallbackFontAssetTable"] = [
        {"m_FileID": 0, "m_PathID": GENERATED_FONT_PATH_ID},    # Generated (4236 TC chars)
        {"m_FileID": 0, "m_PathID": NO_UNDERLAY_FONT_PATH_ID},  # NotoNU (3636 TC chars)
        {"m_FileID": 0, "m_PathID": ROBOTO_FONT_PATH_ID},       # Roboto (9 special chars)
    ]
    futura_obj.save_typetree(futura_tt)
    print("  Futura fallback restore: set 3 fallbacks (Generated→NotoNU→Roboto) ✓")
    return 1


FUTURA_TMP_PID      = 4996038291744176242
FUTURA_ATLAS_PID    = 6757217293111277682
FUTURA_MATERIAL_PID = -6110628699968358286
FUTURA_OLD_W = 1024
FUTURA_OLD_H = 1024
FUTURA_NEW_W = 2048
FUTURA_NEW_H = 8704   # 8704-1024=7680 rows for TC; increased from 8192 to fit all 2593+ TC chars
FUTURA_TC_POINT_SIZE = 70
FUTURA_TC_PADDING    = 5
FUTURA_TC_OVERSAMPLE = 4


def _bake_tc_into_futura(env, noto_bytes: bytes) -> int:
    """Extend futura's atlas[0] from 1024×1024 → 2048×4096 (Alpha8 inline) and
    bake all TC chars directly into it at pointSize=70. Preserve existing 124
    Latin glyphs (occupy max [0..567]×[0..1014] of the original atlas). Strip
    futura's fallback chain so TMP looks up TC directly in the font's own
    lookup dictionary.

    Mirrors the approach proven in `patch_mapbuilder_font.py::_bake_tc_into_mapbuilder`.
    Returns 1 if changed, 0 if already done (idempotent)."""
    import numpy as np
    import freetype
    import tempfile

    futura_obj = atlas_obj = mat_obj = None
    for obj in env.objects:
        if obj.path_id == FUTURA_TMP_PID:      futura_obj = obj
        elif obj.path_id == FUTURA_ATLAS_PID:  atlas_obj  = obj
        elif obj.path_id == FUTURA_MATERIAL_PID: mat_obj  = obj
    if not (futura_obj and atlas_obj and mat_obj):
        print("  Futura bake: futura/atlas/material not found — skipping.")
        return 0

    futura_tt = futura_obj.read_typetree()
    atlas_tt  = atlas_obj.read_typetree()
    mat_tt    = mat_obj.read_typetree()

    char_table = futura_tt.get("m_CharacterTable", [])
    glyphs = futura_tt.get("m_GlyphTable", [])  # Define glyphs early for validity check
    glyph_table_len = len(glyphs)
    has_broken_indices = any(
        c.get("m_Unicode", 0) >= 0x4E00 and (
            c.get("m_GlyphIndex", -1) >= glyph_table_len or c.get("m_GlyphIndex", -1) >= 100000
        )
        for c in char_table
    )
    
    # Idempotency: if atlas already extended AND has valid glyph indices AND has RENDERED TC glyphs, skip
    # (Check: TC char entries must have corresponding glyphs with m_Width > 0, not just exist in table)
    tc_count_existing = sum(1 for c in char_table if c.get("m_Unicode", 0) >= 0x4E00)  # >= CJK Unified Ideographs start
    tc_with_valid_glyphs = 0
    for c in char_table:
        if c.get("m_Unicode", 0) >= 0x4E00:  # TC char
            idx = c.get("m_GlyphIndex", -1)
            if idx >= 0 and idx < len(glyphs) and glyphs[idx].get("m_GlyphRect", {}).get("m_Width", 0) > 0:
                tc_with_valid_glyphs += 1
    
    if (atlas_tt.get("m_Height", 0) >= FUTURA_NEW_H and 
        atlas_tt.get("m_Width", 0) >= FUTURA_NEW_W and
        not has_broken_indices and
        tc_with_valid_glyphs >= 1500 and
        tc_count_existing == 0):  # ALSO require: no TC entries left to avoid stale data
        print(f"  Futura bake: atlas already {atlas_tt['m_Width']}×{atlas_tt['m_Height']} with {tc_with_valid_glyphs} rendered TC chars — skipping.")
        return 0
    
    # Force bake if ANY TC entries exist (they're stale/empty)
    force_bake = tc_count_existing > 0
    
    if has_broken_indices or force_bake:
        if has_broken_indices:
            print(f"  Futura bake: detected OUT_OF_BOUNDS glyph indices — forcing re-bake to fix")
        if force_bake:
            print(f"  Futura bake: found {tc_count_existing} stale TC entries — clearing to force re-bake")
        # Keep only original Latin glyphs (low ID numbers < 700, rendered before TC bake)
        # Remove all TC-related glyphs including empty ones
        new_glyph_table = [g for g in futura_tt.get("m_GlyphTable", []) 
                          if g["m_Index"] < 700]  # Keep only original Latin glyphs
        kept_glyph_ids = {g["m_Index"] for g in new_glyph_table}
        # Keep only Latin chars (Unicode < 0x4E00) whose glyphs are in the kept set
        new_char_table = [c for c in char_table if c.get("m_Unicode", 0) < 0x4E00 and c.get("m_GlyphIndex", -1) in kept_glyph_ids]
        removed_chars = len(char_table) - len(new_char_table)
        print(f"  Futura bake: keeping {len(new_char_table)} Latin chars, removing {removed_chars} TC entries and associated glyphs")
        removed_glyphs = len(futura_tt.get("m_GlyphTable", [])) - len(new_glyph_table)
        print(f"  Futura bake: GlyphTable {len(futura_tt.get('m_GlyphTable', []))} → {len(new_glyph_table)} (removed {removed_glyphs} TC glyphs)")
        futura_tt["m_CharacterTable"] = new_char_table
        futura_tt["m_GlyphTable"] = new_glyph_table
        char_table = new_char_table  # Update for downstream checks
    elif tc_with_valid_glyphs < 1500 and tc_count_existing > 0:
        print(f"  Futura bake: {tc_count_existing} TC entries but only {tc_with_valid_glyphs} rendered — removing empty TC glyphs")
        # Remove TC char entries that have empty glyphs
        new_char_table = []
        for c in char_table:
            idx = c.get("m_GlyphIndex", -1)
            if c.get("m_Unicode", 0) >= 0x4E00:  # TC char
                # Only keep if glyph is valid and rendered
                if idx >= 0 and idx < len(glyphs) and glyphs[idx].get("m_GlyphRect", {}).get("m_Width", 0) > 0:
                    new_char_table.append(c)
            else:
                # Keep non-TC chars
                new_char_table.append(c)
        removed = len(char_table) - len(new_char_table)
        print(f"  Futura bake: removing {removed} empty TC glyph entries, keeping {len(new_char_table)}")
        futura_tt["m_CharacterTable"] = new_char_table
        char_table = new_char_table

    tc_needed = _get_tc_chars_needed()
    print(f"  Futura bake: TC chars needed = {len(tc_needed)}")
    # Exclude chars already in Futura's CharacterTable (pristine has 9 overlapping
    # chars: –, —, ', ', ", ", „, •, …). Adding them again creates duplicate Unicode
    # entries → second occurrence is skipped by TMP's dict build → original Latin
    # versions (correct size/position) remain → no visual regression.
    _existing_unicodes = {c["m_Unicode"] for c in char_table}
    to_bake = sorted(cp for cp in tc_needed if cp not in _existing_unicodes)
    _skipped_existing = len(tc_needed) - len(to_bake)
    if _skipped_existing:
        print(f"  Futura bake: skipping {_skipped_existing} chars already in Futura (e.g. –,—,•,…)")
    print(f"  Futura bake: baking {len(to_bake)} TC chars into extended atlas...")

    # ─ Continue below with atlas extension and glyph rendering (DO NOT RETURN EARLY) ─

    # Read existing 1024×1024 atlas bytes
    img_data = atlas_tt.get("image data", b"")
    
    # Handle both original (1024×1024) and re-bake (2048×8192) cases
    if len(img_data) == FUTURA_OLD_W * FUTURA_OLD_H:
        # Original size
        old = np.frombuffer(bytes(img_data), dtype=np.uint8).reshape(FUTURA_OLD_H, FUTURA_OLD_W)
    elif len(img_data) == FUTURA_NEW_W * FUTURA_NEW_H:
        # Already extended from previous bake — extract just the bottom original portion
        full_img = np.frombuffer(bytes(img_data), dtype=np.uint8).reshape(FUTURA_NEW_H, FUTURA_NEW_W)
        old = full_img[:FUTURA_OLD_H, :FUTURA_OLD_W]
    else:
        print(f"  Futura bake: ERROR atlas data {len(img_data)} != {FUTURA_OLD_W*FUTURA_OLD_H} or {FUTURA_NEW_W*FUTURA_NEW_H}", file=sys.stderr)
        return 0

    # Build new 2048×8192 image (bottom-up). Latin keeps Y_bu ∈ [0..1023], X ∈ [0..1023]
    new_img = np.zeros((FUTURA_NEW_H, FUTURA_NEW_W), dtype=np.uint8)
    new_img[:FUTURA_OLD_H, :FUTURA_OLD_W] = old

    # Bake TC chars into the region above Y_bu=1024 using Noto font
    with tempfile.NamedTemporaryFile(suffix=".ttf", delete=False) as tmp:
        tmp.write(bytes(noto_bytes))
        font_path = tmp.name
    try:
        face = freetype.Face(font_path)

        # Top-down packer over the bake region (width 2048, height 3072)
        REGION_W = FUTURA_NEW_W
        REGION_H = FUTURA_NEW_H - FUTURA_OLD_H   # 7680 with FUTURA_NEW_H=8704
        region = np.zeros((REGION_H, REGION_W), dtype=np.uint8)

        # Start TC glyph indices at max(existing)+1 = 255 on pristine Futura.
        # MUST NOT start at len(GlyphTable)=124 — that overlaps Latin glyph IDs
        # 3..254 and corrupts GlyphLookupDictionary (58 chars silently fail).
        _existing_gi = {g["m_Index"] for g in futura_tt["m_GlyphTable"]}
        glyph_idx = max(_existing_gi, default=0) + 1

        ax = ay = row_h = 0
        new_chars, new_glyphs, new_used = [], [], []
        packed = skipped_invis = skipped_full = 0

        # Per-glyph scale factor so TC chars render at ~ same visual size as
        # futura's native pointSize=90 reference. TC point size is 70 so
        # m_Scale = 90/70 ≈ 1.286 would up-scale — but Unity SDF uses the rect
        # height directly with FaceInfo.PointSize as the "1 em" reference, so
        # use m_Scale=1.0 here (TC will appear at ~70/90 = 78% of em which is
        # fine for body text and matches CJK conventions).
        tc_scale = 1.0

        for cp in to_bake:
            sdf, gw, gh, metrics = _generate_sdf(face, cp, FUTURA_TC_POINT_SIZE,
                                                 FUTURA_TC_PADDING, FUTURA_TC_OVERSAMPLE)
            if sdf is None or gw == 0:
                new_chars.append({
                    "m_ElementType": 1, "m_Unicode": cp,
                    "m_GlyphIndex": glyph_idx, "m_Scale": tc_scale,
                })
                new_glyphs.append({
                    "m_Index": glyph_idx,
                    "m_Metrics": {
                        "m_Width": 0.0, "m_Height": 0.0,
                        "m_HorizontalBearingX": 0.0, "m_HorizontalBearingY": 0.0,
                        "m_HorizontalAdvance": metrics["advance"],
                    },
                    "m_GlyphRect": {"m_X": 0, "m_Y": 0, "m_Width": 0, "m_Height": 0},
                    "m_Scale": 1.0, "m_AtlasIndex": 0, "m_ClassDefinitionType": 0,
                })
                glyph_idx += 1; skipped_invis += 1; continue

            full_w = gw + 2 * FUTURA_TC_PADDING
            full_h = gh + 2 * FUTURA_TC_PADDING
            if ax + full_w > REGION_W:
                ax = 0; ay += row_h; row_h = 0
            if ay + full_h > REGION_H:
                skipped_full = len(to_bake) - packed - skipped_invis
                print(f"  Futura bake: region full after {packed} chars — {skipped_full} skipped")
                break

            region[ay:ay+full_h, ax:ax+full_w] = sdf

            # Region sits ABOVE the preserved Latin area in bottom-up coords:
            # top of region (Y_td=0) maps to Y_bu = FUTURA_NEW_H - 1
            # bottom of region (Y_td=REGION_H-1) maps to Y_bu = FUTURA_OLD_H
            used_y_td_top    = ay
            used_y_td_bottom = ay + full_h - 1
            used_y_bu_bottom = (FUTURA_NEW_H - 1) - used_y_td_bottom
            # (so the rect's bottom-up Y origin = used_y_bu_bottom)

            glyph_x_bu = ax + FUTURA_TC_PADDING
            glyph_y_bu = used_y_bu_bottom + FUTURA_TC_PADDING

            new_used.append({
                "m_X": ax, "m_Y": used_y_bu_bottom,
                "m_Width": full_w, "m_Height": full_h,
            })
            new_chars.append({
                "m_ElementType": 1, "m_Unicode": cp,
                "m_GlyphIndex": glyph_idx, "m_Scale": tc_scale,
            })
            new_glyphs.append({
                "m_Index": glyph_idx,
                "m_Metrics": {
                    "m_Width":  metrics["width"],
                    "m_Height": metrics["height"],
                    "m_HorizontalBearingX": metrics["bearingX"],
                    "m_HorizontalBearingY": metrics["bearingY"],
                    "m_HorizontalAdvance":  metrics["advance"],
                },
                "m_GlyphRect": {
                    "m_X": glyph_x_bu, "m_Y": glyph_y_bu,
                    "m_Width": gw, "m_Height": gh,
                },
                "m_Scale": 1.0, "m_AtlasIndex": 0, "m_ClassDefinitionType": 0,
            })
            ax += full_w
            row_h = max(row_h, full_h)
            glyph_idx += 1
            packed += 1
    finally:
        try: os.unlink(font_path)
        except OSError: pass

    # Composite region (top-down) into new_img (bottom-up). Flip region vertically
    # then drop it at Y_bu ∈ [FUTURA_OLD_H .. FUTURA_NEW_H-1].
    region_botup = np.flipud(region)
    new_img[FUTURA_OLD_H:FUTURA_NEW_H, :REGION_W] = region_botup

    new_bytes = new_img.tobytes()
    assert len(new_bytes) == FUTURA_NEW_W * FUTURA_NEW_H

    # Update Texture2D
    atlas_tt["image data"]          = new_bytes
    atlas_tt["m_Width"]             = FUTURA_NEW_W
    atlas_tt["m_Height"]            = FUTURA_NEW_H
    atlas_tt["m_CompleteImageSize"] = len(new_bytes)
    atlas_tt["m_MipCount"]          = 1
    atlas_tt["m_StreamData"]        = {"offset": 0, "size": 0, "path": ""}
    atlas_obj.save_typetree(atlas_tt)

    # Update TMP font
    futura_tt["m_AtlasWidth"]       = FUTURA_NEW_W
    futura_tt["m_AtlasHeight"]      = FUTURA_NEW_H
    futura_tt["m_CharacterTable"]   = list(futura_tt["m_CharacterTable"]) + new_chars
    futura_tt["m_GlyphTable"]       = list(futura_tt["m_GlyphTable"])     + new_glyphs
    futura_tt["m_UsedGlyphRects"]   = list(futura_tt.get("m_UsedGlyphRects", [])) + new_used
    # New free rect = remaining region tail (top of bake area not yet used)
    free_h_td = REGION_H - (ay + row_h)
    if free_h_td > 0:
        free_y_bu = FUTURA_OLD_H  # bottom of unused area in bottom-up coords
        new_free  = [{"m_X": 0, "m_Y": free_y_bu, "m_Width": FUTURA_NEW_W, "m_Height": free_h_td}]
    else:
        new_free  = []
    futura_tt["m_FreeGlyphRects"]   = new_free
    # Restore fallback chain — TC chars with synthetic glyph indices (100000+)
    # are not found by Unity 6 TextCore at runtime; fallbacks let them resolve
    # via Generated (4236 TC chars, real glyph IDs) as proven fallback.
    futura_tt["m_FallbackFontAssetTable"] = [
        {"m_FileID": 0, "m_PathID": GENERATED_FONT_PATH_ID},    # Generated (4236 TC chars)
        {"m_FileID": 0, "m_PathID": NO_UNDERLAY_FONT_PATH_ID},  # NotoNU (3636 TC chars)
        {"m_FileID": 0, "m_PathID": ROBOTO_FONT_PATH_ID},       # Roboto (9 special chars)
    ]
    # Static mode (pop=0) for Futura — TC chars use sequential GIDs (255+) baked from NotoSansCJKtc.
    # mode=0 bypasses TMP’s runtime GID validation: all pre-baked TC chars enter CharacterLookupDictionary
    # and render from Futura’s inline atlas.
    # mode=1 with Futura GUID would validate TC GIDs against Futura OTF which has no CJK → all TC chars rejected.
    futura_tt["m_AtlasPopulationMode"] = 0   # Static — no GID validation → all TC chars accepted
    futura_tt["m_SourceFontFile"]      = {"m_FileID": 0, "m_PathID": 0}  # null source
    
    # DO NOT STRIP TC characters — they were just baked into the atlas and added to CharacterTable.
    # Keep them so they can be looked up directly in Futura without needing fallbacks.
    # This is the key fix: TC characters now render from Futura's own atlas, not via fallback chain.
    
    # CRITICAL: Sort CharacterTable by Unicode value!
    # TMP uses binary search which requires sorted order. If unsorted, binary search fails to find chars.
    futura_tt["m_CharacterTable"] = sorted(futura_tt["m_CharacterTable"], 
                                           key=lambda c: c.get("m_Unicode", 0))
    
    futura_obj.save_typetree(futura_tt)

    # Update Material _TextureWidth / _TextureHeight
    saved = mat_tt.get("m_SavedProperties", {})
    floats = saved.get("m_Floats", [])
    upd_w = upd_h = False
    for i, entry in enumerate(floats):
        if isinstance(entry, (list, tuple)):
            key = entry[0]
            if key == "_TextureWidth":
                floats[i] = (key, float(FUTURA_NEW_W)); upd_w = True
            elif key == "_TextureHeight":
                floats[i] = (key, float(FUTURA_NEW_H)); upd_h = True
    if not upd_w: floats.append(("_TextureWidth",  float(FUTURA_NEW_W)))
    if not upd_h: floats.append(("_TextureHeight", float(FUTURA_NEW_H)))
    saved["m_Floats"] = floats
    mat_tt["m_SavedProperties"] = saved
    mat_obj.save_typetree(mat_tt)

    print(f"  Futura bake: packed {packed} chars (invisible {skipped_invis}, skipped {skipped_full}). "
          f"Atlas {FUTURA_OLD_W}×{FUTURA_OLD_H} → {FUTURA_NEW_W}×{FUTURA_NEW_H}. "
          f"Char table: {len(futura_tt['m_CharacterTable'])}, fallbacks=Generated→NotoNU→Roboto.")
    return 1


def _set_futura_to_dynamic_noto(env, baked_tc_chars: list, baked_tc_glyphs: list) -> int:
    """
    Step 7: Merge NoUnderlay's 754 TC chars DIRECTLY into futura.
    
    Fallback system doesn't work in this game. The only approach that works
    is mapbuilder: chars directly pre-baked into the font itself. So we:
      1. Copy all 754 TC chars from baked_tc_chars into futura's CharacterTable
      2. Copy corresponding glyphs from baked_tc_glyphs into futura's GlyphTable  
      3. Reference NoUnderlay's atlas as futura's second atlas
      4. Keep futura STATIC (pop=0) - no Dynamic generation needed
    
    This makes futura self-contained like the working mapbuilder font.
    
    Args:
        env: UnityPy environment
        baked_tc_chars: List of Character dicts from NoUnderlay (754 TC chars)
        baked_tc_glyphs: List of Glyph dicts from NoUnderlay (754 TC glyphs)
    
    Returns 1 if changed, 0 if already correct (idempotent).
    """
    FUTURA_PATH_ID      = 4996038291744176242
    NO_UNDERLAY_ATLAS_PID = 4927299259637123988

    # Get futura font
    futura_obj = None
    for obj in env.objects:
        if obj.path_id == FUTURA_PATH_ID:
            futura_obj = obj
            break

    if not futura_obj:
        print("  Futura merge: futura TMP font not found — skipping.")
        return 0

    futura_tt = futura_obj.read_typetree()
    
    # Idempotency: check if already merged (futura should have >700 chars)
    if len(futura_tt.get("m_CharacterTable", [])) > 700:
        print(f"  Futura TMP: already has {len(futura_tt['m_CharacterTable'])} chars — skipping merge.")
        return 0

    if not baked_tc_chars:
        print("  Futura merge: no TC chars provided — skipping.")
        return 0
    
    print(f"  DEBUG: Received {len(baked_tc_chars)} TC chars, {len(baked_tc_glyphs)} TC glyphs for merge")

    # Merge chars and glyphs
    futura_chars = list(futura_tt.get("m_CharacterTable", []))
    futura_glyphs = list(futura_tt.get("m_GlyphTable", []))
    
    orig_char_count = len(futura_chars)
    orig_glyph_count = len(futura_glyphs)
    
    futura_unicode_set = {c["m_Unicode"] for c in futura_chars}
    futura_glyph_ids = {g["m_Index"] for g in futura_glyphs}
    
    added_chars = 0
    added_glyphs = 0
    
    # Find the highest glyph index in futura to avoid collisions
    max_futura_glyph_idx = max((g["m_Index"] for g in futura_glyphs), default=0)
    glyph_idx_offset = max_futura_glyph_idx + 1
    
    # Map old TC glyph indices to new renumbered indices
    old_to_new_glyph_idx = {}
    
    # Add TC glyphs with renumbered indices
    new_glyph_idx = glyph_idx_offset
    for tc_glyph in baked_tc_glyphs:
        old_idx = tc_glyph["m_Index"]
        new_glyph = dict(tc_glyph)
        new_glyph["m_Index"] = new_glyph_idx
        new_glyph["m_AtlasIndex"] = 1  # Reference atlas[1] = NoUnderlay
        futura_glyphs.append(new_glyph)
        old_to_new_glyph_idx[old_idx] = new_glyph_idx
        new_glyph_idx += 1
        added_glyphs += 1
    
    # Add TC chars with updated glyph indices
    for tc_char in baked_tc_chars:
        if tc_char["m_Unicode"] not in futura_unicode_set:
            new_char = dict(tc_char)
            # Update glyph index to renumbered value
            old_glyph_idx = tc_char["m_GlyphIndex"]
            new_char["m_GlyphIndex"] = old_to_new_glyph_idx.get(old_glyph_idx, old_glyph_idx)
            futura_chars.append(new_char)
            added_chars += 1
    
    # Add NoUnderlay atlas as second atlas
    futura_atlases = list(futura_tt.get("m_AtlasTextures", []))
    futura_atlases.append({"m_FileID": 0, "m_PathID": NO_UNDERLAY_ATLAS_PID})
    
    # Update futura (DON'T create fresh dict - directly modify futura_tt)
    futura_tt["m_CharacterTable"] = futura_chars
    futura_tt["m_GlyphTable"] = futura_glyphs
    futura_tt["m_AtlasTextures"] = futura_atlases
    futura_tt["m_FallbackFontAssetTable"] = []
    
    # DEBUG
    print(f"  DEBUG: futura_glyphs list len={len(futura_glyphs)}")
    print(f"  DEBUG: futura_tt['m_GlyphTable'] len={len(futura_tt['m_GlyphTable'])}")
    
    # WORKAROUND for UnityPy cache bug: Set fields AGAIN right before save
    # Multiple explicit sets to force UnityPy to use our data
    futura_tt["m_CharacterTable"] = futura_chars
    futura_tt["m_GlyphTable"] = futura_glyphs
    futura_tt["m_AtlasTextures"] = futura_atlases
    
    futura_obj.save_typetree(futura_tt)
    
    # DEBUG: Verify after save (will be cached, but let's see)
    verify_tt = futura_obj.read_typetree()
    print(f"  DEBUG AFTER SAVE (cached): m_GlyphTable len={len(verify_tt.get('m_GlyphTable', []))}")
    
    print(f"  Futura TMP: Merged {added_chars} TC chars + {added_glyphs} glyphs from NoUnderlay (renumbered glyph indices starting from {glyph_idx_offset}).")
    print(f"              Original: {orig_char_count} chars + {orig_glyph_count} glyphs → Final: {len(futura_chars)} chars + {len(futura_glyphs)} glyphs, {len(futura_atlases)} atlases.")
    return 1



def _fix_glyph_indices_to_real_font_ids(env) -> int:
    """
    Step 6: Replace arbitrary high glyph indices (>=59000) with the real
    NotoSansCJKjp glyph IDs as reported by FreeType.

    For a Static TMP font with m_SourceFontFile set, Unity TextCore validates
    each m_GlyphIndex against the actual font binary at load time.  Chars whose
    stored glyph index does not match the font file's glyph ID are silently
    excluded from the runtime CharacterLookupDictionary and never rendered.

    The original 3401 chars have correct font glyph IDs (e.g. 9831 for U+4E00).
    The 754 chars we added were given sequential IDs starting at 59000+ which do
    NOT match the font file and are therefore rejected by TextCore.

    Returns 1 if changes were made, 0 if already correct (idempotent).
    """
    import freetype
    import io

    HIGH_GI_THRESHOLD = 59000  # IDs >= this were assigned by us, not by the font

    gen_obj    = None
    noto_bytes = None
    for obj in env.objects:
        if obj.path_id == GENERATED_FONT_PATH_ID:
            gen_obj = obj
        elif obj.path_id == NOTO_FONT_OBJECT_PATH_ID:
            fo = obj.read()
            noto_bytes = bytes(fo.m_FontData)
        if gen_obj and noto_bytes:
            break

    if not gen_obj or not noto_bytes:
        print("  Step 6: Required objects not found — skipping.")
        return 0

    gen_tt = gen_obj.read_typetree()
    chars  = gen_tt["m_CharacterTable"]
    glyphs = gen_tt["m_GlyphTable"]

    hi_glyph_ids = {g["m_Index"] for g in glyphs if g["m_Index"] >= HIGH_GI_THRESHOLD}
    if not hi_glyph_ids:
        print(f"  Step 6: No high-index glyphs (>={HIGH_GI_THRESHOLD}) — already fixed.")
        return 0

    print(f"  Step 6: Fixing {len(hi_glyph_ids)} high-index glyph slots "
          f"using real NotoSansCJKjp glyph IDs...")

    face = freetype.Face(io.BytesIO(noto_bytes))

    # Map: old_high_gi → real_font_gi  (one FreeType lookup per unique old index)
    old_to_real = {}
    for c in chars:
        old_gi = c["m_GlyphIndex"]
        if old_gi >= HIGH_GI_THRESHOLD and old_gi not in old_to_real:
            old_to_real[old_gi] = face.get_char_index(c["m_Unicode"])

    # Original glyph indices that must not be overwritten
    orig_glyph_ids = {g["m_Index"] for g in glyphs if g["m_Index"] < HIGH_GI_THRESHOLD}

    # ── Update CharacterTable ─────────────────────────────────────────────────
    # Chars whose real_gi == 0 are not in NotoSansCJK — remove them entirely.
    new_chars = []
    for c in chars:
        old_gi = c.get("m_GlyphIndex", 0)
        if old_gi not in old_to_real:
            new_chars.append(dict(c))        # original char — keep as-is
            continue
        real_gi = old_to_real[old_gi]
        if real_gi == 0:
            continue                          # not in font — drop
        nc = dict(c)
        nc["m_GlyphIndex"] = real_gi
        new_chars.append(nc)

    # ── Update GlyphTable ─────────────────────────────────────────────────────
    # Rename high-index glyphs to real_gi; drop if invalid/duplicate/conflicting.
    seen_real_gis = set()
    new_glyphs = []
    for g in glyphs:
        old_gi = g["m_Index"]
        if old_gi not in old_to_real:
            new_glyphs.append(dict(g))        # original glyph — keep as-is
            continue
        real_gi = old_to_real[old_gi]
        if real_gi == 0:
            continue                           # invalid — drop
        if real_gi in orig_glyph_ids:
            continue                           # original already owns this glyph
        if real_gi in seen_real_gis:
            continue                           # duplicate real_gi — drop
        ng = dict(g)
        ng["m_Index"] = real_gi
        new_glyphs.append(ng)
        seen_real_gis.add(real_gi)

    gen_tt["m_CharacterTable"]              = new_chars
    gen_tt["m_GlyphTable"]                  = new_glyphs
    # Re-assert Step 1's Static config because read_typetree() may return a
    # stale cached snapshot taken before Step 1 saved.
    gen_tt["m_AtlasPopulationMode"]         = 0   # Static — use pre-baked data directly
    gen_tt["m_IsMultiAtlasTexturesEnabled"] = 0
    gen_obj.save_typetree(gen_tt)

    removed_chars  = len(chars)  - len(new_chars)
    removed_glyphs = len(glyphs) - len(new_glyphs)
    print(f"  Step 6: Done. Chars {len(chars)}→{len(new_chars)} "
          f"({removed_chars} dropped, rest have real glyph IDs). "
          f"Glyphs {len(glyphs)}→{len(new_glyphs)} "
          f"({removed_glyphs} removed/merged).")
    return 1


# ── NotoSansCJK No-Underlay atlas direct-bake (TC chars for description body) ─
# Same approach as _bake_tc_into_futura but for NotoSansCJKjp-Regular SDF - No Underlay
# which is used for campaign/crusade description text and only has 941 original chars.
NOTO_NU_OLD_W         = 2048
NOTO_NU_OLD_H         = 2048
NOTO_NU_NEW_W         = 2048
NOTO_NU_NEW_H         = 8192   # 6144 rows for TC region
NOTO_NU_TC_POINT_SIZE = 70
NOTO_NU_TC_PADDING    = 5
NOTO_NU_TC_OVERSAMPLE = 4
NOTO_NU_MATERIAL_PID  = -6068476065370780780  # NotoSansCJKjp-Regular SDF Material (for No Underlay)
# RES_S_KEY is defined inside _repack_all_glyphs_into_new_atlas; redefine here for clarity
_NOTO_NU_RES_S_KEY = "CAB-be8dbf1298107e31652b994c6db02e50.resS"


def _force_futura_to_noto(env) -> int:
    """Force futura TMP font to use Noto No-Underlay data as primary renderer.

    This is a deterministic, Vortex-safe strategy for TC rendering stability:
      - futura keeps its path/name identity (UI references remain valid)
      - but its Character/Glyph tables and atlas references are replaced with
        NotoSansCJKjp No-Underlay tables/atlas (already patched for TC)

    Returns 1 if changed, 0 if already in forced-Noto state.
    """
    futura_obj = None
    noto_obj = None
    for obj in env.objects:
        if obj.path_id == FUTURA_TMP_PID:
            futura_obj = obj
        elif obj.path_id == NO_UNDERLAY_FONT_PATH_ID:
            noto_obj = obj
        if futura_obj and noto_obj:
            break

    if not futura_obj or not noto_obj:
        print("  Force Noto: futura or NotoNU TMP font not found — skipping.")
        return 0

    futura_tt = futura_obj.read_typetree()
    noto_tt = noto_obj.read_typetree()

    futura_chars = futura_tt.get("m_CharacterTable", [])
    noto_chars = noto_tt.get("m_CharacterTable", [])

    # Idempotency: same atlas source + same/greater char coverage
    futura_atlases = futura_tt.get("m_AtlasTextures", []) or []
    forced_already = (
        len(futura_atlases) > 0
        and futura_atlases[0].get("m_PathID", 0) == NO_UNDERLAY_ATLAS_PATH_ID
        and len(futura_chars) >= len(noto_chars)
    )
    if forced_already:
        print(f"  Force Noto: futura already using Noto atlas/tables ({len(futura_chars)} chars), skipping.")
        return 0

    futura_tt["m_CharacterTable"] = [dict(c) for c in noto_tt.get("m_CharacterTable", [])]
    futura_tt["m_GlyphTable"] = [dict(g) for g in noto_tt.get("m_GlyphTable", [])]
    futura_tt["m_AtlasTextures"] = [dict(a) for a in noto_tt.get("m_AtlasTextures", [])]
    futura_tt["m_AtlasWidth"] = noto_tt.get("m_AtlasWidth", FUTURA_NEW_W)
    futura_tt["m_AtlasHeight"] = noto_tt.get("m_AtlasHeight", FUTURA_NEW_H)
    futura_tt["m_AtlasPopulationMode"] = 0
    futura_tt["m_IsMultiAtlasTexturesEnabled"] = 0
    futura_tt["m_FallbackFontAssetTable"] = [
        {"m_FileID": 0, "m_PathID": GENERATED_FONT_PATH_ID},
        {"m_FileID": 0, "m_PathID": ROBOTO_FONT_PATH_ID},
    ]

    # Keep source font local + resolvable if present
    src = noto_tt.get("m_SourceFontFile")
    if isinstance(src, dict):
        futura_tt["m_SourceFontFile"] = dict(src)

    # Character table binary-search safety
    futura_tt["m_CharacterTable"] = sorted(
        futura_tt["m_CharacterTable"], key=lambda c: c.get("m_Unicode", 0)
    )

    futura_obj.save_typetree(futura_tt)
    print(
        f"  Force Noto: futura now mirrors NotoNU tables ({len(futura_tt['m_CharacterTable'])} chars, "
        f"{len(futura_tt['m_GlyphTable'])} glyphs)."
    )
    return 1


def _load_external_otf_characters(otf_path: str) -> list:
    """Extract character table from external OTF font file for Futura substitution.
    
    Downloads Noto Sans CJK TC from Google Fonts if needed, or uses existing OTF file.
    Returns list of {"m_Unicode": int, "m_GlyphIndex": int} entries compatible with TMP.
    """
    import os
    
    # Check if external OTF exists in .copilot_workspace
    workspace_otf = os.path.join(os.path.dirname(__file__), "../../.copilot_workspace/NotoSansCJKtc-Regular.otf")
    if os.path.exists(workspace_otf):
        otf_path = workspace_otf
        print(f"  Using external OTF: {otf_path}")
    else:
        print(f"  External OTF not found at {workspace_otf}")
        return []
    
    try:
        from fontTools import ttLib
        
        print(f"  Loading OTF: {otf_path}")
        font = ttLib.TTFont(otf_path)
        cmap_table = font['cmap']
        cmap = cmap_table.getBestCmap()
        
        # Build character table from OTF
        char_table = []
        for unicode_val, glyph_name in cmap.items():
            char_entry = {
                "m_ElementType": 1,
                "m_Unicode": unicode_val,
                "m_GlyphIndex": len(char_table),  # Sequential indices
                "m_Scale": 1.0,
            }
            char_table.append(char_entry)
        
        # Verify test characters are present
        test_unicodes = {0x5EAB, 0x6578, 0x6A5F, 0x7121, 0x968A, 0x9EDE}
        found_test = sum(1 for c in char_table if c['m_Unicode'] in test_unicodes)
        print(f"  ✓ Loaded {len(char_table)} chars from OTF, test chars found: {found_test}/6")
        
        return char_table
        
    except Exception as e:
        print(f"  ERROR loading OTF: {e}")
        return []


def _substitute_futura_with_noto(env) -> int:
    """FONT SUBSTITUTION: Replace Futura's internal data with complete NotoSansCJK data.
    
    Game UI components reference Futura by name/ID. When Futura is loaded, instead
    of rendering with just 124 Latin chars, it will render with complete TC+Latin coverage.
    Futura's name, ID, and fallback chain remain unchanged.
    
    This approach bypasses the need to find and modify UI component references and
    avoids requiring IL2CPP patching. The game loads "Futura" and gets full coverage.
    
    Returns 1 if substitution was performed, 0 if already done (idempotent).
    """
    import os
    
    NOTO_UNDERLAY_PID = 7178690147649604500  # NotoSansCJKjp-Regular SDF - No Underlay
    FUTURA_PID = 4996038291744176242
    
    # Try to load external OTF first (complete coverage)
    external_char_table = _load_external_otf_characters(None)
    
    # Find Futura font object
    futura_obj = None
    for obj in env.objects:
        if obj.path_id == FUTURA_PID:
            futura_obj = obj
            break
    
    if not futura_obj:
        print("  Font substitution: Futura font not found → skipping.")
        return 0
    
    futura_tt = futura_obj.read_typetree()
    futura_glyphs = len(futura_tt.get("m_GlyphTable", []))
    
    # Idempotency check: if Futura already has full coverage, skip
    if futura_glyphs > 40000:  # 40k+ means external OTF was already applied
        print(f"  Font substitution: Futura already has full coverage ({futura_glyphs} glyphs) → skipping.")
        return 0
    
    # If external OTF loaded successfully, use it (has 44k+ chars)
    if external_char_table and len(external_char_table) > 40000:
        print(f"  Font substitution: Using external Noto OTF ({len(external_char_table)} chars)")
        
        # Generate synthetic glyph table (TextMeshPro will fill in the real glyphs at runtime in Dynamic mode)
        glyph_table = []
        for i in range(len(external_char_table)):
            glyph_entry = {
                "m_Index": i,
                "m_Metrics": {
                    "m_Width": 0.0,
                    "m_Height": 0.0,
                    "m_HorizontalBearingX": 0.0,
                    "m_HorizontalBearingY": 0.0,
                    "m_HorizontalAdvance": 1.0,
                },
                "m_GlyphRect": {"m_X": 0, "m_Y": 0, "m_Width": 0, "m_Height": 0},
                "m_Scale": 1.0,
                "m_AtlasIndex": 0,
                "m_ClassDefinitionType": 0,
            }
            glyph_table.append(glyph_entry)
        
        futura_tt["m_CharacterTable"] = external_char_table
        futura_tt["m_GlyphTable"] = glyph_table
        futura_tt["m_AtlasPopulationMode"] = 1  # Dynamic mode
        
        futura_obj.save_typetree(futura_tt)
        print(f"  Font substitution: Futura now has {len(external_char_table)} chars + Dynamic mode ✓")
        return 1
    
    # Fallback: use in-game Noto if external OTF not available
    print("  Font substitution: External OTF not available, using in-game Noto as fallback")
    noto_obj = None
    for obj in env.objects:
        if obj.path_id == NOTO_UNDERLAY_PID:
            noto_obj = obj
            break
    
    if not noto_obj:
        print("  Font substitution: Neither external OTF nor in-game Noto found → skipping.")
        return 0
    
    noto_tt   = noto_obj.read_typetree()
    noto_chars   = noto_tt.get("m_CharacterTable", [])
    noto_glyphs  = noto_tt.get("m_GlyphTable", [])
    
    noto_chars_count = len(noto_chars)
    noto_glyphs_count = len(noto_glyphs)
    print(f"  Font substitution: Fallback Noto has {noto_chars_count} chars, {noto_glyphs_count} glyphs")
    
    if noto_chars_count < 2000:
        print("  Font substitution: In-game Noto incomplete (corrupted) → cannot substitute.")
        return 0
    
    # Copy in-game Noto's data (if external OTF unavailable)
    futura_tt["m_CharacterTable"]  = [dict(c) for c in noto_chars]
    futura_tt["m_GlyphTable"]      = [dict(g) for g in noto_glyphs]
    futura_tt["m_AtlasTextures"]   = [dict(a) for a in noto_tt.get("m_AtlasTextures", [])]
    
    noto_source = noto_tt.get("m_SourceFontFile")
    if noto_source:
        futura_tt["m_SourceFontFile"] = dict(noto_source) if isinstance(noto_source, dict) else noto_source
    
    futura_tt["m_AtlasWidth"]            = noto_tt.get("m_AtlasWidth", 2048)
    futura_tt["m_AtlasHeight"]           = noto_tt.get("m_AtlasHeight", 2048)
    futura_tt["m_IsMultiAtlasTexturesEnabled"] = noto_tt.get("m_IsMultiAtlasTexturesEnabled", 0)
    futura_tt["m_AtlasPopulationMode"]   = noto_tt.get("m_AtlasPopulationMode", 1)
    
    futura_obj.save_typetree(futura_tt)
    print(f"  Font substitution: Futura now references Noto's {noto_chars_count} chars + {noto_glyphs_count} glyphs ✓")
    return 1


def _bake_tc_into_noto_no_underlay(env, noto_bytes: bytes) -> int:
    """Extend NotoSansCJKjp-Regular SDF - No Underlay atlas from 2048×2048 → 2048×8192
    and bake all TC chars directly into it (inline storage, same as futura approach).

    This font (pid=NO_UNDERLAY_FONT_PATH_ID) is used for campaign/crusade description
    body text. Its original 941 chars are missing ~76 common TC chars causing □.

    Mirrors _bake_tc_into_futura exactly. Returns 1 if changed, 0 if already done."""
    import numpy as np
    import freetype
    import tempfile

    nu_font_obj = nu_atlas_obj = nu_mat_obj = None
    for obj in env.objects:
        if   obj.path_id == NO_UNDERLAY_FONT_PATH_ID:  nu_font_obj  = obj
        elif obj.path_id == NO_UNDERLAY_ATLAS_PATH_ID: nu_atlas_obj = obj
        elif obj.path_id == NOTO_NU_MATERIAL_PID:      nu_mat_obj   = obj

    if not (nu_font_obj and nu_atlas_obj):
        print("  NotoNU bake: font/atlas not found — skipping.")
        return 0

    nu_tt    = nu_font_obj.read_typetree()
    atlas_tt = nu_atlas_obj.read_typetree()

    # Check if glyphs need re-baking: detect OUT_OF_BOUNDS indices from previous broken bake
    # (synthetic indices 200000+ pointing beyond GlyphTable length)
    glyph_table_len = len(nu_tt.get("m_GlyphTable", []))
    char_table = nu_tt.get("m_CharacterTable", [])
    has_broken_indices = any(
        c.get("m_GlyphIndex", -1) >= glyph_table_len or c.get("m_GlyphIndex", -1) >= 200000
        for c in char_table
    )
    
    # Idempotency: if atlas already extended AND has valid glyph indices, skip
    if (atlas_tt.get("m_Height", 0) >= NOTO_NU_NEW_H and 
        atlas_tt.get("m_Width", 0) >= NOTO_NU_NEW_W and
        not has_broken_indices):
        print(f"  NotoNU bake: atlas already {atlas_tt['m_Width']}×{atlas_tt['m_Height']} with valid indices — skipping.")
        return 0
    
    if has_broken_indices:
        print(f"  NotoNU bake: detected OUT_OF_BOUNDS glyph indices — forcing re-bake to fix")
        # Keep only original NotoNU glyphs, remove all baked TC entries with synthetic indices
        new_glyph_table = [g for g in nu_tt.get("m_GlyphTable", []) 
                          if g["m_Index"] < 200000]  # Remove synthetic indices 200000+
        kept_glyph_ids = {g["m_Index"] for g in new_glyph_table}
        new_char_table = [c for c in char_table if c.get("m_GlyphIndex", -1) in kept_glyph_ids]
        removed = len(char_table) - len(new_char_table)
        print(f"  NotoNU bake: keeping {len(new_char_table)} valid chars, removing {removed} broken entries")
        nu_tt["m_CharacterTable"] = new_char_table
        nu_tt["m_GlyphTable"] = new_glyph_table

    tc_needed    = _get_tc_chars_needed()
    existing_cps = {c["m_Unicode"] for c in nu_tt["m_CharacterTable"]}
    to_bake      = sorted(cp for cp in tc_needed if cp not in existing_cps)
    print(f"  NotoNU bake: existing {len(existing_cps)}, to bake {len(to_bake)} of {len(tc_needed)} TC chars")
    if not to_bake:
        return 0

    # When re-baking after removing broken entries, the atlas may already be extended
    # (2048×8192) from the previous broken bake. Extract just the original bottom portion
    # and re-bake the TC region.
    old_pixels = None
    stream_data = atlas_tt.get("m_StreamData", {})
    s_offset = stream_data.get("offset", 0) if stream_data else 0
    s_size   = stream_data.get("size",   0) if stream_data else 0
    
    if s_size > 0 and s_offset >= 0:
        from UnityPy.helpers.ResourceReader import EndianBinaryReader
        res_reader = env.file.files.get(_NOTO_NU_RES_S_KEY)
        if res_reader is not None:
            res_reader.Position = 0
            res_s_bytes = bytes(res_reader.read())
            # For streaming data, only read the first 2048×2048 (original size)
            if s_offset + (NOTO_NU_OLD_W * NOTO_NU_OLD_H) <= len(res_s_bytes):
                old_pixels = np.frombuffer(
                    res_s_bytes[s_offset:s_offset + (NOTO_NU_OLD_W * NOTO_NU_OLD_H)], 
                    dtype=np.uint8
                ).reshape(NOTO_NU_OLD_H, NOTO_NU_OLD_W)
    
    if old_pixels is None:
        inline = bytes(atlas_tt.get("image data", b"") or b"")
        # Handle both original (2048×2048) and re-bake (2048×8192) cases
        if len(inline) == NOTO_NU_OLD_W * NOTO_NU_OLD_H:
            # Original size
            old_pixels = np.frombuffer(inline, dtype=np.uint8).reshape(NOTO_NU_OLD_H, NOTO_NU_OLD_W)
        elif len(inline) == NOTO_NU_NEW_W * NOTO_NU_NEW_H:
            # Already extended — extract just the bottom original portion
            full_img = np.frombuffer(inline, dtype=np.uint8).reshape(NOTO_NU_NEW_H, NOTO_NU_NEW_W)
            old_pixels = full_img[:NOTO_NU_OLD_H, :NOTO_NU_OLD_W]
        else:
            print(f"  NotoNU bake: cannot read existing atlas pixels ({len(inline)} bytes, expected {NOTO_NU_OLD_W * NOTO_NU_OLD_H} or {NOTO_NU_NEW_W * NOTO_NU_NEW_H}) — skipping.")
            return 0

    # Build new 2048×8192 bottom-up image; existing data at rows[0..OLD_H-1]
    new_img = np.zeros((NOTO_NU_NEW_H, NOTO_NU_NEW_W), dtype=np.uint8)
    new_img[:NOTO_NU_OLD_H, :NOTO_NU_OLD_W] = old_pixels

    # Bake TC chars into region above (rows[OLD_H..NEW_H-1] in bottom-up coords)
    REGION_H = NOTO_NU_NEW_H - NOTO_NU_OLD_H   # 6144 rows
    REGION_W = NOTO_NU_NEW_W
    region   = np.zeros((REGION_H, REGION_W), dtype=np.uint8)

    with tempfile.NamedTemporaryFile(suffix=".ttf", delete=False) as tmp:
        tmp.write(bytes(noto_bytes))
        font_path = tmp.name
    try:
        face = freetype.Face(font_path)

        # Use real NotoSansCJKjp glyph IDs as unique identifiers; fall back to sequential
        # for codepoints not in NotoSansCJKjp or on collision. (mode=0 means no runtime
        # validation — glyph IDs just need to be unique within this font asset.)
        _used_gi = {g["m_Index"] for g in nu_tt["m_GlyphTable"]}
        _seq_gi  = (max(_used_gi) + 1) if _used_gi else 1

        ax = ay = row_h = 0
        new_chars, new_glyphs, new_used = [], [], []
        packed = skipped_invis = skipped_full = 0

        for cp in to_bake:
            # Allocate real NotoSansCJKjp glyph ID; fall back to sequential on collision/miss
            real_gi = face.get_char_index(cp)
            if real_gi == 0 or real_gi in _used_gi:
                while _seq_gi in _used_gi:
                    _seq_gi += 1
                real_gi = _seq_gi
                _seq_gi += 1
            _used_gi.add(real_gi)
            glyph_idx = real_gi

            sdf, gw, gh, metrics = _generate_sdf(face, cp, NOTO_NU_TC_POINT_SIZE,
                                                 NOTO_NU_TC_PADDING, NOTO_NU_TC_OVERSAMPLE)
            if sdf is None or gw == 0:
                new_chars.append({
                    "m_ElementType": 1, "m_Unicode": cp,
                    "m_GlyphIndex": glyph_idx, "m_Scale": 1.0,
                })
                new_glyphs.append({
                    "m_Index": glyph_idx,
                    "m_Metrics": {
                        "m_Width": 0.0, "m_Height": 0.0,
                        "m_HorizontalBearingX": 0.0, "m_HorizontalBearingY": 0.0,
                        "m_HorizontalAdvance": metrics["advance"],
                    },
                    "m_GlyphRect": {"m_X": 0, "m_Y": 0, "m_Width": 0, "m_Height": 0},
                    "m_Scale": 1.0, "m_AtlasIndex": 0, "m_ClassDefinitionType": 0,
                })
                skipped_invis += 1; continue

            full_w = gw + 2 * NOTO_NU_TC_PADDING
            full_h = gh + 2 * NOTO_NU_TC_PADDING
            if ax + full_w > REGION_W:
                ax = 0; ay += row_h; row_h = 0
            if ay + full_h > REGION_H:
                skipped_full = len(to_bake) - packed - skipped_invis
                print(f"  NotoNU bake: region full after {packed} chars — {skipped_full} skipped")
                break

            region[ay:ay+full_h, ax:ax+full_w] = sdf

            used_y_bu_bottom = (NOTO_NU_NEW_H - 1) - (ay + full_h - 1)
            glyph_x_bu = ax + NOTO_NU_TC_PADDING
            glyph_y_bu = used_y_bu_bottom + NOTO_NU_TC_PADDING

            new_used.append({
                "m_X": ax, "m_Y": used_y_bu_bottom,
                "m_Width": full_w, "m_Height": full_h,
            })
            new_chars.append({
                "m_ElementType": 1, "m_Unicode": cp,
                "m_GlyphIndex": glyph_idx, "m_Scale": 1.0,
            })
            new_glyphs.append({
                "m_Index": glyph_idx,
                "m_Metrics": {
                    "m_Width":  metrics["width"],
                    "m_Height": metrics["height"],
                    "m_HorizontalBearingX": metrics["bearingX"],
                    "m_HorizontalBearingY": metrics["bearingY"],
                    "m_HorizontalAdvance":  metrics["advance"],
                },
                "m_GlyphRect": {
                    "m_X": glyph_x_bu, "m_Y": glyph_y_bu,
                    "m_Width": gw, "m_Height": gh,
                },
                "m_Scale": 1.0, "m_AtlasIndex": 0, "m_ClassDefinitionType": 0,
            })
            ax += full_w
            row_h = max(row_h, full_h)
            packed += 1
    finally:
        try: os.unlink(font_path)
        except OSError: pass

    # Composite region (top-down) into new_img bottom-up rows[OLD_H..NEW_H-1]
    region_botup = np.flipud(region)
    new_img[NOTO_NU_OLD_H:NOTO_NU_NEW_H, :] = region_botup

    new_bytes = new_img.tobytes()
    assert len(new_bytes) == NOTO_NU_NEW_W * NOTO_NU_NEW_H

    # Convert streaming → inline (proven approach from _bake_tc_into_futura)
    atlas_tt["image data"]          = new_bytes
    atlas_tt["m_Width"]             = NOTO_NU_NEW_W
    atlas_tt["m_Height"]            = NOTO_NU_NEW_H
    atlas_tt["m_CompleteImageSize"] = len(new_bytes)
    atlas_tt["m_MipCount"]          = 1
    atlas_tt["m_StreamData"]        = {"offset": 0, "size": 0, "path": ""}
    nu_atlas_obj.save_typetree(atlas_tt)

    # Update font
    free_h_td = REGION_H - (ay + row_h)
    new_free  = ([{"m_X": 0, "m_Y": NOTO_NU_OLD_H, "m_Width": NOTO_NU_NEW_W, "m_Height": free_h_td}]
                 if free_h_td > 0 else [])

    nu_tt["m_AtlasWidth"]       = NOTO_NU_NEW_W
    nu_tt["m_AtlasHeight"]      = NOTO_NU_NEW_H
    # CRITICAL: Sort CharacterTable by Unicode value for binary search
    nu_tt["m_CharacterTable"]   = sorted(list(nu_tt["m_CharacterTable"]) + new_chars, 
                                         key=lambda c: c.get("m_Unicode", 0))
    nu_tt["m_GlyphTable"]       = list(nu_tt["m_GlyphTable"])     + new_glyphs
    nu_tt["m_UsedGlyphRects"]   = list(nu_tt.get("m_UsedGlyphRects", [])) + new_used
    nu_tt["m_FreeGlyphRects"]   = new_free
    nu_tt["m_FallbackFontAssetTable"] = []
    nu_tt["m_AtlasPopulationMode"]    = 0   # Static — NotoNU pre-baked inline atlas; mode=0 bypasses GID validation
    nu_tt["m_SourceFontFile"]         = {"m_FileID": 0, "m_PathID": 0}  # null — no source OTF means no TextCore runtime validation
    nu_font_obj.save_typetree(nu_tt)

    # Update Material _TextureWidth/_TextureHeight — CRITICAL: TMP uses these for UV normalisation.
    # Without this, glyphs in rows 2048..8191 map to UV > 1.0 and render as □.
    if nu_mat_obj is not None:
        mat_tt = nu_mat_obj.read_typetree()
        saved  = mat_tt.get("m_SavedProperties", {})
        floats = saved.get("m_Floats", [])
        upd_w = upd_h = False
        for i, entry in enumerate(floats):
            if isinstance(entry, (list, tuple)):
                key = entry[0]
                if key == "_TextureWidth":
                    floats[i] = (key, float(NOTO_NU_NEW_W)); upd_w = True
                elif key == "_TextureHeight":
                    floats[i] = (key, float(NOTO_NU_NEW_H)); upd_h = True
        if not upd_w: floats.append(("_TextureWidth",  float(NOTO_NU_NEW_W)))
        if not upd_h: floats.append(("_TextureHeight", float(NOTO_NU_NEW_H)))
        saved["m_Floats"] = floats
        mat_tt["m_SavedProperties"] = saved
        nu_mat_obj.save_typetree(mat_tt)
        print(f"  NotoNU bake: material _TextureWidth→{NOTO_NU_NEW_W} _TextureHeight→{NOTO_NU_NEW_H} (w={upd_w} h={upd_h})")
    else:
        print("  NotoNU bake: WARNING — material object not found, UV normalisation may be wrong!")

    print(f"  NotoNU bake: packed {packed} TC chars (invisible {skipped_invis}, skipped {skipped_full}). "
          f"Atlas {NOTO_NU_OLD_W}×{NOTO_NU_OLD_H} → {NOTO_NU_NEW_W}×{NOTO_NU_NEW_H} inline. "
          f"Char table: {len(nu_tt['m_CharacterTable'])} total, fallback stripped.")
    return 1


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    if not os.path.isfile(BUNDLE_DIST):
        print(f"ERROR: Bundle not found: {BUNDLE_DIST}", file=sys.stderr)
        sys.exit(1)

    print(f"Bundle: {BUNDLE_DIST}  ({os.path.getsize(BUNDLE_DIST):,} bytes)")
    env = UnityPy.load(BUNDLE_DIST)

    # WORKAROUND for UnityPy cache bug: dummy-save each font we will later mutate
    # to break the read-cache, otherwise save_typetree() silently drops the change.
    FUTURA_PATH_ID = 4996038291744176242
    _CACHE_BREAK_PIDS = {FUTURA_PATH_ID, GENERATED_FONT_PATH_ID, NO_UNDERLAY_FONT_PATH_ID,
                         NO_UNDERLAY_ATLAS_PATH_ID, NOTO_NU_MATERIAL_PID}
    for obj in env.objects:
        if obj.path_id in _CACHE_BREAK_PIDS:
            dummy_tt = obj.read_typetree()
            obj.save_typetree(dummy_tt)

    patched = 0

    # ── Step 0: DISABLED — Font substitution blocked TMP fallback.
    #    _substitute_futura_with_noto() added 44,810 fake chars with zero-pixel
    #    glyph rects to Futura. TMP found those chars in Futura's CharacterTable,
    #    tried Dynamic rasterization from Futura's source (no CJK), failed, and
    #    logged "not found" — without ever querying the fallback chain.
    #    TC is now baked directly into Futura's own atlas in Step 8 (proven path).
    n_subst = 0
    if n_subst > 0:
        patched += 1

    # ── Step 1: Ensure Generated font uses Static mode (pop=0) ──
    # Static mode preserves pre-baked CharacterTable at runtime.
    # Dynamic mode (pop=1) with source_pid=0 + GUID causes TMP to validate
    # m_GlyphIndex against the font binary; our sequential GIDs fail validation
    # → chars excluded from CharacterLookupDictionary (177 failures with mode=1).
    # mode=0 (Static) bypasses all validation → 118 failures (current best).
    gen_already_ok = False
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour" or obj.path_id != GENERATED_FONT_PATH_ID:
            continue
        tt = obj.read_typetree()
        changes = []

        # Static mode: use pre-baked data directly
        if tt.get("m_AtlasPopulationMode") != 0:
            tt["m_AtlasPopulationMode"] = 0
            changes.append("pop→0(Static)")

        if tt.get("m_IsMultiAtlasTexturesEnabled") != 0:
            tt["m_IsMultiAtlasTexturesEnabled"] = 0
            changes.append("multi_atlas→0")

        if changes:
            obj.save_typetree(tt)
            print(f"  NotoSansCJKjp-Regular SDF - No Underlay - Generated: {', '.join(changes)}")
            patched += 1
        else:
            print("  NotoSansCJKjp-Regular SDF - No Underlay - Generated: already correct, skipping.")
            gen_already_ok = True
        break

    # ── Step 2: Pre-bake missing TC chars into No Underlay atlas ──
    # Check if No Underlay already has pre-baked chars (idempotent)
    no_underlay_baked = False
    for obj in env.objects:
        if obj.type.name == "MonoBehaviour" and obj.path_id == NO_UNDERLAY_FONT_PATH_ID:
            tt = obj.read_typetree()
            ct = tt.get("m_CharacterTable", [])
            n_chars = len(ct)
            pop = tt.get("m_AtlasPopulationMode")

            if n_chars > 0 and pop == 0:
                # Check if elementType is already correct (1 = TextCore format)
                first_et = ct[0].get("m_ElementType", 0) if ct else 0
                if first_et == 1:
                    print(f"  NotoSansCJKjp-Regular SDF - No Underlay: already pre-baked correctly ({n_chars} chars), skipping.")
                    no_underlay_baked = True
                else:
                    # Fix wrong elementType in place (no need to re-bake atlas)
                    print(f"  NotoSansCJKjp-Regular SDF - No Underlay: fixing m_ElementType 0→1 for {n_chars} chars")
                    for e in ct:
                        e["m_ElementType"] = 1
                    # CRITICAL: Sort CharacterTable by Unicode value for binary search
                    tt["m_CharacterTable"] = sorted(ct, key=lambda c: c.get("m_Unicode", 0))
                    obj.save_typetree(tt)
                    patched += 1
                    no_underlay_baked = True
            break

    baked_tc_chars = []   # Will hold the 754 TC Character dicts for futura merge
    baked_tc_glyphs = []  # Will hold the 754 TC Glyph dicts for futura merge
    baked_atlas_bytes = b""  # Bottom-up Alpha8 pixels just written into NoUnderlay atlas

    if not no_underlay_baked:
        gen_chars    = _get_generated_chars(env)
        tc_needed    = _get_tc_chars_needed()
        missing      = sorted(tc_needed - gen_chars)
        print(f"  TC chars needed: {len(tc_needed)},  in Generated: {len(tc_needed & gen_chars)},  missing: {len(missing)}")

        noto_bytes   = _extract_noto_font_bytes(env)
        n, baked_tc_chars, baked_tc_glyphs, baked_atlas_bytes = _bake_chars_into_no_underlay(env, missing, noto_bytes)
        if n > 0:
            patched += 2   # atlas Texture2D + font MonoBehaviour
    else:
        # NoUnderlay was already baked (e.g., running patch again on dist).
        # Read the baked chars/glyphs from NoUnderlay for futura merge.
        for obj in env.objects:
            if obj.path_id == NO_UNDERLAY_FONT_PATH_ID:
                nu_tt = obj.read_typetree()
                baked_tc_chars = list(nu_tt.get("m_CharacterTable", []))
                baked_tc_glyphs = list(nu_tt.get("m_GlyphTable", []))
                break

    # ── Step 3: Attempt 5e — convert NoUnderlay atlas from inline to streaming.
    #    The inline Texture2D format is confirmed NOT to render in this Unity 6
    #    IL2CPP title.  Appending the pixel data to the .resS (same file that the
    #    Generated atlas streams from) makes it load identically to the confirmed-
    #    working Generated atlas.
    #
    #    With streaming NoUnderlay:
    #      futura → Generated [missing 754 chars] → NoUnderlay fallback [found,
    #      streaming atlas loads] → renders ✓
    n_streaming = _make_no_underlay_atlas_streaming(env, atlas_bytes_fresh=baked_atlas_bytes or None)
    if n_streaming > 0:
        patched += 1   # NoUnderlay atlas Texture2D + .resS

    # ── Step 4: Attempt 5g — repack ALL glyphs into a single new 4096×2048
    #    atlas[0].  Root cause of all prior failures (5b/5c/5e/5f): Unity 6
    #    IL2CPP TMP only samples atlas[0] because that is the only atlas with a
    #    pre-baked Material.  atlas[1] entries (even with multi-atlas enabled,
    #    even streaming) are ignored at render time.  Putting every char into a
    #    single atlas[0] is the only confirmed-working path in this title.
    n_repack = _repack_all_glyphs_into_new_atlas(
        env, nu_chars_fresh=baked_tc_chars or None, nu_glyphs_fresh=baked_tc_glyphs or None
    )
    if n_repack > 0:
        patched += 1

    # ── Step 6: Fix arbitrary high glyph indices (≥59000) to real NotoSansCJK IDs.
    #    For a Static TMP font with m_SourceFontFile set, Unity TextCore validates
    #    each m_GlyphIndex against the font binary at load time.  Chars whose
    #    stored index does not match the font file's glyph ID are silently excluded
    #    from the runtime CharacterLookupDictionary and never rendered.
    #    The original 3401 chars have correct IDs (e.g. 9831 for U+4E00).
    #    Our 754 added chars got sequential IDs (59000+) which TextCore rejects.
    #
    #    Skipped when Step 5g succeeds: 5g rebuilds the glyph table with clean
    #    sequential indices and already wrote the final state. Re-reading Generated
    #    here would hit the UnityPy cache (still pre-5g snapshot) and overwrite
    #    5g's larger char table with the original 3295 entries.
    if n_repack > 0:
        print("  Step 6: Skipped (Step 5g rewrote glyph indices).")
        n_fix = 0
    else:
        n_fix = _fix_glyph_indices_to_real_font_ids(env)
    if n_fix > 0:
        patched += 1

    # ── Step 7: DISABLED — futura merge was the bug.
    #    Prior strategy: copy TC chars from NoUnderlay into futura's m_CharacterTable
    #    with m_AtlasIndex=1 (NoUnderlay atlas as futura's atlas[1]), then clear futura's
    #    m_FallbackFontAssetTable. This failed silently because TMP only renders glyphs
    #    referencing atlas[0]; atlas[1]+ chars produce □.
    #    Correct behaviour: leave futura untouched so its original fallback chain
    #    [Generated, NoUnderlay, Roboto No Underlay] is preserved. Generated now has
    #    4236 chars including every TC codepoint we need, so all CJK lookups resolve
    #    via the fallback chain to a real atlas-index-0 glyph in Generated.
    n_futura = 0
    if n_futura > 0:
        patched += 1

    # ── Step 8: Bake TC directly into futura's own atlas[0].
    #    Fallback chain does NOT work in this Unity 6 IL2CPP title — confirmed by
    #    disabling this step: errors went from 152 (58 unique) → 635 (150 unique).
    #    TMP finds chars in a fallback's CharacterLookupDictionary but fails to
    #    render them when the primary font is Dynamic (mode=1) — the streaming
    #    atlas path for fallback fonts fails silently in this IL2CPP build.
    #    Proven fix: extend futura's atlas to 2048×8192, bake all TC chars using
    #    NotoSansCJKtc OTF glyph shapes (visual = NotoSans, not Futura).
    #    TC sits in futura's own lookup dict so TMP resolves it without fallback.
    #    Glyph indices MUST start at max(existing)+1=255 to avoid conflicts with
    #    original Latin glyph indices (range 3..254) — starting at len(table)=124
    #    caused 19 duplicate GlyphTable entries that corrupted GlyphLookupDictionary
    #    and caused 58 chars to silently fail at runtime.
    _ext_otf_path = os.path.join(REPO_ROOT, ".copilot_workspace", "NotoSansCJKtc-Regular.otf")
    if os.path.isfile(_ext_otf_path):
        with open(_ext_otf_path, "rb") as _otf_f:
            _futura_noto_bytes = _otf_f.read()
        print(f"  Step 8: Using external NotoSansCJKtc OTF ({len(_futura_noto_bytes):,} bytes)")
    else:
        try:
            _futura_noto_bytes = noto_bytes  # noqa: F821 — defined above in non-idempotent branch
        except NameError:
            _futura_noto_bytes = _extract_noto_font_bytes(env)
        print(f"  Step 8: External OTF not found, falling back to in-game Noto ({len(_futura_noto_bytes):,} bytes)")
    n_futura_bake = _bake_tc_into_futura(env, _futura_noto_bytes)
    if n_futura_bake > 0:
        patched += 1

    # DO NOT restore Futura fallbacks — font substitution already solved the problem
    # by making Futura's data identical to Noto's (see Step 0).
    # (This call was here but is no longer needed after Step 0 substitution runs first)
    # n_futura_fb = _restore_futura_fallbacks(env)
    # if n_futura_fb > 0:
    #     patched += 1

    # ── Step 9: Bake TC directly into NotoSansCJKjp-Regular SDF - No Underlay atlas[0].
    #    This font (pid=NO_UNDERLAY_FONT_PATH_ID, 941 chars, pop=0, streaming 2048×2048)
    #    is used for campaign/crusade description body text. Its original 941 chars are
    #    missing ~76 common TC chars (一不中之他但何使等...), causing description boxes to
    #    show □. Same inline-atlas bake approach as Step 8 (proven with futura).
    try:
        _noto_nu_bytes = noto_bytes  # noqa: F821 — defined above
    except NameError:
        _noto_nu_bytes = _extract_noto_font_bytes(env)
    n_noto_nu_bake = _bake_tc_into_noto_no_underlay(env, _noto_nu_bytes)
    if n_noto_nu_bake > 0:
        patched += 1

    # ── Step 10: Force futura to Noto tables/atlas (default ON) ──
    # User-facing stability mode for TC: keep UI references to futura intact,
    # but render with Noto No-Underlay glyph data directly.
    if os.environ.get("MOD_FORCE_NOTO_FUTURA", "1") == "1":
        n_force_noto = _force_futura_to_noto(env)
        if n_force_noto > 0:
            patched += 1
    else:
        print("  Step 10: Force Noto for futura disabled (MOD_FORCE_NOTO_FUTURA=0).")

    if patched == 0:
        print("No TMP font assets needed patching.")
        return

    print(f"\nPatched {patched} TMP font asset(s). Saving bundle...")

    env.file.dataflags       = type(env.file.dataflags)(579)
    env.file._block_info_flags = 64
    bundle_bytes = env.file.save(packer="original")

    with open(BUNDLE_DIST, "wb") as f:
        f.write(bundle_bytes)
    print(f"Bundle saved: {len(bundle_bytes):,} bytes")

    new_crc = zlib.crc32(bundle_bytes[BUNDLE_DATA_OFFSET:]) & 0xFFFFFFFF
    print(f"New bundle CRC32: 0x{new_crc:08X}")

    if not os.path.isfile(CATALOG_DIST):
        print(f"WARNING: catalog.bin not found at {CATALOG_DIST}, skipping CRC update.", file=sys.stderr)
        return

    catalog = bytearray(open(CATALOG_DIST, "rb").read())
    old_crc = struct.unpack_from("<I", catalog, CATALOG_CRC_OFFSET)[0]
    struct.pack_into("<I", catalog, CATALOG_CRC_OFFSET, new_crc)
    with open(CATALOG_DIST, "wb") as f:
        f.write(catalog)
    print(f"catalog.bin: CRC 0x{old_crc:08X} → 0x{new_crc:08X}")

    new_hash = hashlib.md5(catalog).hexdigest()
    with open(CATALOG_HASH_DIST, "w") as f:
        f.write(new_hash)
    print(f"catalog.hash: {new_hash}")


if __name__ == "__main__":
    main()
