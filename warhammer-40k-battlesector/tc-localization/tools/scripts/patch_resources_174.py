#!/usr/bin/env python3
"""
patch_resources_174.py — 1.7.4 (Unity 6) Traditional Chinese patcher.

In 1.7.4 the game reads localization from resources.assets as TextAssets named
`text_repository-<repo>[-external]_chinese` (Simplified). This script converts
those Simplified TextAssets to Traditional and writes a patched resources.assets
(plus its unchanged .resS sidecar) to the dist directory.

Method: byte-identical in-place replacement. OpenCC `s2tw` maps each Simplified
CJK char (3-byte UTF-8) to a single Traditional CJK char (also 3-byte UTF-8), so
every converted TextAsset keeps the exact same byte length. We locate each
script blob by its unique original bytes and swap in the converted bytes without
touching the serialized-file offset table. This avoids re-serializing the whole
Unity 6 assets file (which UnityPy 1.25 does not do reliably).

Usage:
    python3 tools/scripts/patch_resources_174.py

Env overrides:
    MOD_GAME_DIR    game install dir
    MOD_BACKUP_DIR  pristine backup dir (preferred source)
    MOD_DIST_DIR    output dir
"""
import os
import shutil
import sys

try:
    import UnityPy
except ImportError:
    print("ERROR: UnityPy not installed. pip install UnityPy", file=sys.stderr)
    sys.exit(1)

try:
    import opencc
except ImportError:
    print("ERROR: opencc-python-reimplemented not installed.", file=sys.stderr)
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

DEFAULT_GAME_DIR = "/mnt/d/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector"
GAME_DIR = os.environ.get("MOD_GAME_DIR", DEFAULT_GAME_DIR)
MOD_BACKUP_DIR = os.environ.get(
    "MOD_BACKUP_DIR", os.path.join(GAME_DIR, ".zh-tw-mod-backup")
)
DIST_DIR = os.environ.get(
    "MOD_DIST_DIR", os.path.join(REPO_ROOT, "translation", "zh-TW", "dist")
)

DATA_REL = "Warhammer 40K Battlesector_Data"
RESOURCES_NAME = "resources.assets"

_BACKUP_RES = os.path.join(MOD_BACKUP_DIR, DATA_REL, RESOURCES_NAME)
_GAME_RES = os.path.join(GAME_DIR, DATA_REL, RESOURCES_NAME)
SOURCE_RES = _BACKUP_RES if os.path.isfile(_BACKUP_RES) else _GAME_RES

# Simplified-Chinese TextAssets that must become Traditional.
CHINESE_ASSETS = {
    "text_repository-barks_chinese",
    "text_repository-campaign_chinese",
    "text_repository-campaign-external_chinese",
    "text_repository-default_chinese",
    "text_repository-default-external_chinese",
    "text_repository-units_chinese",
    "text_repository-units-external_chinese",
}

# s2tw: char-level Simplified -> Traditional (Taiwan variants), strictly 1:1 so
# byte length is preserved. Do NOT use s2twp (phrase conversion changes length),
# and do NOT post-process whitespace (that would also change byte length).
converter = opencc.OpenCC("s2tw")


def as_bytes(script) -> bytes:
    if isinstance(script, str):
        return script.encode("utf-8", "surrogateescape")
    return bytes(script)


def main() -> None:
    if not os.path.isfile(SOURCE_RES):
        print(f"ERROR: resources.assets not found:\n  {SOURCE_RES}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(DIST_DIR, exist_ok=True)
    out_res = os.path.join(DIST_DIR, RESOURCES_NAME)

    print(f"Source: {SOURCE_RES}")
    raw = bytearray(open(SOURCE_RES, "rb").read())

    # Read the script bytes for each Chinese TextAsset via UnityPy.
    env = UnityPy.load(SOURCE_RES)
    targets = {}
    for obj in env.objects:
        if obj.type.name != "TextAsset":
            continue
        d = obj.read()
        name = getattr(d, "m_Name", "") or ""
        if name in CHINESE_ASSETS:
            targets[name] = as_bytes(d.m_Script)

    missing = CHINESE_ASSETS - set(targets)
    if missing:
        print(f"WARNING: missing Chinese TextAssets: {sorted(missing)}", file=sys.stderr)

    patched = 0
    for name, orig in sorted(targets.items()):
        text = orig.decode("utf-8", "surrogateescape")
        converted = converter.convert(text)
        new = converted.encode("utf-8")
        if len(new) != len(orig):
            print(
                f"  ERROR {name}: byte length changed {len(orig)} -> {len(new)}; "
                f"aborting to avoid offset corruption.",
                file=sys.stderr,
            )
            sys.exit(2)

        idx = raw.find(orig)
        if idx < 0:
            print(f"  ERROR {name}: original bytes not found in file.", file=sys.stderr)
            sys.exit(3)
        if raw.find(orig, idx + 1) != -1:
            print(f"  ERROR {name}: original bytes not unique.", file=sys.stderr)
            sys.exit(4)

        raw[idx : idx + len(new)] = new
        cjk = sum(1 for ch in converted if "\u4e00" <= ch <= "\u9fff")
        print(f"  {name:45} @0x{idx:08x}  {len(orig):8,}B  cjk={cjk}")
        patched += 1

    with open(out_res, "wb") as f:
        f.write(raw)

    # Copy the unchanged .resS sidecar so the asset file resolves streamed data.
    src_ress = SOURCE_RES + ".resS"
    if os.path.isfile(src_ress):
        shutil.copy2(src_ress, out_res + ".resS")

    src_size = os.path.getsize(SOURCE_RES)
    out_size = os.path.getsize(out_res)
    changed = "unchanged" if src_size == out_size else "CHANGED!"
    print(f"\nPatched {patched}/{len(CHINESE_ASSETS)} TextAssets.")
    print(f"  Source size:  {src_size:,} bytes")
    print(f"  Output size:  {out_size:,} bytes  ({changed})")
    print(f"  Output: {out_res}")


if __name__ == "__main__":
    main()
