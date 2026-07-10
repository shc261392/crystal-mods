#!/usr/bin/env python3
"""
inject_loc.py — Inject patched TC localization into sharedassets1.assets.

Localization lives in MonoBehaviour path_id=3644 (sharedassets1.assets).
The data has 8 language slots in this order per content group:
    [0] pt-BR  [1] zh-CN  [2] fr-FR  [3] de-DE
    [4] ko-KR  [5] pl-PL  [6] ru-RU  [7] es-ES

By default, this script replaces the **Simplified Chinese (zh-CN)** slot with
the patched Traditional Chinese translation.  In-game, select "Chinese" to
display Traditional Chinese.

Requires:
    pip install UnityPy
    python3 tools/scripts/build_patch.py  (run first)

Usage:
    python3 tools/scripts/inject_loc.py [--slot SLOT_INDEX]

    SLOT_INDEX  Which language slot to overwrite (default: 1 = zh-CN).
                Options: 0=pt-BR 1=zh-CN 2=fr-FR 3=de-DE 4=ko-KR 5=pl-PL 6=ru-RU 7=es-ES

Output:
    translation/zh-TW/dist/sharedassets1.assets  (ready to deploy)
    translation/zh-TW/dist/<bundle>.bundle, catalog.bin, catalog.hash

Deploy:
    cp translation/zh-TW/dist/sharedassets1.assets \\
       "/mnt/d/.../Warhammer 40K Battlesector_Data/sharedassets1.assets"

Adjust ASSETS_FILE below if your Steam library is on a different drive.
"""

import argparse
import binascii
import hashlib
import os
import re
import shutil
import struct
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

DEFAULT_GAME_DIR = "/mnt/d/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector"
GAME_DIR        = os.environ.get("MOD_GAME_DIR", DEFAULT_GAME_DIR)
MOD_BACKUP_DIR  = os.environ.get("MOD_BACKUP_DIR", os.path.join(GAME_DIR, ".zh-tw-mod-backup"))

GAME_DATA_REL = "Warhammer 40K Battlesector_Data"
SA_REL        = os.path.join(GAME_DATA_REL, "StreamingAssets")

BUNDLE_CANDIDATES = [
    "startup_assets_all.bundle",
    "unknownassets_assets_all_12cf1b4aeb7c9355f8487758e37a43d2.bundle",
]


def _resolve_bundle_filename() -> str:
    for candidate in BUNDLE_CANDIDATES:
        backup_candidate = os.path.join(MOD_BACKUP_DIR, SA_REL, candidate)
        game_candidate = os.path.join(GAME_DIR, SA_REL, candidate)
        if os.path.isfile(backup_candidate) or os.path.isfile(game_candidate):
            return candidate
    return BUNDLE_CANDIDATES[0]


BUNDLE_FILENAME = _resolve_bundle_filename()
LOC_PATH_ID = 3644

# All inputs come from the installation backup (pristine originals).
ASSETS_FILE       = os.path.join(MOD_BACKUP_DIR, GAME_DATA_REL, "sharedassets1.assets")
BUNDLE_FILE       = os.path.join(MOD_BACKUP_DIR, SA_REL, BUNDLE_FILENAME)
CATALOG_FILE      = os.path.join(MOD_BACKUP_DIR, SA_REL, "aa", "catalog.bin")
CATALOG_HASH_FILE = os.path.join(MOD_BACKUP_DIR, SA_REL, "aa", "catalog.hash")
ENABLE_CATALOG_PATCH = os.environ.get("MOD_ENABLE_CATALOG_PATCH", "0") == "1"

# UnityFS data block starts after 16-byte-aligned blocks_info; for this bundle
# the data block begins at file offset 160.  Unity computes CRC32 over these bytes.
BUNDLE_DATA_OFFSET = 160

PATCHED_DIR = os.path.join(REPO_ROOT, "translation", "zh-TW", "patched")
DIST_DIR    = os.environ.get("MOD_DIST_DIR", os.path.join(REPO_ROOT, "translation", "zh-TW", "dist"))


