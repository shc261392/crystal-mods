#!/usr/bin/env python3
"""
patch_mapbuilder_font.py — Patch TMP font asset in mapbuildertools_assets_all.bundle
for TC support.

ROOT CAUSE:
  mapbuildertools_assets_all.bundle is a non-Addressable bundle loaded early in the
  game's boot sequence.  Its NotoSansCJKjp-Regular SDF font has:
    m_SourceFontFile = {fileID:2, pathID:-951123113223942216}   ← cross-bundle ref
    m_FallbackFontAssetTable = [{fileID:2, pid:7178690147649604500}]  ← cross-bundle
  The referenced objects live in the unknownassets Addressable bundle which loads
  *after* mapbuildertools.  Unity resolves PPtr references at deserialization time,
  so both source-font and fallback come back null.  The SC glyphs already baked into
  the two atlas textures still render fine; only the missing TC glyphs fail → boxes.

FIX (Attempt 3 – local source font):
  • Extract NotoSansCJKjp-Regular font binary from the deployed unknownassets bundle.
  • Replace LiberationSans Font (pid=-1618862201301623692) m_FontData with the NotoSansCJK
    binary.  LiberationSans is a safe target:
      – LiberationSans SDF (pop=0 static) already has all needed Latin glyphs baked.
      – LiberationSans SDF - Fallback (pop=1) uses LiberationSans as its source; after
        replacement it would use NotoSansCJK — that is fine, Noto covers Latin too.
  • Change NotoSansCJKjp-Regular SDF's m_SourceFontFile to the now-local font:
      {fileID:0, pathID:-1618862201301623692}
  • Clear the external fallback (was No Underlay from unknownassets) to avoid null-ref.
  • Leave the SC baked atlas and char/glyph tables untouched so existing SC glyphs
    continue to render from pre-baked data.  TMP will add TC glyphs at runtime into
    the atlas free space using the now-local NotoSansCJK font.

PREVIOUS FAILED ATTEMPTS (logged for reference):
  Attempt 1: blank atlas + clear tables + complete=0
    → ALL chars fail (complete=0 means TMP can't allocate runtime texture buffer).
  Attempt 2: blank atlas + clear tables + complete=4194304
    → SC chars also fail (pre-baked data gone; cross-bundle src still null → all boxes).

The mapbuildertools bundle has no hash suffix and is NOT tracked in catalog.bin, so
no CRC or catalog update is required.
"""

import os
import sys

import UnityPy

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

DEFAULT_GAME_DIR = "/mnt/d/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector"
GAME_DIR        = os.environ.get("MOD_GAME_DIR", DEFAULT_GAME_DIR)
MOD_BACKUP_DIR  = os.environ.get("MOD_BACKUP_DIR", os.path.join(GAME_DIR, ".zh-tw-mod-backup"))
DIST_DIR        = os.environ.get("MOD_DIST_DIR", os.path.join(REPO_ROOT, "translation/zh-TW/dist"))

SA_REL = os.path.join("Warhammer 40K Battlesector_Data", "StreamingAssets")

MAPBUILDER_BUNDLE_CANDIDATES = [
    "mapbuilder-tools_assets_all.bundle",
    "mapbuildertools_assets_all.bundle",
]
UA_BUNDLE_CANDIDATES = [
    "startup_assets_all.bundle",
    "unknownassets_assets_all_12cf1b4aeb7c9355f8487758e37a43d2.bundle",
]


def _resolve_bundle_name(candidates: list[str]) -> str:
    for candidate in candidates:
        if os.path.isfile(os.path.join(DIST_DIR, candidate)):
            return candidate
        if os.path.isfile(os.path.join(MOD_BACKUP_DIR, SA_REL, candidate)):
            return candidate
        if os.path.isfile(os.path.join(GAME_DIR, SA_REL, candidate)):
            return candidate
    return candidates[0]


BUNDLE_NAME = _resolve_bundle_name(MAPBUILDER_BUNDLE_CANDIDATES)
UA_BUNDLE_NAME = _resolve_bundle_name(UA_BUNDLE_CANDIDATES)

# Read the pristine mapbuildertools bundle from the installation backup so
# repeated runs always start from the original game data.
BUNDLE_SRC  = os.path.join(MOD_BACKUP_DIR, SA_REL, BUNDLE_NAME)
BUNDLE_DIST = os.path.join(DIST_DIR, BUNDLE_NAME)

