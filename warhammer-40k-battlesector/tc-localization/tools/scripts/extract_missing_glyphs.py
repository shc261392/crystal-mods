#!/usr/bin/env python3
"""
extract_missing_glyphs.py — Parse Unity Player.log for TMP missing-glyph diagnostics.

Primary use in this repo:
- find missing glyphs for [futura medium condensed bt SDF - No Underlay]
- in key text objects (campaign + unit management):
    [Description], [TitleText], [PointCostText], [UnitNameText], [ArmyCohesionLimit]
- refresh campaign-only fallback config consumed by patch_resources.py

Usage examples:
  python3 tools/scripts/extract_missing_glyphs.py
  python3 tools/scripts/extract_missing_glyphs.py --log "/path/to/Player.log"
  python3 tools/scripts/extract_missing_glyphs.py --write-config
"""

import argparse
import json
import os
import re
import sys
from collections import Counter
from collections import deque
from datetime import datetime, UTC

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
DEFAULT_LOG = "/mnt/c/Users/shado/AppData/LocalLow/Black Lab Games/Warhammer 40,000 Battlesector/Player.log"
FALLBACK_CONFIG = os.path.join(REPO_ROOT, "translation", "zh-TW", "config", "description_fallback_chars.json")

LINE_RE = re.compile(
    r"The character with Unicode value \\u([0-9A-Fa-f]{4,6}) was not found in the \[(.*?)\].*text object \[(.*?)\]\."
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Extract missing TMP glyphs from Player.log")
    p.add_argument("--log", default=DEFAULT_LOG, help="Path to Player.log")
    p.add_argument("--write-config", action="store_true", help="Write campaign fallback config JSON")
    p.add_argument(
        "--font-contains",
        default="futura medium condensed bt SDF - No Underlay",
        help="Filter to missing glyph entries where font asset contains this string (case-insensitive)",
    )
    p.add_argument(
        "--text-objects",
        default="Description,TitleText,PointCostText,UnitNameText,ArmyCohesionLimit",
        help="Comma-separated text object names to include",
    )
    p.add_argument(
        "--tail-lines",
        type=int,
        default=0,
        help="Only analyze the last N lines of Player.log (0 = full file)",
    )
    p.add_argument(
        "--no-merge-existing",
        action="store_true",
        help="When --write-config is used, do not merge with existing fallback chars",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if not os.path.isfile(args.log):
        print(f"ERROR: log file not found: {args.log}", file=sys.stderr)
        sys.exit(1)

    target_font = args.font_contains.lower().strip()
    allowed_objects = {x.strip() for x in args.text_objects.split(",") if x.strip()}

    counter: Counter[int] = Counter()
    total = 0

    with open(args.log, "r", encoding="utf-8", errors="replace") as f:
        if args.tail_lines and args.tail_lines > 0:
            lines = deque(f, maxlen=args.tail_lines)
        else:
            lines = f

        for line in lines:
            m = LINE_RE.search(line)
            if not m:
                continue
            cp = int(m.group(1), 16)
            font_asset = m.group(2)
            text_obj = m.group(3)

            if target_font and target_font not in font_asset.lower():
                continue
            if allowed_objects and text_obj not in allowed_objects:
                continue

            total += 1
            counter[cp] += 1

    observed = set(counter.keys())
    uniq = sorted(observed)
    chars = "".join(chr(cp) for cp in uniq)

    print(f"Log: {args.log}")
    if args.tail_lines and args.tail_lines > 0:
        print(f"Analysis window: last {args.tail_lines} lines")
    else:
        print("Analysis window: full log")
    print(f"Matched missing-glyph entries: {total}")
    print(f"Unique codepoints: {len(uniq)}")
    if uniq:
        print("Unique list:")
        print(" ".join(f"U+{cp:04X}:{chr(cp)}({counter[cp]})" for cp in uniq))

    if not args.write_config:
        return

    existing_chars: set[str] = set()
    merged = set(observed)
    if not args.no_merge_existing:
        if os.path.isfile(FALLBACK_CONFIG):
            try:
                with open(FALLBACK_CONFIG, "r", encoding="utf-8") as f:
                    existing_payload = json.load(f)
                existing_raw = ""
                if isinstance(existing_payload, dict):
                    existing_raw = existing_payload.get("campaign_chinese_fallback_chars", "") or ""
                if isinstance(existing_raw, str):
                    existing_chars = set(existing_raw)
            except Exception as e:
                print(f"WARN: failed to read existing config for merge: {e}", file=sys.stderr)

        merged = observed | {ord(ch) for ch in existing_chars}
        if len(merged) != len(observed):
            print(
                "Merging with existing config to avoid shrink: "
                f"observed={len(observed)} existing={len(existing_chars)} merged={len(merged)}"
            )
    else:
        print("Merge mode: disabled (--no-merge-existing). Writing observed set only.")

    uniq = sorted(merged)
    chars = "".join(chr(cp) for cp in uniq)

    os.makedirs(os.path.dirname(FALLBACK_CONFIG), exist_ok=True)
    payload = {
        "version": 1,
        "updated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "source_log": args.log,
        "font_filter": args.font_contains,
        "text_objects": sorted(allowed_objects),
        "campaign_chinese_fallback_chars": chars,
        "unique_codepoints": [f"U+{cp:04X}" for cp in uniq],
    }

    with open(FALLBACK_CONFIG, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Wrote config: {FALLBACK_CONFIG}")


if __name__ == "__main__":
    main()
