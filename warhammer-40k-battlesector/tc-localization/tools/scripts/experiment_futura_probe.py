#!/usr/bin/env python3
"""
DECISIVE DIAGNOSTIC EXPERIMENT (reversible — next deploy.sh restores everything).

Patches ONLY the already-deployed game bundle + catalog in place. Two probes
into the Futura TMP font ('futura medium condensed bt SDF - No Underlay'):

  Probe 1 — read-test:  Blank the glyph of existing Latin 'A' (U+0041) by pointing
            its glyph rect to an empty atlas corner (0,0,0,0).
            -> If 'A' renders BLANK in-game, Unity IS reading our edits to Futura's
               existing entries.  If 'A' renders normally, Unity is loading Futura
               from a source we have not modified.

  Probe 2 — glyph-index test:  Repoint the failing char 戰 (U+6230) from its
            synthetic glyph index 100782 to the small real glyph index 48 (the 'M'
            glyph, which has visible pixels in the original atlas region).
            -> If 戰 renders as 'M' (or any visible mark) in-game, the character IS
               present in Futura's runtime lookup and the ONLY problem was the
               synthetic 100000+ glyph index failing to resolve.
            -> If 戰 stays □, the character never made it into Futura's runtime
               character table (table-truncation / load problem).

Run:  python3 tools/scripts/experiment_futura_probe.py
Then: full restart the game, open a campaign description/title box, and report:
      (a) does 'A' look blank anywhere it appears?
      (b) does 戰 show an 'M' / any mark, or still □?
"""
import hashlib
import os
import struct
import zlib

import UnityPy

GAME_DIR = "/mnt/d/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector"
DATA_REL = "Warhammer 40K Battlesector_Data"
SA_REL = os.path.join(DATA_REL, "StreamingAssets")
BUNDLE_NAME = "unknownassets_assets_all_12cf1b4aeb7c9355f8487758e37a43d2.bundle"

BUNDLE_PATH = os.path.join(GAME_DIR, SA_REL, BUNDLE_NAME)
CATALOG_PATHS = [
    os.path.join(GAME_DIR, SA_REL, "catalog.bin"),
    os.path.join(GAME_DIR, SA_REL, "aa", "catalog.bin"),
]
CATALOG_HASH_PATHS = [
    os.path.join(GAME_DIR, SA_REL, "catalog.hash"),
    os.path.join(GAME_DIR, SA_REL, "aa", "catalog.hash"),
]

FUTURA_PID = 4996038291744176242
BUNDLE_DATA_OFFSET = 160
CATALOG_CRC_OFFSET = 173069


def main():
    print(f"Loading deployed bundle: {BUNDLE_PATH}")
    env = UnityPy.load(BUNDLE_PATH)

    futura_obj = None
    for obj in env.objects:
        if obj.path_id == FUTURA_PID:
            futura_obj = obj
            break
    if not futura_obj:
        raise SystemExit("Futura not found in deployed bundle")

    tt = futura_obj.read_typetree()
    chars = tt["m_CharacterTable"]
    glyphs = tt["m_GlyphTable"]
    cm = {c["m_Unicode"]: c for c in chars}
    gm = {g["m_Index"]: g for g in glyphs}

    # ── Probe 1: blank 'A' (U+0041) glyph rect ────────────────────────────────
    A = cm.get(0x41)
    if not A:
        raise SystemExit("'A' not in Futura char table")
    a_glyph = gm[A["m_GlyphIndex"]]
    print(f"Probe1: 'A' glyph {A['m_GlyphIndex']} old rect={a_glyph['m_GlyphRect']}")
    a_glyph["m_GlyphRect"] = {"m_X": 0, "m_Y": 0, "m_Width": 0, "m_Height": 0}
    print("Probe1: 'A' glyph rect -> (0,0,0,0) [blanked]")

    # ── Probe 2: repoint 戰 (U+6230) to real glyph index 48 ('M') ──────────────
    z = cm.get(0x6230)
    if not z:
        raise SystemExit("戰 not in Futura char table")
    print(f"Probe2: 戰 old glyph index = {z['m_GlyphIndex']}")
    z["m_GlyphIndex"] = 48  # 'M' real glyph index, visible pixels in orig region
    print("Probe2: 戰 glyph index -> 48 ('M')")

    futura_obj.save_typetree(tt)

    # Save bundle with the exact same flags patch_font.py uses
    env.file.dataflags = type(env.file.dataflags)(579)
    env.file._block_info_flags = 64
    bundle_bytes = env.file.save(packer="original")
    with open(BUNDLE_PATH, "wb") as f:
        f.write(bundle_bytes)
    print(f"Bundle written: {len(bundle_bytes):,} bytes")

    new_crc = zlib.crc32(bundle_bytes[BUNDLE_DATA_OFFSET:]) & 0xFFFFFFFF
    print(f"New bundle CRC32: 0x{new_crc:08X}")

    for cat_path in CATALOG_PATHS:
        cat = bytearray(open(cat_path, "rb").read())
        old = struct.unpack_from("<I", cat, CATALOG_CRC_OFFSET)[0]
        struct.pack_into("<I", cat, CATALOG_CRC_OFFSET, new_crc)
        with open(cat_path, "wb") as f:
            f.write(cat)
        h = hashlib.md5(cat).hexdigest()
        print(f"  {cat_path}: CRC 0x{old:08X} -> 0x{new_crc:08X}")
        # write matching hash next to it
    for hash_path in CATALOG_HASH_PATHS:
        # recompute from the catalog in the same dir
        cat_dir = os.path.dirname(hash_path)
        cat = open(os.path.join(cat_dir, "catalog.bin"), "rb").read()
        h = hashlib.md5(cat).hexdigest()
        with open(hash_path, "w") as f:
            f.write(h)
        print(f"  {hash_path}: {h}")

    print("\nDONE. Full-restart the game, open a campaign description/title box, and report:")
    print("  (a) Does 'A' appear BLANK wherever Latin 'A' shows?")
    print("  (b) Does 戰 show an 'M' / any visible mark, or is it still □?")


if __name__ == "__main__":
    main()
