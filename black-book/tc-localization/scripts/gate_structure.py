#!/usr/bin/env python3
"""Gate 2 - structural fidelity.

The converter must only ever change string scalars. Everything else - the key
set, key order, nesting, numbers, booleans, nulls, the UTF-8 BOM and the CRLF
line endings the game itself ships - has to survive untouched.

A payload file that loses its BOM, flips to LF, or reorders keys is a file the
game's parser has never seen before.
"""

from __future__ import annotations

import sys

from _common import format_flags, iter_scalars, load, payload_root, source_root


def key_order(node, path=()):
    """Flatten the mapping key order so reordering can be detected."""
    out = []
    if isinstance(node, dict):
        for key, value in node.items():
            out.append(path + (str(key),))
            out.extend(key_order(value, path + (str(key),)))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            out.extend(key_order(value, path + (str(index),)))
    return out


def main() -> int:
    src_root, pay_root = source_root(), payload_root()
    errors: list[str] = []
    checked = 0

    for src in sorted(src_root.rglob("config_zh.yaml")):
        rel = src.relative_to(src_root)
        pay = pay_root / rel
        if not pay.exists():
            continue  # reported by gate_coverage
        checked += 1

        src_data, pay_data = load(src), load(pay)

        if key_order(src_data) != key_order(pay_data):
            errors.append(f"{rel}: key order / structure changed")

        src_scalars = dict(iter_scalars(src_data))
        pay_scalars = dict(iter_scalars(pay_data))
        for path, value in src_scalars.items():
            if path not in pay_scalars:
                errors.append(f"{rel}: non-string value lost at {path}")
            elif pay_scalars[path] != value:
                errors.append(
                    f"{rel}: non-string value changed at {path}: "
                    f"{value!r} -> {pay_scalars[path]!r}"
                )

        src_bom, src_crlf = format_flags(src)
        pay_bom, pay_crlf = format_flags(pay)
        if (src_bom, src_crlf) != (pay_bom, pay_crlf):
            errors.append(
                f"{rel}: encoding/line-ending drift "
                f"(BOM {src_bom}->{pay_bom}, CRLF {src_crlf}->{pay_crlf})"
            )

    if errors:
        print(f"[FAIL] structure: {len(errors)} problem(s)")
        for e in errors[:40]:
            print(f"       {e}")
        if len(errors) > 40:
            print(f"       ... and {len(errors) - 40} more")
        return 1

    print(f"[PASS] structure: {checked} file(s) keep key order, "
          f"scalars, BOM and line endings")
    return 0


if __name__ == "__main__":
    sys.exit(main())