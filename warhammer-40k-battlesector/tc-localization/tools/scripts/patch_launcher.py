#!/usr/bin/env python3
"""
patch_launcher.py — Convert Launcher/Localization/stringsChinese.resx from SC→TC.

Reads the launcher's Chinese localization resource file, converts all Chinese
text values from Simplified Chinese to Traditional Chinese (Taiwan) using
OpenCC s2twp, and writes the result to dist/ for deployment.

Requires:
    pip install opencc-python-reimplemented

Usage:
    python3 tools/scripts/patch_launcher.py

Output:
    translation/zh-TW/dist/stringsChinese.resx

Deploy:
    cp translation/zh-TW/dist/stringsChinese.resx \
       "/mnt/d/.../Launcher/Localization/stringsChinese.resx"
"""

import os
import re
import sys
import shutil
import xml.etree.ElementTree as ET

try:
    import opencc
except ImportError:
    print("ERROR: opencc-python-reimplemented not installed. Run: pip install opencc-python-reimplemented", file=sys.stderr)
    sys.exit(1)

# ── Paths ──────────────────────────────────────────────────────────────────────

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT   = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

DEFAULT_GAME_DIR = "/mnt/d/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector"
GAME_DIR        = os.environ.get("MOD_GAME_DIR", DEFAULT_GAME_DIR)
MOD_BACKUP_DIR  = os.environ.get("MOD_BACKUP_DIR", os.path.join(GAME_DIR, ".zh-tw-mod-backup"))
DIST_DIR        = os.environ.get("MOD_DIST_DIR", os.path.join(REPO_ROOT, "translation", "zh-TW", "dist"))

LAUNCHER_REL = os.path.join("Launcher", "Localization", "stringsChinese.resx")
SOURCE_FILE  = os.path.join(MOD_BACKUP_DIR, LAUNCHER_REL)
DIST_FILE    = os.path.join(DIST_DIR, "stringsChinese.resx")

# ── OpenCC converter ───────────────────────────────────────────────────────────

converter = opencc.OpenCC("s2twp")

# ── Helpers ────────────────────────────────────────────────────────────────────

def is_chinese(text: str) -> bool:
    """Return True if text contains any CJK Unified Ideographs."""
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def convert_value(text: str) -> str:
    """Convert a single text string SC→TC; return unchanged if non-Chinese."""
    if not is_chinese(text):
        return text
    converted = converter.convert(text)
    # Some source strings contain accidental spacing within Chinese words.
    # Keep Latin spacing intact, but collapse spaces between CJK chars.
    converted = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", converted)
    return converted


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    if not os.path.exists(SOURCE_FILE):
        print(f"ERROR: Launcher backup not found:\n  {SOURCE_FILE}", file=sys.stderr)
        print("       Run tools/scripts/deploy.sh to initialise the backup.", file=sys.stderr)
        sys.exit(1)

    # Read raw XML bytes (preserve BOM/encoding declaration)
    with open(SOURCE_FILE, "rb") as fh:
        raw = fh.read()

    text = raw.decode("utf-8")

    # Replace <value>...</value> contents using regex so we don't need to
    # re-serialise the whole ElementTree (which would lose comments/whitespace).
    converted_count = 0
    unchanged_count = 0

    def replacer(m: re.Match) -> str:
        nonlocal converted_count, unchanged_count
        original = m.group(1)
        converted = convert_value(original)
        if converted != original:
            converted_count += 1
        else:
            unchanged_count += 1
        return f"<value>{converted}</value>"

    new_text = re.sub(r"<value>([^<]*)</value>", replacer, text)

    # String_LanguageNative: OpenCC would produce '簡體中文' (SC→TC script for
    # "Simplified Chinese"), but we need '繁體中文' (Traditional Chinese).
    new_text = re.sub(
        r'(<data name="String_LanguageNative"[^>]*>\s*<value>)[^<]*(</value>)',
        r'\1繁體中文\2',
        new_text,
    )

    # String_Language is the internal language name shown in the language selector;
    # leave it as "Chinese" (English name unchanged).

    os.makedirs(DIST_DIR, exist_ok=True)
    with open(DIST_FILE, "w", encoding="utf-8") as fh:
        fh.write(new_text)

    print(f"\nConverted {converted_count} values SC→TC, {unchanged_count} unchanged.")
    print(f"Output → {DIST_FILE}")

    # Show before/after for key entries
    print("\nKey value changes:")
    orig_vals = re.findall(r'<data name="([^"]+)"[^>]*>\s*<value>([^<]*)</value>', text)
    new_vals  = re.findall(r'<data name="([^"]+)"[^>]*>\s*<value>([^<]*)</value>', new_text)
    orig_map  = {k: v for k, v in orig_vals}
    new_map   = {k: v for k, v in new_vals}
    for key in orig_map:
        if orig_map[key] != new_map.get(key, orig_map[key]):
            print(f"  {key}: {orig_map[key]!r} → {new_map[key]!r}")


if __name__ == "__main__":
    main()
