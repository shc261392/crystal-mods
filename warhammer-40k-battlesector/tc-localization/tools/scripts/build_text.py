#!/usr/bin/env python3
"""
build_text.py — Reproducible Traditional-Chinese text build.

For each of the 7 Chinese TextAssets it takes the vanilla (Simplified) script and
applies, in order:
  1. OpenCC s2tw          Simplified -> Traditional (char-level, 1:1, no phrase
                          errors like s2twp's 重装 -> 重灌)
  2. glossary corrections translation/zh-TW/glossary.tsv (lore terms + fixes)
  3. punctuation          half-width -> full-width CJK punctuation (convert_punctuation)

It writes one serialized TextAsset MonoBehaviour per repo to OUT_DIR/text_<pid>.bin,
plus manifest.txt (pid<TAB>bin). A FontTool `replace` step (build.sh) swaps these
into resources.assets. Building always from vanilla keeps the result idempotent.

Env:
  MOD_VANILLA_RES  path to vanilla resources.assets
                   (default: .copilot_workspace/vanilla-1.7.7/<data>/resources.assets)
  MOD_TEXT_OUT     output subdir under .build (default: text)
"""
import os
import sys

import opencc
from UnityPy.helpers import TypeTreeHelper
from UnityPy.streams import EndianBinaryWriter

import UnityPy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from convert_punctuation import convert as convert_punct  # noqa: E402

TypeTreeHelper.read_typetree_boost = False

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_REL = "Warhammer 40K Battlesector_Data"
DEFAULT_VANILLA = os.path.join(
    REPO, ".copilot_workspace", "vanilla-1.7.7", DATA_REL, "resources.assets"
)
VANILLA_RES = os.environ.get("MOD_VANILLA_RES", DEFAULT_VANILLA)
OUT_DIR = os.path.join(REPO, ".build", os.environ.get("MOD_TEXT_OUT", "text"))
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
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.lstrip().startswith("#"):
                continue
            if "\t" not in line:
                continue
            search, replace = line.split("\t", 1)
            if search:
                rules.append((search, replace))
    return rules


def as_text(d):
    s = d.m_Script
    b = s.encode("utf-8", "surrogateescape") if isinstance(s, str) else bytes(s)
    return b.decode("utf-8", "replace")


def main():
    if not os.path.isfile(VANILLA_RES):
        print(f"ERROR: vanilla resources.assets not found: {VANILLA_RES}", file=sys.stderr)
        print("Set MOD_VANILLA_RES to your pristine resources.assets.", file=sys.stderr)
        sys.exit(1)
    os.makedirs(OUT_DIR, exist_ok=True)

    s2tw = opencc.OpenCC("s2tw")
    glossary = load_glossary(GLOSSARY)
    print(f"glossary rules: {len(glossary)}")

    env = UnityPy.load(VANILLA_RES)
    manifest = []
    for o in env.objects:
        if o.type.name != "TextAsset":
            continue
        d = o.read()
        name = getattr(d, "m_Name", "")
        if name not in CHINESE:
            continue
        text = as_text(d)
        text = s2tw.convert(text)
        for search, replace in glossary:
            text = text.replace(search, replace)
        text = convert_punct(text)

        node = o._get_typetree_node()
        td = o.read_typetree()
        td["m_Script"] = text
        w = EndianBinaryWriter(endian="<")
        TypeTreeHelper.write_typetree(td, node, w)
        binpath = os.path.join(OUT_DIR, f"text_{o.path_id}.bin")
        with open(binpath, "wb") as f:
            f.write(bytes(w.bytes))
        manifest.append((o.path_id, binpath))
        print(f"{name} (pid {o.path_id}): {len(text.encode('utf-8'))} bytes -> {os.path.basename(binpath)}")

    with open(os.path.join(OUT_DIR, "manifest.txt"), "w", encoding="utf-8") as f:
        for pid, binpath in manifest:
            f.write(f"{pid}\t{binpath}\n")
    print(f"wrote {len(manifest)} text bins + manifest.txt to {OUT_DIR}")


if __name__ == "__main__":
    main()
