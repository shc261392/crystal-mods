#!/usr/bin/env python3
"""Gate 4 - override integrity.

Every row in reference/overrides.tsv must actually be present in the payload
with exactly the text it declares. An override that silently stopped matching
- because a game update renamed a key, or because someone mistyped the path -
would otherwise disappear without anyone noticing.

This is the gate that keeps manual corrections from rotting.
"""

from __future__ import annotations

import sys
from pathlib import Path

from _common import iter_strings, load, payload_root

SCRIPT_DIR = Path(__file__).resolve().parent.parent
OVERRIDES_FILE = SCRIPT_DIR / "reference" / "overrides.tsv"


def main() -> int:
    if not OVERRIDES_FILE.exists():
        print("[PASS] overrides: no overrides.tsv, nothing to check")
        return 0

    pay_root = payload_root()
    errors: list[str] = []
    checked = 0

    for lineno, line in enumerate(
        OVERRIDES_FILE.read_text(encoding="utf-8").splitlines(), 1
    ):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            errors.append(f"{OVERRIDES_FILE.name}:{lineno}: expected 3 fields")
            continue

        rel, key, expected = parts[0].strip(), parts[1].strip(), parts[2]
        target = pay_root / rel
        checked += 1

        if not target.exists():
            errors.append(f"{rel}: file missing from payload")
            continue

        actual = dict(iter_strings(load(target))).get(key)
        if actual is None:
            errors.append(f"{rel} [{key}]: no such string in payload")
        elif actual != expected:
            errors.append(
                f"{rel} [{key}]: payload says {actual!r}, "
                f"override says {expected!r}"
            )

    if errors:
        print(f"[FAIL] overrides: {len(errors)} problem(s)")
        for e in errors[:40]:
            print(f"       {e}")
        return 1

    print(f"[PASS] overrides: {checked} override(s) present and correct")
    return 0


if __name__ == "__main__":
    sys.exit(main())