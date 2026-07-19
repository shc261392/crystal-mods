#!/usr/bin/env python3
"""
Adjust Dawn of War DE font sizes across all resolutions.

This script increases or decreases font sizes in .fnt files by a fixed amount
across ALL resolution breakpoints (sizeDefault, size640, size800, size1024,
size1280, size1600).

Usage:
    python3 adjust_font_sizes.py --root data/ --increase 6
    python3 adjust_font_sizes.py --root data/ --decrease 4 --dry-run
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def adjust_fnt_sizes(
    fnt_path: Path,
    delta: int,
    dry_run: bool = False,
) -> dict[str, int]:
    """
    Adjust all size* properties in an .fnt file by delta.

    Returns dict mapping property names to old values for reporting.
    """
    content = fnt_path.read_text(encoding="utf-8")
    changes = {}

    # Pattern matches: sizeDefault = 14;
    #                  size640 = 10;
    #                  size1024 = 18;
    # etc.
    pattern = re.compile(r"(size(?:Default|640|800|1024|1280|1600))\s*=\s*(\d+)\s*;", re.IGNORECASE)

    def replace_size(match: re.Match) -> str:
        prop_name = match.group(1)
        old_value = int(match.group(2))
        new_value = old_value + delta

        # Clamp to reasonable range (min 6, max 96)
        new_value = max(6, min(96, new_value))

        changes[prop_name] = old_value
        return f"{prop_name}\t= {new_value};"

    new_content = pattern.sub(replace_size, content)

    if changes:
        if not dry_run:
            fnt_path.write_text(new_content, encoding="utf-8")
        return changes

    return {}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Adjust Dawn of War DE font sizes across all resolutions"
    )
    parser.add_argument(
        "--root",
        type=Path,
        required=True,
        help="Root directory containing font/ subdirectory with .fnt files",
    )

    size_group = parser.add_mutually_exclusive_group(required=True)
    size_group.add_argument(
        "--increase",
        type=int,
        metavar="N",
        help="Increase all font sizes by N points",
    )
    size_group.add_argument(
        "--decrease",
        type=int,
        metavar="N",
        help="Decrease all font sizes by N points",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without modifying files",
    )

    args = parser.parse_args()

    root = args.root.resolve()
    font_dir = root / "font"

    if not font_dir.exists():
        print(f"ERROR: Font directory not found: {font_dir}")
        return 1

    # Calculate delta
    if args.increase:
        delta = args.increase
        action = f"increase by +{delta}"
    else:
        delta = -args.decrease
        action = f"decrease by {delta}"

    print(f"{'[DRY-RUN] ' if args.dry_run else ''}Adjusting font sizes: {action}")
    print(f"Scanning: {font_dir}")
    print()

    fnt_files = sorted(font_dir.glob("*.fnt"))

    if not fnt_files:
        print(f"ERROR: No .fnt files found in {font_dir}")
        return 1

    total_files = 0
    total_properties = 0

    for fnt_path in fnt_files:
        changes = adjust_fnt_sizes(fnt_path, delta, dry_run=args.dry_run)

        if changes:
            total_files += 1
            total_properties += len(changes)

            print(f"✓ {fnt_path.name}")
            for prop_name, old_value in sorted(changes.items()):
                new_value = old_value + delta
                # Clamp display to match actual clamping in adjust_fnt_sizes
                new_value = max(6, min(96, new_value))
                print(f"  {prop_name:15} {old_value:3d} → {new_value:3d}")
            print()

    print(f"{'[DRY-RUN] ' if args.dry_run else ''}Summary:")
    print(f"  Files modified: {total_files}")
    print(f"  Properties adjusted: {total_properties}")

    if args.dry_run:
        print()
        print("No files were modified. Remove --dry-run to apply changes.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
