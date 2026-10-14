#!/usr/bin/env python3
"""Regenerate the plugin's SC->TC conversion tables from OpenCC.

Run this only when upgrading OpenCC. The output is committed, so a normal
`make build` / plugin build never needs the opencc Python package.

    python3 scripts/generate_opencc_tables.py

OpenCC's s2twp pipeline is:

    stage 1: mmseg segmentation over STPhrases, then STPhrases -> STCharacters
    stage 2: TWPhrases
    stage 3: TWVariants

Porting the segmentation and candidate-disambiguation machinery to C# would be
fragile, so we flatten each dictionary to its FIRST candidate and do greedy
longest-match at runtime instead. Measured against real OpenCC on 4,832 of
Black Book's own strings, that simplification agrees 99.98% of the time (the
only miss is the 羣/群 variant, which changes nothing semantically).

Outputs (committed):
    plugin/tables/opencc_st.tsv   stage 1
    plugin/tables/opencc_tw.tsv   stages 2+3
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = SCRIPT_DIR / "plugin" / "tables"

try:
    import opencc
    from opencc import OpenCC
except ImportError:
    sys.exit("ERROR: pip install opencc-python-reimplemented")

DICT_DIR = Path(opencc.__file__).parent / "dictionary"


def load(name: str) -> dict[str, str]:
    """Load an OpenCC dictionary, keeping the first candidate per key."""
    path = DICT_DIR / name
    if not path.exists():
        sys.exit(f"ERROR: OpenCC dictionary not found: {path}")
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or "\t" not in line:
            continue
        key, value = line.split("\t", 1)
        candidates = value.split()
        if key and candidates:
            out[key] = candidates[0]
    return out


def write(name: str, *tables: dict[str, str]) -> None:
    """Write one stage, longest keys first so a reader can pre-size buffers."""
    merged: dict[str, str] = {}
    for table in tables:
        merged.update(table)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for key in sorted(merged, key=lambda k: (-len(k), k)):
            fh.write(f"{key}\t{merged[key]}\n")
    print(f"  {path.relative_to(SCRIPT_DIR)}  "
          f"{len(merged):,} entries, {path.stat().st_size:,} bytes")


def validate() -> None:
    """Sanity-check the flattened tables against real OpenCC on our own text.

    Mirrors exactly what the C# converter does: one merged longest-match table
    per stage, applied in sequence.
    """
    src = SCRIPT_DIR / "source" / "sc" / "StreamingAssets" / "Config"
    if not src.is_dir():
        print("  (source/sc not present, skipping validation)")
        return

    stage1 = load("STPhrases.txt")
    stage1.update(load("STCharacters.txt"))
    stage2 = load("TWPhrases.txt")
    stage2.update(load("TWVariants.txt"))
    max1 = max(len(k) for k in stage1)
    max2 = max(len(k) for k in stage2)

    def convert(text: str, table: dict[str, str], maxlen: int) -> str:
        out: list[str] = []
        i, n = 0, len(text)
        while i < n:
            for length in range(min(maxlen, n - i), 1, -1):
                chunk = text[i:i + length]
                if chunk in table:
                    out.append(table[chunk])
                    i += length
                    break
            else:
                out.append(table.get(text[i], text[i]))
                i += 1
        return "".join(out)

    cc = OpenCC("s2twp")
    total = same = 0
    for path in src.rglob("config_zh.yaml"):
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            if ":" not in line:
                continue
            value = line.split(":", 1)[1].strip()
            if not value:
                continue
            total += 1
            if convert(convert(value, stage1, max1), stage2, max2) == cc.convert(value):
                same += 1

    if total:
        print(f"  validation: {same}/{total} identical to real OpenCC "
              f"({100 * same / total:.2f}%)")


def main() -> int:
    print("Generating OpenCC runtime tables")
    write("opencc_st.tsv", load("STPhrases.txt"), load("STCharacters.txt"))
    write("opencc_tw.tsv", load("TWPhrases.txt"), load("TWVariants.txt"))
    validate()
    return 0


if __name__ == "__main__":
    sys.exit(main())