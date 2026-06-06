#!/usr/bin/env python3
"""
analyze.py — Translation coverage and quality report for WH40K Battlesector zh-TW mod.

Usage:
    python3 tools/scripts/analyze.py [--translation-dir translation/zh-TW/Text]
"""

import argparse
import csv
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_translations(txt_path: Path) -> dict[str, str]:
    """Load key=value translation pairs from a .txt file.
    The separator is the first '=' NOT preceded by a backslash.
    """
    entries: dict[str, str] = {}
    _SEP = re.compile(r'(?<!\\)=')
    with open(txt_path, encoding="utf-8", errors="replace") as f:
        for lineno, line in enumerate(f, 1):
            line = line.rstrip("\n")
            if not line or line.startswith("//"):
                continue
            m = _SEP.search(line)
            if not m:
                continue
            key = line[:m.start()]
            val = line[m.end():]
            entries[key] = val
    return entries


def load_glossary(csv_path: Path) -> list[dict]:
    with open(csv_path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def analyze(translation_dir: Path, glossary_path: Path) -> None:
    files = sorted(translation_dir.glob("*.txt"))
    if not files:
        print(f"No .txt files found in {translation_dir}", file=sys.stderr)
        sys.exit(1)

    all_entries: dict[str, str] = {}
    per_file: dict[str, dict[str, str]] = {}
    for f in files:
        entries = load_translations(f)
        per_file[f.name] = entries
        all_entries.update(entries)

    total = len(all_entries)

    # ---- Basic stats ----
    identical = {k: v for k, v in all_entries.items() if k == v}
    empty_val = {k: v for k, v in all_entries.items() if not v.strip()}
    with_rich = {k for k, v in all_entries.items() if re.search(r"<[a-z/]", v, re.I)}
    with_placeholders = {k for k, v in all_entries.items() if re.search(r"\{[0-9]+\}", v)}
    multiline = {k for k, v in all_entries.items() if r"\r\n" in v or r"\n" in v}

    print("=" * 60)
    print("WH40K Battlesector zh-TW Translation Analysis")
    print("=" * 60)
    print(f"\nTranslation directory : {translation_dir}")
    print(f"Files loaded          : {len(files)}")
    print(f"  " + "\n  ".join(
        f"{fn} ({len(entries)} entries)" for fn, entries in per_file.items()
    ))
    print(f"\nTotal unique entries  : {total}")
    print(f"Identical SC=TC       : {len(identical)}  ({100*len(identical)//max(total,1)}%)")
    print(f"Empty translation     : {len(empty_val)}")
    print(f"With rich-text markup : {len(with_rich)}")
    print(f"With placeholders     : {len(with_placeholders)}")
    print(f"Multiline             : {len(multiline)}")

    # ---- Glossary term check ----
    if glossary_path.exists():
        glossary = load_glossary(glossary_path)
        print(f"\n{'='*60}")
        print("Glossary Term Compliance")
        print(f"{'='*60}")
        violations: list[tuple[str, str, str, str]] = []
        for row in glossary:
            sc = row["sc_term"]
            tc_expected = row["tc_term"]
            category = row.get("category", "")
            for key, val in all_entries.items():
                # Check if the TC value still contains the SC term (not converted)
                if sc in val and tc_expected not in val and sc != tc_expected:
                    violations.append((key[:60], val[:60], sc, tc_expected))
        if violations:
            print(f"\n⚠  {len(violations)} translation(s) contain SC term in TC value:")
            for key, val, sc_t, tc_t in violations[:20]:
                print(f"  SC term [{sc_t}] → expected [{tc_t}]")
                print(f"    key: {key}")
                print(f"    val: {val}")
        else:
            print("\n✓ No glossary violations found.")
    else:
        print(f"\n(Glossary not found at {glossary_path} — skipping term check)")

    # ---- Markup integrity check ----
    broken_markup: list[tuple[str, str]] = []
    for key, val in all_entries.items():
        opens = len(re.findall(r"<(?!/)(\w+)[^>]*>", val))
        closes = len(re.findall(r"</(\w+)>", val))
        if opens != closes:
            broken_markup.append((key[:80], val[:80]))

    print(f"\n{'='*60}")
    print("Rich-text Markup Integrity")
    print(f"{'='*60}")
    if broken_markup:
        print(f"\n⚠  {len(broken_markup)} entries with unbalanced tags:")
        for k, v in broken_markup[:10]:
            print(f"  key: {k}")
            print(f"  val: {v}")
    else:
        print("\n✓ All rich-text tags appear balanced.")

    # ---- Placeholder preservation ----
    broken_ph: list[tuple[str, str, str]] = []
    for key, val in all_entries.items():
        key_phs = set(re.findall(r"\{[0-9]+\}", key))
        val_phs = set(re.findall(r"\{[0-9]+\}", val))
        if key_phs != val_phs:
            broken_ph.append((key[:80], str(key_phs), str(val_phs)))

    print(f"\n{'='*60}")
    print("Format Placeholder Preservation")
    print(f"{'='*60}")
    if broken_ph:
        print(f"\n⚠  {len(broken_ph)} entries with mismatched placeholders:")
        for k, exp, got in broken_ph[:10]:
            print(f"  key: {k}")
            print(f"  expected: {exp}  got: {got}")
    else:
        print("\n✓ All format placeholders preserved.")

    print("\nDone.\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Translation quality report")
    parser.add_argument(
        "--translation-dir",
        default=str(REPO_ROOT / "translation" / "zh-TW" / "Text"),
        help="Path to the Translation/zh-TW/Text directory",
    )
    parser.add_argument(
        "--glossary",
        default=str(REPO_ROOT / "glossary" / "wh40k-tc-glossary.csv"),
        help="Path to the glossary CSV",
    )
    args = parser.parse_args()
    analyze(Path(args.translation_dir), Path(args.glossary))


if __name__ == "__main__":
    main()
