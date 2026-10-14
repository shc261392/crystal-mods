#!/usr/bin/env python3
"""Verify that ``make build`` is reproducible.

Builds twice from the same commit and compares the SHA-256 of both archives.
A mismatch means something non-deterministic leaked into the pipeline (a
timestamp, a filesystem ordering, an untracked manual edit) and the release
must not be published until it is fixed. See AGENTS.md rule 15.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=SCRIPT_DIR / "dist")
    parser.add_argument("--name", required=True)
    args = parser.parse_args()

    target = args.dist / args.name
    if not target.exists():
        sys.exit(f"ERROR: {target} does not exist - run `make build` first")

    first = sha256(target)

    with tempfile.TemporaryDirectory() as tmp:
        stash = Path(tmp) / "first.zip"
        shutil.copy2(target, stash)

        print("  rebuilding from scratch...")
        # Forward the interpreter running this check, so the rebuild uses the
        # same environment (and the same OpenCC/dictionary version) as the
        # build being verified.
        result = subprocess.run(
            ["make", "build", f"PYTHON={sys.executable}"], cwd=SCRIPT_DIR,
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            sys.exit("ERROR: rebuild failed\n" + result.stdout + result.stderr)

        second = sha256(target)

    if first == second:
        print(f"[PASS] reproducible: {args.name} sha256={first}")
        return 0

    print(f"[FAIL] build is NOT reproducible")
    print(f"       first  : {first}")
    print(f"       second : {second}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())