UA_DIST = os.path.join(DIST_DIR, UA_BUNDLE_NAME)

# NotoSansCJKjp-Regular Font object (binary) in unknownassets bundle
NOTO_FONT_PID = -951123113223942216

# LiberationSans Font object in mapbuildertools (will carry NotoSansCJK data)
LIBERATION_FONT_PID = -1618862201301623692

# NotoSansCJKjp-Regular SDF TMP font in mapbuildertools (the one that renders CJK text)
NOTO_TMP_FONT_PID = -3782840183126329981

# Atlas[0] Texture2D for the NotoSansCJKjp-Regular SDF font in mapbuildertools
NOTO_ATLAS0_PID   = -760500969631156861

# Material that samples the atlas (its _TextureWidth/_TextureHeight must match)
NOTO_MATERIAL_PID = -4966807468849662589

# Bake parameters (must match m_FaceInfo / m_AtlasPadding of the TMP font)
MB_POINT_SIZE = 35
MB_PADDING    = 5
MB_OVERSAMPLE = 4

# Atlas size: original is 2048x2048, we extend vertically to 2048x4096.
# Existing baked SC glyphs live in the BOTTOM half (Y_bu = 0..2047) and stay valid.
# Newly baked TC glyphs go into the TOP half (Y_bu = 2048..4095).
MB_ATLAS_W    = 2048
MB_ATLAS_H_OLD = 2048
MB_ATLAS_H_NEW = 4096


def _repair_mapbuilder_sdf_references(env) -> int:
    """Repair TMP SDF source/fallback references in mapbuildertools to local-only.

    mapbuildertools frequently carries cross-bundle references (fileID=2) to
    unknownassets font objects that are not guaranteed to be resolved at the
    time mapbuildertools is deserialised. Those unresolved references cause
    runtime fallback collapse and tofu even when glyphs exist in local atlases.

    This pass enforces:
      - Dynamic SDF fonts use a local source font object
      - External fallback entries (fileID!=0 or missing local PathID) are removed
      - A local Noto TMP fallback is present for non-Noto SDF fonts

    Returns number of patched font assets.
    """
    patched = 0
    local_pids = {o.path_id for o in env.objects}

    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue

        try:
            tt = obj.read_typetree()
        except Exception:
            continue

        name = tt.get("m_Name", "")
        if not (isinstance(name, str) and "SDF" in name):
            continue

        # CRITICAL: skip the primary Noto TMP font here.
        # It has just been baked/extended in _bake_tc_into_mapbuilder(); re-reading
        # typetree in this pass can return a stale pre-bake snapshot and overwrite
        # the baked Character/Glyph tables when save_typetree() is called.
        if obj.path_id == NOTO_TMP_FONT_PID:
            continue

        changes = []

        pop_mode = tt.get("m_AtlasPopulationMode", 0)
        src = tt.get("m_SourceFontFile", {})
        src_fid = src.get("m_FileID", 0) if isinstance(src, dict) else 0
        src_pid = src.get("m_PathID", 0) if isinstance(src, dict) else 0

        # Dynamic fonts must have a resolvable local source to avoid null font-file.
        if pop_mode == 1 and (src_fid != 0 or src_pid not in local_pids):
            tt["m_SourceFontFile"] = {"m_FileID": 0, "m_PathID": LIBERATION_FONT_PID}
            changes.append("source→local liberation")

        fb = tt.get("m_FallbackFontAssetTable", []) or []
        cleaned_fb = []
        for e in fb:
            if not isinstance(e, dict):
                continue
            fid = e.get("m_FileID", 0)
            pid = e.get("m_PathID", 0)
            if fid == 0 and pid in local_pids:
                cleaned_fb.append({"m_FileID": 0, "m_PathID": pid})

        if len(cleaned_fb) != len(fb):
            tt["m_FallbackFontAssetTable"] = cleaned_fb
            changes.append(f"fallbacks cleaned {len(fb)}→{len(cleaned_fb)}")

        # Ensure non-Noto SDF fonts can fall back to the local Noto TMP font.
        if obj.path_id != NOTO_TMP_FONT_PID:
            cur_fb = tt.get("m_FallbackFontAssetTable", []) or []
            cur_pids = {e.get("m_PathID", 0) for e in cur_fb if isinstance(e, dict)}
            if NOTO_TMP_FONT_PID not in cur_pids:
                cur_fb.append({"m_FileID": 0, "m_PathID": NOTO_TMP_FONT_PID})
                tt["m_FallbackFontAssetTable"] = cur_fb
                changes.append("+fallback NotoTMP")

        if changes:
            obj.save_typetree(tt)
            print(f"  TMP SDF '{name}' (pid={obj.path_id}): {', '.join(changes)}")
            patched += 1

    return patched


