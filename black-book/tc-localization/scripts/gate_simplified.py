#!/usr/bin/env python3
"""Gate 3 - no Simplified leftovers.

Every string in the payload must equal exactly what a single ``OpenCC s2twp``
pass over the corresponding source string produces (unless a manual override in
reference/overrides.tsv says otherwise).

Note on idempotence: ``s2twp`` is deliberately NOT idempotent. Applying it
twice mangles text - ``托马希哈`` -> ``托馬希哈`` -> ``託馬希哈`` (the surname
particle 托 gets wrongly turned into 託), and ``班尼亚里面`` -> ``班尼亞里面``
-> ``班尼亞裡面``. So the check is equality against the expected output, not
"running the converter again changes nothing". A previous version of this
pipeline ran the conversion twice, which is where those wrong forms came from.
"""

from __future__ import annotations

import sys
from pathlib import Path

from _common import iter_strings, load, payload_root, source_root

try:
    from opencc import OpenCC
except ImportError:  # pragma: no cover
    sys.exit("ERROR: opencc-python-reimplemented is required. See pyproject.toml")

SCRIPT_DIR = Path(__file__).resolve().parent.parent
OVERRIDES_FILE = SCRIPT_DIR / "reference" / "overrides.tsv"

CONVERTER = OpenCC("s2twp")


def load_override_map() -> dict[str, dict[str, str]]:
    if not OVERRIDES_FILE.exists():
        return {}
    out: dict[str, dict[str, str]] = {}
    for line in OVERRIDES_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) == 3:
            out.setdefault(parts[0].strip(), {})[parts[1].strip()] = parts[2]
    return out


def main() -> int:
    src_root, pay_root = source_root(), payload_root()
    overrides = load_override_map()
    errors: list[str] = []
    total = 0

    for src in sorted(src_root.rglob("config_zh.yaml")):
        rel = src.relative_to(src_root)
        pay = pay_root / rel
        if not pay.exists():
            continue

        file_overrides = overrides.get(str(rel), {})
        src_leaves = dict(iter_strings(load(src)))
        for key, value in iter_strings(load(pay)):
            total += 1
            if key in file_overrides:
                expected = file_overrides[key]
            elif key in src_leaves:
                expected = CONVERTER.convert(src_leaves[key])
            else:
                continue
            if value != expected:
                errors.append(
                    f"{rel} [{key}]: payload {value[:40]!r} "
                    f"!= expected {expected[:40]!r}"
                )

    if errors:
        print(f"[FAIL] simplified: {len(errors)} of {total} string(s) wrong")
        for e in errors[:40]:
            print(f"       {e}")
        if len(errors) > 40:
            print(f"       ... and {len(errors) - 40} more")
        return 1

    print(f"[PASS] simplified: all {total} string(s) match s2twp(source)")
    return 0


if __name__ == "__main__":
    sys.exit(main())