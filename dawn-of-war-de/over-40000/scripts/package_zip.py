#!/usr/bin/env python3
"""Deterministic Vortex zip packaging (used by `make build` / build.ps1).

Wraps a directory tree into a .zip with:
  - stable entry order (paths sorted lexicographically),
  - fixed entry timestamps (SOURCE_DATE_EPOCH if set, else the HEAD commit
    date, else 2000-01-01 UTC),
  - normalized metadata (0644 mode, no per-entry extra fields),
  - fixed deflate level (6).

Same input tree + same effective timestamp => byte-identical zips, so
`make build` is reproducible per AGENTS.md hard rule 15.

Usage: python3 scripts/package_zip.py <src-dir> <out-zip>
"""
from __future__ import annotations

import argparse
import datetime as _dt
import os
import subprocess
import sys
import zipfile
from pathlib import Path

FALLBACK_EPOCH = "946684800"  # 2000-01-01 00:00:00 UTC


def effective_epoch() -> int:
    """SOURCE_DATE_EPOCH, else HEAD commit date, else a fixed fallback."""
    env = os.environ.get("SOURCE_DATE_EPOCH")
    if env is not None:
        try:
            return int(env)
        except ValueError:
            print(f"warning: ignoring invalid SOURCE_DATE_EPOCH={env!r}", file=sys.stderr)
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%ct"],
            capture_output=True, text=True, timeout=10,
        )
        if out.returncode == 0 and out.stdout.strip().isdigit():
            return int(out.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    return int(FALLBACK_EPOCH)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("src_dir", type=Path)
    ap.add_argument("out_zip", type=Path)
    args = ap.parse_args()

    epoch = effective_epoch()
    dt = _dt.datetime.fromtimestamp(epoch, tz=_dt.timezone.utc)
    stamp = (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

    src = args.src_dir
    files = sorted(
        p for p in src.rglob("*") if p.is_file() and p.name != ".DS_Store"
    )
    with zipfile.ZipFile(args.out_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for f in files:
            info = zipfile.ZipInfo(f.relative_to(src).as_posix(), date_time=stamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            info.create_system = 3
            with open(f, "rb") as fh:
                z.writestr(info, fh.read())
    print(f"✓ {args.out_zip}  ({len(files)} files, timestamp {dt:%Y-%m-%d %H:%M:%S} UTC)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())