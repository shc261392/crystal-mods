#!/usr/bin/env python3
"""Extract all EN/SC/TC string triples from the Black Book config files.

Output: triples.jsonl  (one JSON object per line)
  {file, key, en, sc, tc}
Also prints summary stats.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

MOD = Path("/home/shado/crystal-mods/black-book/tc-localization")
TC_ROOT = MOD / "payload" / "Black Book_Data" / "StreamingAssets" / "Config"
SC_ROOT = MOD / "source" / "sc" / "StreamingAssets" / "Config"
GAME = Path("/mnt/d/SteamLibrary/steamapps/common/Black Book/Black Book_Data/StreamingAssets/Config")
OUT = Path("/home/shado/crystal-mods/.copilot_workspace/bb-tc-audit")


def leaves(node, prefix=""):
    if isinstance(node, dict):
        for key, value in node.items():
            yield from leaves(value, f"{prefix}.{key}" if prefix else str(key))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from leaves(value, f"{prefix}[{index}]")
    elif isinstance(node, str) and node.strip():
        yield f"{prefix}", node


def load(path: Path):
    try:
        return yaml.safe_load(path.read_bytes().decode("utf-8-sig")) or {}
    except Exception as exc:  # noqa: BLE001
        print(f"  !! parse fail {path}: {exc}", file=sys.stderr)
        return None


def main() -> int:
    tc_files = sorted(TC_ROOT.rglob("config_zh.yaml"))
    rows = []
    stat = {"tc_files": 0, "en_missing": 0, "key_missing_en": 0, "identical": 0}
    for tc_path in tc_files:
        rel = tc_path.relative_to(TC_ROOT)
        en_path = GAME / rel.parent / "config_en.yaml"
        sc_path = SC_ROOT / rel.parent / "config_zh.yaml"
        tc_data = load(tc_path)
        if tc_data is None:
            continue
        stat["tc_files"] += 1
        en_data = load(en_path) if en_path.exists() else None
        sc_data = load(sc_path) if sc_path.exists() else None
        if en_data is None:
            stat["en_missing"] += 1
        en_map = dict(leaves(en_data)) if en_data is not None else {}
        sc_map = dict(leaves(sc_data)) if sc_data is not None else {}
        for key, tc in leaves(tc_data):
            en = en_map.get(key)
            sc = sc_map.get(key)
            rows.append({
                "file": str(rel.parent),
                "key": key,
                "en": en,
                "sc": sc,
                "tc": tc,
            })
    with (OUT / "triples.jsonl").open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    total = len(rows)
    print(f"TC files parsed            : {stat['tc_files']}")
    print(f"files with no EN counterpart: {stat['en_missing']}")
    print(f"total string triples       : {total}")
    print(f"rows missing EN value      : {sum(1 for r in rows if r['en'] is None)}")
    print(f"rows missing SC value      : {sum(1 for r in rows if r['sc'] is None)}")
    print(f"rows EN==TC                : {sum(1 for r in rows if r['en'] == r['tc'])}")
    print(f"rows SC!=TC (OpenCC change): {sum(1 for r in rows if r['sc'] is not None and r['sc'] != r['tc'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
