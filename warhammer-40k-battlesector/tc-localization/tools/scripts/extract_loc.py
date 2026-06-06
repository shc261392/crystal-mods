#!/usr/bin/env python3
"""
extract_loc.py — Extract all language blocks from sharedassets1.assets.

Localization data lives in a single 6 MB MonoBehaviour (path_id=3644) inside
sharedassets1.assets.  It holds 8 languages × 4 content groups × 2 copies
= 64 contiguous string blocks in the order: pt-BR, zh-CN, fr-FR, de-DE,
ko-KR, pl-PL, ru-RU, es-ES.

Requires:
    pip install UnityPy

Usage:
    python3 tools/scripts/extract_loc.py

Output:
    translation/zh-TW/source/zh-CN/barks.txt    (Simplified Chinese)
    translation/zh-TW/source/zh-CN/missions.txt
    translation/zh-TW/source/zh-CN/ui.txt
    translation/zh-TW/source/zh-CN/units.txt
    translation/zh-TW/source/zh-TW/barks.txt    (TC baseline = copy of SC)
    ... (all 8 languages written; zh-TW is the editable TC copy)

Adjust ASSETS_FILE below if your Steam library is on a different drive.
"""

import os
import re
import shutil
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

DEFAULT_GAME_DIR = "/mnt/d/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector"
GAME_DIR        = os.environ.get("MOD_GAME_DIR", DEFAULT_GAME_DIR)
MOD_BACKUP_DIR  = os.environ.get("MOD_BACKUP_DIR", os.path.join(GAME_DIR, ".zh-tw-mod-backup"))

# Prefer the pristine backup when present (created by deploy.sh on first install).
_BACKUP_ASSETS = os.path.join(MOD_BACKUP_DIR, "Warhammer 40K Battlesector_Data", "sharedassets1.assets")
_GAME_ASSETS   = os.path.join(GAME_DIR,        "Warhammer 40K Battlesector_Data", "sharedassets1.assets")
ASSETS_FILE = _BACKUP_ASSETS if os.path.isfile(_BACKUP_ASSETS) else _GAME_ASSETS
LOC_PATH_ID = 3644

SOURCE_DIR = os.path.join(REPO_ROOT, "translation", "zh-TW", "source")

# Language slot order within each content group (index = slot number)
LANG_SLOTS = ["pt-BR", "zh-CN", "fr-FR", "de-DE", "ko-KR", "pl-PL", "ru-RU", "es-ES"]
NUM_LANGS = len(LANG_SLOTS)

# The 4 unique content groups (the MonoBehaviour stores them twice; we extract
# only the first copy — groups 5-8 are identical duplicates of groups 1-4).
GROUP_NAMES = ["barks", "missions", "ui", "units"]
NUM_GROUPS = len(GROUP_NAMES)

# Block boundary marker: end of one block's last entry + start of next block's entry 1
_BOUNDARY_RE = re.compile(rb"\|\r\n1\|")


def main() -> None:
    try:
        import UnityPy  # noqa: PLC0415
    except ImportError:
        print("ERROR: UnityPy is not installed.", file=sys.stderr)
        print("       Run:  pip install UnityPy", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(ASSETS_FILE):
        print(f"ERROR: Assets file not found:\n  {ASSETS_FILE}", file=sys.stderr)
        print("Edit ASSETS_FILE in this script to match your game install.", file=sys.stderr)
        sys.exit(1)

    print(f"Loading: {ASSETS_FILE}")
    env = UnityPy.load(ASSETS_FILE)

    obj = next((o for o in env.objects if o.path_id == LOC_PATH_ID), None)
    if obj is None:
        print(f"ERROR: MonoBehaviour path_id={LOC_PATH_ID} not found!", file=sys.stderr)
        sys.exit(1)

    raw = obj.get_raw_data()
    print(f"Raw data: {len(raw):,} bytes")

    boundaries = [m.start() for m in _BOUNDARY_RE.finditer(raw)]
    expected = NUM_LANGS * NUM_GROUPS * 2  # 2 copies
    if len(boundaries) != expected:
        print(
            f"WARNING: Expected {expected} block boundaries, found {len(boundaries)}.",
            file=sys.stderr,
        )
    print(
        f"Found {len(boundaries)} boundaries = "
        f"{len(boundaries) // NUM_LANGS} content groups × {NUM_LANGS} languages"
    )

    # Extract only the first copy (groups 0..NUM_GROUPS-1)
    for group_idx, group_name in enumerate(GROUP_NAMES):
        for lang_idx, lang_code in enumerate(LANG_SLOTS):
            block_idx = group_idx * NUM_LANGS + lang_idx
            next_block_idx = block_idx + 1

            # Each block spans from "1|..." of this block up to "1|..." of the next
            block_start = boundaries[block_idx] + 3   # skip |\r\n → lands on "1|"
            block_end = boundaries[next_block_idx] + 3

            block_bytes = raw[block_start:block_end]
            block_text = block_bytes.decode("utf-8", errors="replace")

            out_dir = os.path.join(SOURCE_DIR, lang_code)
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, f"{group_name}.txt")
            with open(out_path, "w", encoding="utf-8", newline="") as f:
                f.write(block_text)

            entry_count = block_text.count("\r\n")
            print(
                f"  {lang_code}/{group_name}.txt  "
                f"{len(block_bytes):,} bytes  {entry_count} entries"
            )

    # Create TC baseline: copy zh-CN → zh-TW
    print("\nCreating TC baseline (copying zh-CN → zh-TW)...")
    sc_dir = os.path.join(SOURCE_DIR, "zh-CN")
    tc_dir = os.path.join(SOURCE_DIR, "zh-TW")
    os.makedirs(tc_dir, exist_ok=True)
    for group_name in GROUP_NAMES:
        src = os.path.join(sc_dir, f"{group_name}.txt")
        dst = os.path.join(tc_dir, f"{group_name}.txt")
        shutil.copy2(src, dst)
        print(f"  zh-TW/{group_name}.txt  (TC baseline)")

    print(f"\nExtraction complete! All language files written to:\n  {SOURCE_DIR}")
    print("\nNext step:  python3 tools/scripts/build_patch.py")


if __name__ == "__main__":
    main()
