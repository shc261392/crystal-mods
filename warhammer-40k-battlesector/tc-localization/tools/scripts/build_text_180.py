#!/usr/bin/env python3
"""build_text_180.py — SC->TC text rebuild for Battlesector 1.8.0.

Loads a pristine resources.assets, converts the seven Chinese text repositories
(OpenCC s2tw -> glossary -> full-width punctuation) and writes the patched
resources.assets into translation/zh-TW/dist/. Always starts from vanilla, so
repeated builds are identical.

Env:
  MOD_VANILLA_RES  pristine resources.assets (default: live game)
  MOD_DIST_DIR     output dir (default: translation/zh-TW/dist)
"""
import os
import shutil
import sys

import opencc
import UnityPy
from UnityPy.helpers import TypeTreeHelper

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from convert_punctuation import convert as convert_punct  # noqa: E402

TypeTreeHelper.read_typetree_boost = False

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GAME = os.environ.get(
    "MOD_GAME_DIR", "/mnt/d/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector"
)
DEFAULT_VANILLA = os.path.join(
    GAME, "Warhammer 40K Battlesector_Data", "resources.assets"
)
VANILLA = os.environ.get("MOD_VANILLA_RES", DEFAULT_VANILLA)
DIST = os.environ.get("MOD_DIST_DIR", os.path.join(REPO, "translation", "zh-TW", "dist"))
GLOSSARY = os.path.join(REPO, "translation", "zh-TW", "glossary.tsv")

CHINESE = {
    "text_repository-barks_chinese",
    "text_repository-campaign_chinese",
    "text_repository-campaign-external_chinese",
    "text_repository-default_chinese",
    "text_repository-default-external_chinese",
    "text_repository-units_chinese",
    "text_repository-units-external_chinese",
}


def load_glossary(path):
    rules = []
    if not os.path.isfile(path):
        return rules
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line or line.lstrip().startswith("#") or "\t" not in line:
            continue
        search, replace = line.split("\t", 1)
        if search:
            rules.append((search, replace))
    return rules


def main():
    if not os.path.isfile(VANILLA):
        sys.exit(f"ERROR: vanilla resources.assets not found: {VANILLA}")
    os.makedirs(DIST, exist_ok=True)

    s2tw = opencc.OpenCC("s2tw")
    glossary = load_glossary(GLOSSARY)
    print(f"glossary rules: {len(glossary)}")

    env = UnityPy.load(VANILLA)
    changed = 0
    for o in env.objects:
        if o.type.name != "TextAsset":
            continue
        d = o.read()
        name = getattr(d, "m_Name", "")
        if name not in CHINESE:
            continue
        s = d.m_Script
        raw = s.encode("utf-8", "surrogateescape") if isinstance(s, str) else bytes(s)
        text = raw.decode("utf-8", "replace")
        new = s2tw.convert(text)
        for search, replace in glossary:
            new = new.replace(search, replace)
        new = convert_punct(new)
        d.m_Script = new
        o.save_typetree(d)
        changed += 1
        print(f"  {name} (pid {o.path_id}): {len(raw):,} -> {len(new.encode('utf-8')):,} bytes")

    out = os.path.join(DIST, "resources.assets")
    with open(out, "wb") as f:
        f.write(env.file.save())
    print(f"wrote {changed} repositories -> {out} ({os.path.getsize(out):,} B)")

    # A pristine copy for cross-checks / future diffs.
    ref = os.path.join(REPO, ".agent_workspace", "vanilla-1.8.0", "resources.assets")
    os.makedirs(os.path.dirname(ref), exist_ok=True)
    if not os.path.exists(ref):
        shutil.copy2(VANILLA, ref)
        print(f"kept pristine reference: {ref}")


if __name__ == "__main__":
    main()
