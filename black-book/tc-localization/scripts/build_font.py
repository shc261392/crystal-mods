#!/usr/bin/env python3
"""Produce the font + charset that the Unity font-asset build consumes.

The game's own TMP fonts are static atlases baked from its Simplified text, so
they contain no glyphs for the characters that differ in Traditional Chinese.
We therefore ship our own Traditional serif: Noto Serif TC - the same Noto Serif
family as the game's "Noto Serif SC" CJK atlases, so the result looks native
rather than merely uniform.

Noto Serif TC is a variable font whose default instance is ExtraLight, so we
instantiate Regular (wght=400) before subsetting. The subset keeps the whole CJK
Unified Ideographs + Extension A blocks so dynamically composed strings cannot
hit tofu.

Outputs (gitignored; consumed by tools/unity-font/):
    tools/unity-font/Assets/Fonts/Iansui-Regular.ttf
    tools/unity-font/Assets/Fonts/charset.txt

Requires network access plus fonttools:
    pip install fonttools
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent
UNITY_ASSETS = SCRIPT_DIR / "tools" / "unity-font" / "Assets" / "Fonts"
SOURCE_SC = SCRIPT_DIR / "source" / "sc" / "StreamingAssets" / "Config"
PAYLOAD = SCRIPT_DIR / "payload" / "Black Book_Data" / "StreamingAssets" / "Config"

# Iansui (芫荽) - a Traditional Chinese face designed for zh-TW, SIL OFL.
# Chosen over Noto Serif TC because the game's own Chinese glyphs are Noto Serif
# SC, and mixing an SC and a TC cut of the same family still read as two fonts.
# Pinned so the build is reproducible.
FONT_URL = "https://github.com/ButTaiwan/iansui/releases/download/v1.020/iansui.zip"
CACHE = SCRIPT_DIR / ".cache" / "iansui"

try:
    from fontTools.ttLib import TTFont
    from fontTools.subset import Subsetter, Options
except ImportError:
    sys.exit("ERROR: pip install fonttools")


def fetch_font() -> Path:
    """Return the upstream Iansui-Regular.ttf, downloading it once."""
    cached = CACHE / "Iansui-Regular.ttf"
    if cached.exists():
        return cached

    CACHE.parent.mkdir(parents=True, exist_ok=True)
    archive = CACHE.parent / "iansui.zip"
    print(f"downloading Iansui -> {archive.relative_to(SCRIPT_DIR)}")
    urllib.request.urlretrieve(FONT_URL, archive)

    import zipfile
    with zipfile.ZipFile(archive) as zf:
        for name in zf.namelist():
            if name.endswith("Iansui-Regular.ttf"):
                zf.extract(name, CACHE)
                break
    archive.unlink(missing_ok=True)

    if not cached.exists():
        sys.exit("ERROR: Iansui-Regular.ttf not found inside the release archive")
    return cached


def collect_chars() -> set[str]:
    """Every character Black Book can actually display, plus a margin.

    Deliberately NOT the whole CJK block: at 24 pt with padding 5 an atlas holds
    a few thousand glyphs, and only Black Book's own text needs to render.
    Anything outside this set falls back to the game's fonts.
    """
    chars: set[str] = set()

    # The game's own Simplified source and our converted Traditional payload.
    for root in (SOURCE_SC, PAYLOAD):
        if root.is_dir():
            for path in root.rglob("config_zh.yaml"):
                chars.update(path.read_text(encoding="utf-8-sig"))

    # Dialogue and UI labels, which do NOT live in the config files.
    chars.update(chars_from_game_assets())

    # Latin, Cyrillic, punctuation and symbols the UI mixes in.
    for lo, hi in [(0x20, 0x7E), (0xA0, 0x24F), (0x400, 0x4FF),
                   (0x2000, 0x206F), (0x2190, 0x21FF), (0x25A0, 0x25FF),
                   (0x3000, 0x303F), (0xFE30, 0xFE4F), (0xFF00, 0xFFEF)]:
        chars.update(chr(c) for c in range(lo, hi + 1))

    return {c for c in chars if c.isprintable() or c == " "}


def dedupe_by_glyph(font: TTFont, chars: set[str]) -> set[str]:
    """Keep at most one codepoint per glyph.

    TMP 1.4.1 crashes with "An item with the same key has already been added"
    when two codepoints resolve to the same glyph index: TryAddGlyphsToTexture
    hands back that glyph once per codepoint and TMP then does a bare
    m_GlyphLookupDictionary.Add(glyphIndex, glyph) (TMP_FontAsset.cs:1246).
    Compatibility forms and fullwidth variants collide this way, so we keep the
    lowest codepoint per glyph - the others map to the identical glyph anyway.
    """
    cmap = font.getBestCmap()
    seen: set[str] = set()
    kept: set[str] = set()
    dropped: list[int] = []

    for cp in sorted(ord(c) for c in chars):
        glyph = cmap.get(cp)
        if glyph is None:
            dropped.append(cp)          # not in this font at all
            continue
        if glyph in seen:
            dropped.append(cp)          # same glyph as one we already kept
            continue
        seen.add(glyph)
        kept.add(chr(cp))

    print(f"  glyph dedupe: kept {len(kept):,}, dropped {len(dropped):,} "
          f"({sum(1 for c in dropped if cmap.get(c))} were shared-glyph duplicates)")
    return kept


def chars_from_game_assets() -> set[str]:
    """Characters used by the DialogueDatabase and TextTable.

    These are Dialogue System ScriptableObjects inside data.unity3d and hold
    ~25k Chinese strings that never appear in the config files. Optional: if the
    game or UnityPy is unavailable we fall back to the config/payload sets, and
    the game's own fonts still cover anything we miss.
    """
    game = Path("/mnt/d/SteamLibrary/steamapps/common/Black Book")
    data = game / "Black Book_Data" / "data.unity3d"
    if not data.exists():
        print("  (game not found; charset limited to config + payload)")
        return set()

    try:
        import UnityPy
    except ImportError:
        print("  (UnityPy not installed; charset limited to config + payload)")
        return set()

    cache = SCRIPT_DIR / ".cache" / "game-chars.txt"
    if cache.exists():
        return set(cache.read_text(encoding="utf-8"))

    print("  extracting characters from data.unity3d (this takes a minute)...")
    env = UnityPy.load(str(data))
    chars: set[str] = set()
    for obj in env.objects:
        if obj.path_id not in (71459, 71461):   # DialogueDatabase, TextTable
            continue
        body = obj.get_raw_data()
        for match in re.finditer(rb"[\xe0-\xef][\x80-\xbf]{2}"
                                 rb"(?:[\xe0-\xef][\x80-\xbf]{2}|[\x20-\x7e])*", body):
            try:
                chars.update(match.group().decode("utf-8"))
            except UnicodeDecodeError:
                pass

    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text("".join(sorted(chars)), encoding="utf-8")
    return chars


def main() -> int:
    UNITY_ASSETS.mkdir(parents=True, exist_ok=True)

    chars = collect_chars()
    charset_path = UNITY_ASSETS / "charset.txt"
    charset_path.write_text("".join(sorted(chars)), encoding="utf-8")
    print(f"charset: {len(chars):,} codepoints -> {charset_path.relative_to(SCRIPT_DIR)}")

    source = fetch_font()

    # Iansui ships as a static Regular, so unlike Noto Serif TC there is no
    # variable-font instance to instantiate.
    font = TTFont(str(source))
    names = {r.nameID: r.toUnicode() for r in font["name"].names if r.platformID == 3}
    print(f"  source family={names.get(1)!r} subfamily={names.get(2)!r}")

    # Must happen before subsetting, so the cmap still covers every codepoint.
    chars = dedupe_by_glyph(font, chars)
    charset_path.write_text("".join(sorted(chars)), encoding="utf-8")

    print("subsetting...")
    options = Options()
    options.name_IDs = ['*']
    options.name_legacy = True
    options.name_languages = ['*']
    options.notdef_outline = True
    options.recalc_bounds = True
    options.layout_features = ['*']
    options.drop_tables = ['BASE', 'vhea', 'vmtx', 'VORG']
    subsetter = Subsetter(options=options)
    subsetter.populate(text="".join(sorted(chars)))
    subsetter.subset(font)

    dest = UNITY_ASSETS / "Iansui-Regular.ttf"
    font.save(str(dest))
    print(f"  {dest.relative_to(SCRIPT_DIR)}  {dest.stat().st_size:,} bytes")

    check = TTFont(str(dest), lazy=True)
    cps: set[int] = set()
    for table in check["cmap"].tables:
        cps.update(table.cmap.keys())
    missing = [c for c in "說裡們沒這" if ord(c) not in cps]
    print(f"  cmap {len(cps):,} codepoints; sanity chars missing: {missing or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())