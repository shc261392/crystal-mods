#!/usr/bin/env python3
"""Gate 5 - terminology.

Rejects Mainland-only wording that survives OpenCC's s2twp conversion. The
rules live in reference/terminology_banned.tsv so they are reviewable without
reading Python.

Example of what this catches: s2twp has no phrase rule for
``本地化`` -> ``在地化``, so ``简体中文本地化`` comes out as
``簡體中文字地化``. Taiwan's Ministry of Education standard is ``在地化``.
"""

from __future__ import annotations

import sys
from pathlib import Path

from _common import iter_strings, load, payload_root

SCRIPT_DIR = Path(__file__).resolve().parent.parent
BANNED_FILE = SCRIPT_DIR / "reference" / "terminology_banned.tsv"


def main() -> int:
    if not BANNED_FILE.exists():
        print("[PASS] terminology: no banned-terms list, nothing to check")
        return 0

    rules: list[tuple[str, str]] = []
    for lineno, line in enumerate(
        BANNED_FILE.read_text(encoding="utf-8").splitlines(), 1
    ):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            print(f"[FAIL] terminology: {BANNED_FILE.name}:{lineno}: "
                  f"expected 3 fields")
            return 1
        scope, pattern, _note = parts
        rules.append((scope.strip(), pattern))

    pay_root = payload_root()
    errors: list[str] = []
    scanned = 0

    for target in sorted(pay_root.rglob("config_zh.yaml")):
        rel = str(target.relative_to(pay_root))
        applicable = [
            pattern
            for scope, pattern in rules
            if scope == "*" or scope == rel
        ]
        if not applicable:
            continue
        for path, value in iter_strings(load(target)):
            scanned += 1
            for pattern in applicable:
                if pattern in value:
                    errors.append(
                        f"{rel} [{path}]: banned term {pattern!r} in {value[:60]!r}"
                    )

    if errors:
        print(f"[FAIL] terminology: {len(errors)} occurrence(s) of "
              f"{len({p for _, p in rules})} banned term(s)")
        for e in errors[:40]:
            print(f"       {e}")
        if len(errors) > 40:
            print(f"       ... and {len(errors) - 40} more")
        return 1

    print(f"[PASS] terminology: {scanned} string(s) free of "
          f"{len({p for _, p in rules})} Mainland-only term(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())