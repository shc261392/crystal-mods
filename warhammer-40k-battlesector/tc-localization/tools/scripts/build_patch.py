#!/usr/bin/env python3
"""
build_patch.py — Convert SC baseline to TC using OpenCC s2twp.

Reads SC source files from translation/zh-TW/source/zh-CN/,
converts each entry's text to Traditional Chinese (Taiwan),
and writes patched TC files to translation/zh-TW/patched/.

Requires:
    python3 tools/scripts/extract_loc.py  (run first to create source files)
    pip install --break-system-packages opencc-python-reimplemented

Usage:
    python3 tools/scripts/build_patch.py

Output (one file per content group):
    translation/zh-TW/patched/barks.txt
    translation/zh-TW/patched/missions.txt
    translation/zh-TW/patched/ui.txt
    translation/zh-TW/patched/units.txt

Algorithm
---------
Source format (SC baseline):   ID|text|\\r\\n
Conversion: OpenCC s2twp (Simplified → Traditional Chinese with Taiwan phrases)
"""

import os
import re
import sys

try:
    import opencc
except ImportError:
    print("ERROR: opencc-python-reimplemented not installed.", file=sys.stderr)
    print("Run: pip install --break-system-packages opencc-python-reimplemented", file=sys.stderr)
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

# SC baseline extracted from game
SOURCE_DIR = os.path.join(REPO_ROOT, "translation", "zh-TW", "source", "zh-CN")
OUT_DIR = os.path.join(REPO_ROOT, "translation", "zh-TW", "patched")

GROUP_NAMES = ["barks", "missions", "ui", "units"]

# Post-OpenCC terminology normalization for project-specific lore consistency.
# Keep this map tiny and explicit; each key/value should be fully intentional.
TERM_OVERRIDES: dict[str, str] = {
    "腥紅": "猩紅",
}

# Regex: ID|text| — text may contain no pipes
_ROW_RE = re.compile(r"^(\d+)\|([^|]*)\|?", re.MULTILINE)


def process_group(group_name: str, converter: "opencc.OpenCC") -> None:
    source_path = os.path.join(SOURCE_DIR, f"{group_name}.txt")
    if not os.path.exists(source_path):
        print(f"  SKIP {group_name}.txt (not found — run extract_loc.py first)", file=sys.stderr)
        return

    with open(source_path, encoding="utf-8", newline="") as f:
        source_text = f.read()

    rows = _ROW_RE.findall(source_text)

    out_rows: list[str] = []

    for row_id, sc_text in rows:
        tc_text = converter.convert(sc_text)
        for src, dst in TERM_OVERRIDES.items():
            tc_text = tc_text.replace(src, dst)
        out_rows.append(f"{row_id}|{tc_text}|")

    print(
        f"  {group_name}.txt: {len(rows):,} entries converted SC→TC"
    )

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, f"{group_name}.txt")
    # Use newline="" to write raw \r\n bytes without translation
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        f.write("\r\n".join(out_rows))
        f.write("\r\n")


def main() -> None:
    if not os.path.isdir(SOURCE_DIR):
        print(f"ERROR: Source dir not found: {SOURCE_DIR}", file=sys.stderr)
        print("Run extract_loc.py first.", file=sys.stderr)
        sys.exit(1)

    # s2twp: Simplified → Traditional Chinese with Taiwan phrases
    converter = opencc.OpenCC("s2twp")
    print("OpenCC s2twp converter loaded.")

    print(f"\nProcessing {len(GROUP_NAMES)} content groups...")
    for group_name in GROUP_NAMES:
        process_group(group_name, converter)

    print(f"\nPatched files written to:\n  {OUT_DIR}")
    print("\nNext step:  python3 tools/scripts/inject_loc.py")


if __name__ == "__main__":
    main()
