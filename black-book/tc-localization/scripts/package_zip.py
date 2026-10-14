#!/usr/bin/env python3
"""Package the payload into a deterministic, reproducible zip.

Given the same commit, ``make build`` must always produce a byte-identical
archive (AGENTS.md rule 15). That means:

*   entries are added in sorted order;
*   every entry gets the same fixed timestamp;
*   file modes are normalised;
*   no extra attributes are stored;
*   the existing archive is removed first, so a stale build can never linger.
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent

# 1980-01-01 00:00:00 - the earliest timestamp the zip format can represent.
FIXED_DATE = (1980, 1, 1, 0, 0, 0)

GLOBAL_MODE = 0o644


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--payload", type=Path,
                        default=SCRIPT_DIR / "payload")
    parser.add_argument("--dist", type=Path, default=SCRIPT_DIR / "dist")
    parser.add_argument("--name", required=True, help="output file name, e.g. mod.zip")
    parser.add_argument("--exclude", nargs="*", default=[".DS_Store", "Thumbs.db"])
    args = parser.parse_args()

    if not args.payload.is_dir():
        sys.exit(f"ERROR: payload directory not found: {args.payload}")

    args.dist.mkdir(parents=True, exist_ok=True)
    out = args.dist / args.name
    if out.exists():
        out.unlink()

    files = sorted(
        p for p in args.payload.rglob("*")
        if p.is_file() and p.name not in args.exclude
    )
    if not files:
        sys.exit(f"ERROR: no files to package under {args.payload}")

    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as zf:
        for path in files:
            arcname = path.relative_to(args.payload).as_posix()
            info = zipfile.ZipInfo(arcname, date_time=FIXED_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = GLOBAL_MODE << 16
            info.create_system = 3  # Unix, so the mode above is honoured
            zf.writestr(info, path.read_bytes())

    print(f"  archive          : {out.relative_to(SCRIPT_DIR)}")
    print(f"  entries          : {len(files)}")
    print(f"  size             : {out.stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())