LANG_SLOTS = ["pt-BR", "zh-CN", "fr-FR", "de-DE", "ko-KR", "pl-PL", "ru-RU", "es-ES"]
NUM_LANGS = len(LANG_SLOTS)

GROUP_NAMES = ["barks", "missions", "ui", "units"]
NUM_GROUPS = len(GROUP_NAMES)

_BOUNDARY_RE = re.compile(rb"\|\r\n1\|")

# No slots are hard-protected; the user chooses which language to replace.
_PROTECTED_SLOTS: set[int] = set()


def _apply_tc_blocks(
    raw: bytearray,
    boundaries: list[int],
    target_slot: int,
    tc_content: dict[str, bytes],
    num_copies: int,
    file_label: str = "",
) -> tuple[int, int]:
    """Replace zh-CN blocks with TC in-place. Returns (total_trimmed, total_padded)."""
    total_trimmed = 0
    total_padded = 0
    slot_name = LANG_SLOTS[target_slot]
    TERMINATOR = b"|\r\n"

    for copy_idx in range(num_copies):
        for group_idx, group_name in enumerate(GROUP_NAMES):
            block_idx = (copy_idx * NUM_GROUPS + group_idx) * NUM_LANGS + target_slot
            block_start = boundaries[block_idx] + 3
            block_end = boundaries[block_idx + 1] + 3
            orig_len = block_end - block_start

            tc_bytes = bytearray(tc_content[group_name])
            tc_len = len(tc_bytes)

            assert tc_bytes[-3:] == TERMINATOR, \
                f"{group_name}: expected |\\r\\n at end, got {tc_bytes[-3:]!r}"

            if tc_len == orig_len:
                payload = bytes(tc_bytes)
            elif tc_len < orig_len:
                shortage = orig_len - tc_len
                payload = bytes(tc_bytes[:-3]) + b"\x00" * shortage + TERMINATOR
                total_padded += shortage
            else:
                cut_pos = orig_len - 3
                while cut_pos > 0 and (tc_bytes[cut_pos] & 0xC0) == 0x80:
                    cut_pos -= 1
                null_fill = (orig_len - 3) - cut_pos
                payload = bytes(tc_bytes[:cut_pos]) + b"\x00" * null_fill + TERMINATOR
                total_trimmed += (tc_len - orig_len)

            raw[block_start:block_end] = payload

            diff = tc_len - orig_len
            prefix = f"[{file_label}] " if file_label else ""
            print(
                f"  {prefix}Copy{copy_idx + 1} {group_name}: "
                f"replaced {slot_name} ({orig_len:,}B) → TC ({tc_len:,}B) "
                f"Δ={diff:+d}B"
                + (f"  [trimmed {diff}B]" if diff > 0 else "")
                + (f"  [padded {-diff}B]" if diff < 0 else "")
            )

    return total_trimmed, total_padded


