#!/usr/bin/env python3
"""Gate 1 - coverage.

Catches the class of bug where the converter silently drops files or strings.
Every ``config_zh.yaml`` in the SC source must have exactly one counterpart in
the payload, and that counterpart must expose the same structure (same key
paths, same number of string leaves).

This is the gate that would have caught ``Service/Credits``,
``Demons`` and ``Izba`` being missing from the previous payload.
"""

from __future__ import annotations

import sys
from pathlib import Path

from _common import iter_strings, load, payload_root, source_root  # noqa: F401


def main() -> int:
    src_root, pay_root = source_root(), payload_root()
    src_files = {p.relative_to(src_root) for p in src_root.rglob("config_zh.yaml")}
    pay_files = {p.relative_to(pay_root) for p in pay_root.rglob("config_zh.yaml")}

    errors: list[str] = []

    for missing in sorted(src_files - pay_files):
        errors.append(f"missing from payload: {missing}")
    for extra in sorted(pay_files - src_files):
        errors.append(f"in payload but not in source: {extra}")

    checked = 0
    for rel in sorted(src_files & pay_files):
        src_leaves = dict(iter_strings(load(src_root / rel)))
        pay_leaves = dict(iter_strings(load(pay_root / rel)))
        checked += 1

        src_paths = set(src_leaves)
        pay_paths = set(pay_leaves)
        if src_paths != pay_paths:
            only_src = sorted(src_paths - pay_paths)
            only_pay = sorted(pay_paths - src_paths)
            if only_src:
                errors.append(f"{rel}: {len(only_src)} string key(s) lost, "
                              f"e.g. {only_src[:3]}")
            if only_pay:
                errors.append(f"{rel}: {len(only_pay)} unexpected string key(s), "
                              f"e.g. {only_pay[:3]}")

    if errors:
        print(f"[FAIL] coverage: {len(errors)} problem(s)")
        for e in errors[:40]:
            print(f"       {e}")
        if len(errors) > 40:
            print(f"       ... and {len(errors) - 40} more")
        return 1

    print(f"[PASS] coverage: {checked} file(s), string keys match source exactly")
    return 0


if __name__ == "__main__":
    sys.exit(main())