def _bake_tc_into_mapbuilder(env, noto_bytes: bytes) -> int:
    """Extend atlas[0] from 2048x2048 to 2048x4096 and pre-bake TC chars into the
    new top half. Existing SC pre-baked data and tables are preserved (we only
    append). Returns number of TC chars baked."""
    import numpy as np
    import freetype
    import tempfile

    # Import shared helpers from patch_font.py
    sys.path.insert(0, os.path.dirname(__file__))
    from patch_font import _generate_sdf, _get_tc_chars_needed  # type: ignore

    tc_needed = _get_tc_chars_needed()
    print(f"  TC chars needed (patched + resources.assets scan): {len(tc_needed)}")
    if not tc_needed:
        print("  Nothing to bake; skipping atlas extension.")
        return 0

    # Find the TMP font and atlas objects
    font_obj = None
    atlas_obj = None
    mat_obj = None
    for obj in env.objects:
        if obj.path_id == NOTO_TMP_FONT_PID:
            font_obj = obj
        elif obj.path_id == NOTO_ATLAS0_PID:
            atlas_obj = obj
        elif obj.path_id == NOTO_MATERIAL_PID:
            mat_obj = obj
    if not (font_obj and atlas_obj and mat_obj):
        print("ERROR: Could not locate TMP font / atlas / material in mapbuildertools.", file=sys.stderr)
        sys.exit(1)

    font_tt  = font_obj.read_typetree()
    atlas_tt = atlas_obj.read_typetree()
    mat_tt   = mat_obj.read_typetree()

    # Skip chars already in the table (the existing atlas has 2518 chars incl. some TC)
    existing_cps = {c["m_Unicode"] for c in font_tt["m_CharacterTable"]}
    to_bake = sorted(cp for cp in tc_needed if cp not in existing_cps)
    print(f"  Already in atlas: {len(tc_needed) - len(to_bake)};  to bake: {len(to_bake)}")
    if not to_bake:
        print("  All TC chars already baked; skipping atlas extension.")
        return 0

    # Read existing atlas[0] image data (bottom-up Alpha8). It might be in StreamData.
    img_data = atlas_tt.get("image data", b"")
    sd = atlas_tt.get("m_StreamData", {})
    if (not img_data) and sd.get("size", 0) > 0 and sd.get("path"):
        # Resolve from .resS (not expected for mapbuildertools but safe)
        print(f"ERROR: atlas[0] image data is in external StreamData '{sd.get('path')}' — "
              "extension not implemented for that case.", file=sys.stderr)
        sys.exit(1)
    if len(img_data) != MB_ATLAS_W * MB_ATLAS_H_OLD:
        print(f"ERROR: atlas[0] image data size {len(img_data)} != "
              f"{MB_ATLAS_W * MB_ATLAS_H_OLD} (Alpha8 2048x2048 expected).", file=sys.stderr)
        sys.exit(1)
    existing_botup = bytes(img_data)

    # Bake TC chars into a fresh 2048x2048 region (top-down, shelf-packed)
    with tempfile.NamedTemporaryFile(suffix=".ttf", delete=False) as tmp:
        tmp.write(bytes(noto_bytes))
        font_path = tmp.name
    try:
        face = freetype.Face(font_path)
        region = np.zeros((MB_ATLAS_H_OLD, MB_ATLAS_W), dtype=np.uint8)

        # Pick a fresh glyph-index range that doesn't collide with existing ones
        max_idx = max((g["m_Index"] for g in font_tt["m_GlyphTable"]), default=0)
        glyph_idx = max(max_idx + 1, 100000)

        ax, ay, row_h = 0, 0, 0
        new_chars, new_glyphs, new_used = [], [], []
        packed = 0; skipped_invis = 0; skipped_full = 0

        for cp in to_bake:
            sdf, gw, gh, metrics = _generate_sdf(face, cp, MB_POINT_SIZE, MB_PADDING, MB_OVERSAMPLE)

            if sdf is None or gw == 0:
                # Invisible / whitespace — still register so TMP doesn't try Dynamic gen
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
                glyph_idx += 1
                skipped_invis += 1
                continue

            full_w = gw + 2 * MB_PADDING
            full_h = gh + 2 * MB_PADDING

            if ax + full_w > MB_ATLAS_W:
                ax = 0; ay += row_h; row_h = 0
            if ay + full_h > MB_ATLAS_H_OLD:
                skipped_full = len(to_bake) - packed - skipped_invis
                print(f"  WARNING: new region full after {packed} chars — {skipped_full} skipped")
                break

            region[ay:ay+full_h, ax:ax+full_w] = sdf

            # Bottom-up Y inside region (region height = MB_ATLAS_H_OLD = 2048)
            used_y_bu_in_region = MB_ATLAS_H_OLD - (ay + full_h)
            # Region sits on top of the original atlas → +MB_ATLAS_H_OLD offset
            used_y_bu_full = MB_ATLAS_H_OLD + used_y_bu_in_region
            glyph_x_bu = ax + MB_PADDING
            glyph_y_bu = used_y_bu_full + MB_PADDING

            new_used.append({
                "m_X": ax, "m_Y": used_y_bu_full,
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
            glyph_idx += 1
            packed += 1
    finally:
        try: os.unlink(font_path)
        except OSError: pass

    # Convert top-down region to bottom-up bytes, then prepend existing data
    # (existing occupies Y_bu = 0..2047, region occupies Y_bu = 2048..4095)
    region_botup = np.flipud(region).tobytes()
    new_image_data = existing_botup + region_botup
    assert len(new_image_data) == MB_ATLAS_W * MB_ATLAS_H_NEW, len(new_image_data)

    # Free-rect for the unused tail of the top region (top-down y > ay+row_h)
    free_y_top_in_region = ay + row_h
    free_h_bu = MB_ATLAS_H_OLD - free_y_top_in_region  # Y_bu range 2048..2048+free_h_bu
    new_free = (
        [{"m_X": 0, "m_Y": MB_ATLAS_H_OLD, "m_Width": MB_ATLAS_W, "m_Height": free_h_bu}]
        if free_h_bu > 0 else []
    )

    # ── Update Texture2D (atlas[0]) ──
    atlas_tt["image data"]          = new_image_data
    atlas_tt["m_Width"]             = MB_ATLAS_W
    atlas_tt["m_Height"]            = MB_ATLAS_H_NEW
    atlas_tt["m_CompleteImageSize"] = len(new_image_data)
    atlas_tt["m_MipCount"]          = 1
    atlas_tt["m_StreamData"]        = {"offset": 0, "size": 0, "path": ""}
    atlas_obj.save_typetree(atlas_tt)

    # ── Update TMP font ──
    font_tt["m_AtlasHeight"] = MB_ATLAS_H_NEW
    font_tt["m_CharacterTable"] = font_tt["m_CharacterTable"] + new_chars
    # TMP runtime lookup uses binary search; keep CharacterTable sorted.
    font_tt["m_CharacterTable"].sort(key=lambda c: c.get("m_Unicode", 0))
    font_tt["m_GlyphTable"]     = font_tt["m_GlyphTable"]     + new_glyphs
    
    # ── Reassign ALL glyph indices sequentially (CRITICAL FIX for 3722+ out-of-bounds indices) ──
    # The original mapbuildertools NotoSansCJKjp font has 3722 characters with synthetic
    # indices (100000+, 100001+, ...) that exceed GlyphTable bounds (3806 entries).
    # This causes TMP glyph lookup to fail with "was not found in font or any potential fallbacks".
    # Solution: Rebuild entire GlyphTable with sequential indices 0, 1, 2, ..., N-1.
    all_glyphs = font_tt.get("m_GlyphTable", [])
    old_to_new_glyph_idx = {}
    updated_glyphs = []
    seq_idx = 0
    for g in all_glyphs:
        old_gi = g.get("m_Index", -1)
        ng = dict(g)
        ng["m_Index"] = seq_idx
        old_to_new_glyph_idx[old_gi] = seq_idx
        updated_glyphs.append(ng)
        seq_idx += 1
    
    # Update all character entries to use new sequential indices
    updated_chars = []
    for c in font_tt.get("m_CharacterTable", []):
        nc = dict(c)
        old_idx = c.get("m_GlyphIndex", -1)
        if old_idx in old_to_new_glyph_idx:
            nc["m_GlyphIndex"] = old_to_new_glyph_idx[old_idx]
        updated_chars.append(nc)
    
    font_tt["m_GlyphTable"]      = updated_glyphs
    # CRITICAL: Sort CharacterTable by Unicode value for binary search lookup
    font_tt["m_CharacterTable"]  = sorted(updated_chars, key=lambda c: c.get("m_Unicode", 0))
    font_tt["m_UsedGlyphRects"] = font_tt.get("m_UsedGlyphRects", []) + new_used
    # Replace free rects with our extended-area free rect; the original FreeRects
    # were 1-pixel slivers in the bottom half (atlas was full) — useless to keep.
    font_tt["m_FreeGlyphRects"] = new_free
    # Re-assert local source/fallback policy here as well. This function reads
    # typetree again and can otherwise overwrite Step 4's reference fix.
    font_tt["m_SourceFontFile"] = {"m_FileID": 0, "m_PathID": LIBERATION_FONT_PID}
    font_tt["m_FallbackFontAssetTable"] = []
    font_tt["m_AtlasPopulationMode"] = 1
    font_tt["m_IsMultiAtlasTexturesEnabled"] = 1
    font_obj.save_typetree(font_tt)

    # ── Update Material ──
    mt = mat_tt
    saved = mt.get("m_SavedProperties", {})
    floats = saved.get("m_Floats", [])
    updated_w = updated_h = False
    for i, entry in enumerate(floats):
        if isinstance(entry, (list, tuple)):
            key = entry[0]
            if key == "_TextureWidth":
                floats[i] = (key, float(MB_ATLAS_W)); updated_w = True
            elif key == "_TextureHeight":
                floats[i] = (key, float(MB_ATLAS_H_NEW)); updated_h = True
        elif isinstance(entry, dict):
            key = entry.get("first", entry.get("key"))
            if key == "_TextureWidth":
                if "first" in entry: entry["second"] = float(MB_ATLAS_W)
                else: entry["value"] = float(MB_ATLAS_W)
                updated_w = True
            elif key == "_TextureHeight":
                if "first" in entry: entry["second"] = float(MB_ATLAS_H_NEW)
                else: entry["value"] = float(MB_ATLAS_H_NEW)
                updated_h = True
    saved["m_Floats"] = floats
    mt["m_SavedProperties"] = saved
    mat_obj.save_typetree(mt)
    print(f"  Material _TextureWidth→{MB_ATLAS_W} _TextureHeight→{MB_ATLAS_H_NEW} (w={updated_w} h={updated_h})")

    print(f"  Baked: {packed} visible TC + {skipped_invis} invisible (total {len(new_chars)})")
    print(f"  Atlas extended: {MB_ATLAS_W}x{MB_ATLAS_H_OLD} -> {MB_ATLAS_W}x{MB_ATLAS_H_NEW}")
    return len(new_chars)


def main() -> None:
    for path, label in [(BUNDLE_SRC, "Backup mapbuildertools bundle"), (UA_DIST, "Dist unknownassets bundle")]:
        if not os.path.isfile(path):
            print(f"ERROR: {label} not found: {path}", file=sys.stderr)
            print("       Run tools/scripts/deploy.sh from a clean game state to initialise the backup.", file=sys.stderr)
            sys.exit(1)

    os.makedirs(DIST_DIR, exist_ok=True)

    # ── Step 1: Extract NotoSansCJK font binary from unknownassets dist bundle ──
    print(f"Loading unknownassets dist bundle: {UA_DIST}")
    env_ua = UnityPy.load(UA_DIST)
    noto_font_data: bytes = b""
    for obj in env_ua.objects:
        if obj.path_id == NOTO_FONT_PID:
            tt = obj.read_typetree()
            noto_font_data = tt.get("m_FontData", b"")
            print(f"  Extracted NotoSansCJK font binary: {len(noto_font_data):,} bytes")
            break
    if not noto_font_data:
        print("ERROR: NotoSansCJK Font object not found in unknownassets bundle.", file=sys.stderr)
        sys.exit(1)

    # ── Step 2: Load mapbuildertools from installation backup ──
    print(f"\nLoading backup mapbuildertools bundle: {BUNDLE_SRC}  ({os.path.getsize(BUNDLE_SRC):,} bytes)")
    env = UnityPy.load(BUNDLE_SRC)

    patched = 0

    for obj in env.objects:
        # ── Step 3: Replace LiberationSans Font data with NotoSansCJK ──
        if obj.type.name == "Font" and obj.path_id == LIBERATION_FONT_PID:
            tt = obj.read_typetree()
            orig_len = len(tt.get("m_FontData", b""))
            print(f"  Font '{tt.get('m_Name')}' (pid={obj.path_id}): replacing "
                  f"{orig_len:,} bytes with NotoSansCJK {len(noto_font_data):,} bytes")
            tt["m_FontData"] = noto_font_data
            obj.save_typetree(tt)
            patched += 1
            continue

        # ── Step 4: Patch NotoSansCJKjp-Regular SDF TMP font ──
        if obj.type.name == "MonoBehaviour" and obj.path_id == NOTO_TMP_FONT_PID:
            tt = obj.read_typetree()
            changes = []

            # Point source font to the now-local LiberationSans Font object
            # (which now contains NotoSansCJK data) — avoids cross-bundle timing issue
            old_src = tt.get("m_SourceFontFile")
            new_src = {"m_FileID": 0, "m_PathID": LIBERATION_FONT_PID}
            if old_src != new_src:
                tt["m_SourceFontFile"] = new_src
                changes.append(f"src {old_src} → local(pid={LIBERATION_FONT_PID})")

            # Remove the external fallback (was No Underlay from unknownassets) to
            # prevent a null-ref from an unresolved cross-bundle PPtr at runtime.
            old_fallback = tt.get("m_FallbackFontAssetTable", [])
            if old_fallback:
                tt["m_FallbackFontAssetTable"] = []
                changes.append(f"cleared {len(old_fallback)} external fallback(s)")

            # Ensure Dynamic population mode
            if tt.get("m_AtlasPopulationMode") != 1:
                tt["m_AtlasPopulationMode"] = 1
                changes.append("pop→1(Dynamic)")

            # Ensure multi-atlas enabled
            if tt.get("m_IsMultiAtlasTexturesEnabled") != 1:
                tt["m_IsMultiAtlasTexturesEnabled"] = 1
                changes.append("multi_atlas→1")

            if changes:
                obj.save_typetree(tt)
                print(f"  TMP font '{tt.get('m_Name')}' (pid={obj.path_id}): {', '.join(changes)}")
                print(f"    Chars in atlas: {len(tt.get('m_CharacterTable', []))}  (SC pre-baked, untouched)")
                patched += 1
            else:
                print(f"  TMP font '{tt.get('m_Name')}': already correct, skipping.")

    if patched == 0:
        print("WARNING: No assets patched — check path IDs.", file=sys.stderr)
        sys.exit(1)

    # ── Step 5: Extend atlas vertically and pre-bake TC chars into the new top half ──
    # The original 2048x2048 atlas is full (FreeRects are 1-pixel slivers), so even
    # with a TC-capable source font Dynamic gen has nowhere to put new TC glyphs.
    print("\nExtending atlas and pre-baking TC chars...")
    _bake_tc_into_mapbuilder(env, noto_font_data)

    print("\nRepairing TMP SDF local references (post-bake)...")
    repaired = _repair_mapbuilder_sdf_references(env)
    if repaired:
        print(f"  Reference repair updated {repaired} TMP font asset(s)")

    print(f"\nPatched {patched} asset(s). Saving bundle to dist...")

    # Same flags as unknownassets bundle (dataflags=579 / 0x243, _block_info_flags=64)
    env.file.dataflags = type(env.file.dataflags)(579)
    env.file._block_info_flags = 64

    bundle_bytes = env.file.save(packer="original")
    with open(BUNDLE_DIST, "wb") as f:
        f.write(bundle_bytes)
    print(f"Bundle saved: {BUNDLE_DIST}  ({len(bundle_bytes):,} bytes)")
    # No catalog update needed — mapbuildertools has no hash suffix


if __name__ == "__main__":
    main()