def _patch_catalog(bundle_raw: bytearray, dist_dir: str) -> None:
    """Update the CRC32 entry for the patched bundle in catalog.bin and regenerate catalog.hash.

    Unity computes CRC32 over the bundle's raw data block (bytes BUNDLE_DATA_OFFSET onward)
    and compares it to the value stored in catalog.bin.  After patching the bundle we must
    update that stored CRC32, then rewrite catalog.hash (MD5 of catalog.bin).
    """
    if not os.path.exists(CATALOG_FILE):
        print("  NOTE: catalog.bin not found — skipping catalog CRC patch.")
        return

    new_crc = binascii.crc32(bundle_raw[BUNDLE_DATA_OFFSET:]) & 0xFFFFFFFF
    new_crc_le = struct.pack("<I", new_crc)

    with open(CATALOG_FILE, "rb") as fh:
        catalog = bytearray(fh.read())

    # Find the old CRC in the vicinity of the bundle name entry.
    bundle_name = BUNDLE_FILENAME.encode()
    name_pos = catalog.find(bundle_name)
    if name_pos == -1:
        print("  WARNING: bundle name not found in catalog.bin — cannot patch CRC.", file=sys.stderr)
        return

    # Search for any 4-byte value in a window around the name entry that will
    # be replaced; we look for a uint32 that does NOT match the new CRC (i.e. it
    # IS the old CRC).  The old CRC is whatever was there before.
    window_start = name_pos
    window_end = min(name_pos + 300, len(catalog) - 3)
    # The CRC appears roughly 120–160 bytes after the bundle name in the catalog.
    # Scan for the first 4-byte value in that range that differs from the new CRC.
    old_crc_pos: int | None = None
    for i in range(window_start, window_end):
        val = struct.unpack_from("<I", catalog, i)[0]
        if val != 0 and val != new_crc and catalog[i : i + 4] != b"\xff\xff\xff\xff":
            # Heuristic: CRC32 values are typically in [0x10000000, 0xFFFFFFFF].
            # Skip ASCII runs (they'd look like small values).
            if val > 0x10000000:
                old_crc_pos = i
                old_crc_val = val
                break

    # More reliable: search for exactly 1 occurrence of the known-bad (old) value.
    # We know the old CRC was embedded; let's find it precisely.
    # Re-read catalog fresh to find the exact old CRC bytes.
    # Actually, search for any 4-byte LE value > 0x10000000 starting from
    # 100 bytes after the name (where the AssetBundleRequestOptions data lives).
    # Use the distinct pattern: after the 32-char hex hash string.
    hex_hash_pattern = b"2781ae29253f6c5ed449290299cfd05f"
    hash_pos = catalog.find(hex_hash_pattern, name_pos)
    if hash_pos != -1:
        # CRC is a few bytes after the hash string (skip 2 uint32 offsets then CRC)
        after_hash = hash_pos + len(hex_hash_pattern)
        # Skip \xd1\xa3\x02\x00 and \xe5\xa3\x02\x00 (8 bytes of catalog offsets)
        crc_pos = after_hash + 8
        old_crc_pos = crc_pos
        old_crc_val = struct.unpack_from("<I", catalog, crc_pos)[0]

    if old_crc_pos is None:
        print("  WARNING: cannot locate CRC32 field in catalog.bin — skipping.", file=sys.stderr)
        return

    print(f"  Catalog CRC32: 0x{old_crc_val:08X} → 0x{new_crc:08X}  (offset {old_crc_pos})")
    catalog[old_crc_pos : old_crc_pos + 4] = new_crc_le

    # Save updated catalog.bin to dist/
    dist_catalog = os.path.join(dist_dir, "catalog.bin")
    with open(dist_catalog, "wb") as fh:
        fh.write(catalog)

    # Regenerate catalog.hash (MD5 of catalog.bin)
    new_md5 = hashlib.md5(bytes(catalog)).hexdigest()
    dist_hash = os.path.join(dist_dir, "catalog.hash")
    with open(dist_hash, "w") as fh:
        fh.write(new_md5)

    print(f"  Saved catalog.bin → {dist_catalog}")
    print(f"  New catalog MD5: {new_md5} → {dist_hash}")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Inject TC patch into sharedassets1.assets and StreamingAssets bundle")
    parser.add_argument(
        "--slot",
        type=int,
        default=1,
        help=(
            "Language slot index to replace with TC (default: 1 = zh-CN). "
            "Options: 0=pt-BR 1=zh-CN 2=fr-FR 3=de-DE 4=ko-KR 5=pl-PL 6=ru-RU 7=es-ES"
        ),
    )
    args = parser.parse_args()
    target_slot = args.slot

    if target_slot not in range(NUM_LANGS):
        print(f"ERROR: --slot must be 0..{NUM_LANGS - 1}", file=sys.stderr)
        sys.exit(1)

    try:
        import UnityPy  # noqa: PLC0415
    except ImportError:
        print("ERROR: UnityPy is not installed.  Run:  pip install UnityPy", file=sys.stderr)
        sys.exit(1)

    # Verify all patched files exist
    missing = [
        g for g in GROUP_NAMES
        if not os.path.exists(os.path.join(PATCHED_DIR, f"{g}.txt"))
    ]
    if missing:
        print(f"ERROR: Missing patched files: {missing}", file=sys.stderr)
        print("Run build_patch.py first.", file=sys.stderr)
        sys.exit(1)

    # Load TC content
    tc_content: dict[str, bytes] = {}
    for group_name in GROUP_NAMES:
        p = os.path.join(PATCHED_DIR, f"{group_name}.txt")
        with open(p, "r", encoding="utf-8", newline="") as f:
            tc_content[group_name] = f.read().encode("utf-8")
        print(f"Loaded patched/{group_name}.txt: {len(tc_content[group_name]):,} bytes")

    if not os.path.exists(ASSETS_FILE):
        print(f"ERROR: Backup sharedassets1.assets not found:\n  {ASSETS_FILE}", file=sys.stderr)
        print("       Run tools/scripts/deploy.sh to initialise the installation backup.", file=sys.stderr)
        sys.exit(1)

    print(f"\nLoading: {ASSETS_FILE}")
    env = UnityPy.load(ASSETS_FILE)

    obj = next((o for o in env.objects if o.path_id == LOC_PATH_ID), None)
    if obj is None:
        print(f"ERROR: MonoBehaviour path_id={LOC_PATH_ID} not found!", file=sys.stderr)
        sys.exit(1)

    raw_original = bytes(obj.get_raw_data())
    blob_size = len(raw_original)
    print(f"Raw data: {blob_size:,} bytes")

    raw = bytearray(raw_original)
    boundaries = [m.start() for m in _BOUNDARY_RE.finditer(raw)]
    expected = NUM_LANGS * NUM_GROUPS * 2
    if len(boundaries) != expected:
        print(
            f"WARNING: Expected {expected} block boundaries, found {len(boundaries)}",
            file=sys.stderr,
        )

    num_copies = len(boundaries) // (NUM_GROUPS * NUM_LANGS)
    slot_name = LANG_SLOTS[target_slot]
    print(
        f"\nReplacing slot {target_slot} ({slot_name}) with TC "
        f"across {num_copies} copies × {NUM_GROUPS} content groups..."
    )

    # Replace each block so that its byte length is EXACTLY the same as the
    # original.  This avoids any data shifting after replacements, which could
    # corrupt internal offsets within the blob (e.g. font-atlas glyph tables
    # that share the same MonoBehaviour object).
    #
    # Strategy per block:
    #   TC < original → pad TC with null bytes at the end
    #   TC > original → trim TC to fit (trimmed bytes come from trailing content
    #                   of the last entry; trim to a valid UTF-8 boundary first)
    #
    # Because every block stays the same size, no size_delta tracking is needed
    # and the total blob size is unchanged.
    total_trimmed, total_padded = _apply_tc_blocks(
        raw, boundaries, target_slot, tc_content, num_copies
    )

    if total_trimmed:
        print(f"\n  ⚠  Total TC bytes trimmed to fit: {total_trimmed:,}")
    if total_padded:
        print(f"  Total null-pad bytes added:       {total_padded:,}")
    print(f"\nBlob size unchanged: {blob_size:,} bytes")

    # ── Pure binary patch ──────────────────────────────────────────────────
    # Read the whole file, locate the MonoBehaviour blob, overwrite it, write
    # the result.  UnityPy's save() is NOT called — it was rewriting too much
    # of the file structure and producing a corrupt asset.
    with open(ASSETS_FILE, "rb") as fh:
        file_bytes = bytearray(fh.read())

    # Locate the blob in the file.  Try header-derived offset first.
    abs_offset: int | None = None
    try:
        sf = env.files[ASSETS_FILE]
        candidate = sf.reader.data_offset + obj.byte_start
        if file_bytes[candidate : candidate + 32] == raw_original[:32]:
            abs_offset = candidate
    except Exception:
        pass

    if abs_offset is None:
        # Fallback: binary search using a 64-byte needle from raw data
        needle = raw_original[:64]
        found = file_bytes.find(needle)
        if found == -1:
            print("ERROR: Cannot locate MonoBehaviour blob in file.", file=sys.stderr)
            sys.exit(1)
        abs_offset = found
        print(f"  (located blob via binary search at offset {abs_offset:,})")

    file_bytes[abs_offset : abs_offset + blob_size] = raw

    os.makedirs(DIST_DIR, exist_ok=True)
    dist_path = os.path.join(DIST_DIR, "sharedassets1.assets")
    print(f"Saving patched assets → {dist_path}")
    with open(dist_path, "wb") as fh:
        fh.write(file_bytes)

    orig_size = os.path.getsize(ASSETS_FILE)
    new_size = os.path.getsize(dist_path)
    print(f"\nOriginal: {orig_size:,} bytes")
    print(f"Patched:  {new_size:,} bytes  (Δ: {new_size - orig_size:+d})")
    if new_size != orig_size:
        print("WARNING: File size changed — this should not happen with in-place patching.",
              file=sys.stderr)

    print(f"\nDone (sharedassets1.assets)!")

    # ── Patch StreamingAssets bundle ───────────────────────────────────────
    # The bundle overrides sharedassets1.assets at runtime and also contains
    # SC localization in the same 64-block structure.  Patch it the same way.
    if os.path.exists(BUNDLE_FILE):
        print(f"\n{'─'*60}")
        print(f"Patching StreamingAssets bundle...")

        print(f"  Loading bundle ({os.path.getsize(BUNDLE_FILE):,} bytes)...")
        with open(BUNDLE_FILE, "rb") as fh:
            bundle_raw = bytearray(fh.read())

        bundle_bounds = [m.start() for m in _BOUNDARY_RE.finditer(bundle_raw)]
        print(f"  Bundle boundary count: {len(bundle_bounds)} (expected {NUM_LANGS * NUM_GROUPS * 2})")
        if len(bundle_bounds) != NUM_LANGS * NUM_GROUPS * 2:
            print("  WARNING: Unexpected boundary count — skipping bundle patch.", file=sys.stderr)
        else:
            bundle_copies = len(bundle_bounds) // (NUM_GROUPS * NUM_LANGS)
            bt, bp = _apply_tc_blocks(
                bundle_raw, bundle_bounds, target_slot, tc_content, bundle_copies, "bundle"
            )
            if bt:
                print(f"  ⚠  Bundle TC bytes trimmed: {bt:,}")
            if bp:
                print(f"  Bundle null-pad bytes added: {bp:,}")

            bundle_dist = os.path.join(DIST_DIR, BUNDLE_FILENAME)
            print(f"  Saving patched bundle → {bundle_dist}")
            with open(bundle_dist, "wb") as fh:
                fh.write(bundle_raw)

            print(f"  Bundle size: {len(bundle_raw):,} bytes (unchanged)")

            # Catalog patching is disabled by default because incorrect binary
            # offsets can corrupt catalog.bin and hard-freeze startup.
            if ENABLE_CATALOG_PATCH:
                print(f"\n  Patching catalog CRC32...")
                _patch_catalog(bundle_raw, DIST_DIR)
            else:
                print("\n  Skipping catalog patch (MOD_ENABLE_CATALOG_PATCH!=1).")
                print("  deploy.sh will use pristine catalog.bin/catalog.hash from backup.")
    else:
        print(f"\nNOTE: Bundle not found at expected path — skipping bundle patch.")
        print(f"  {BUNDLE_FILE}")

    print(f"\nAll done. dist/ now holds the patched assets, bundle, catalog.bin and catalog.hash.")
    print(f"deploy.sh will copy them into the game directory.")


if __name__ == "__main__":
    main()
