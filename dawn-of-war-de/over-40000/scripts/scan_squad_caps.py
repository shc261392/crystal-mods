#!/usr/bin/env python3
"""Scan DoW DE squad files (.rgd) for `required_squad_cap` requirements.

For each squad whose `squad_requirement_ext.requirements` list contains a
`requirements\\required_squad_cap.lua` entry, print the 1-based list index and
the current max_squad_cap value. This is the "1-of / N-of" unit limit.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rgd_decode import Decoder, extract_aegd, relic_hash

REF = 0x49D60FAE  # fixed "reference" key -> path value
MAX_SQ = relic_hash("max_squad_cap")
SQ_REQ_EXT = relic_hash("squad_requirement_ext")
REQUIREMENTS = relic_hash("requirements")


def analyze(path: Path):
    try:
        aegd = extract_aegd(path)
    except Exception:
        return []
    d = Decoder(aegd)
    top = d._table(12)
    if top is None:
        return []
    # locate squad_requirement_ext top-level entry
    req_ext_vabs = None
    for kh, typ, vabs in top[1]:
        if typ == 100 and kh == SQ_REQ_EXT:
            req_ext_vabs = vabs
            break
    if req_ext_vabs is None:
        return []
    req_ext = d._table(req_ext_vabs)
    if req_ext is None:
        return []
    req_list_vabs = None
    for kh, typ, vabs in req_ext[1]:
        if typ == 100 and kh == REQUIREMENTS:
            req_list_vabs = vabs
            break
    if req_list_vabs is None:
        return []
    req_list = d._table(req_list_vabs)
    if req_list is None:
        return []
    results = []
    for idx, (kh, typ, vabs) in enumerate(req_list[1], start=1):
        if typ != 100:
            continue
        sub = d._table(vabs)
        if sub is None:
            continue
        is_cap = False
        max_cap = None
        for kh2, typ2, vabs2 in sub[1]:
            if typ2 == 3 and kh2 == REF:
                if d._read_cstr(vabs2).lower().endswith("required_squad_cap.lua"):
                    is_cap = True
            elif typ2 in (0, 4) and kh2 == MAX_SQ:
                max_cap = d._value(typ2, vabs2)
        if is_cap:
            results.append((kh, idx, max_cap))
    return results


def main(root: str):
    rootp = Path(root)
    total = 0
    for rgd in sorted(rootp.rglob("*.rgd")):
        if "sbps" not in str(rgd).replace("\\", "/"):
            continue
        results = analyze(rgd)
        if results:
            rel = str(rgd).replace(str(rootp), "").lstrip("/\\")
            for entry_hash, idx, cap in results:
                print(f"{rel}  req#{idx} [0x{entry_hash:08X}] max_squad_cap={cap}")
                total += 1
    print(f"TOTAL requirement entries: {total}")


if __name__ == "__main__":
    main(sys.argv[1])
