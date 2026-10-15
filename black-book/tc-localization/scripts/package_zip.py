#!/usr/bin/env python3
"""Assemble the release tree and package it into a deterministic zip.

Given the same commit, ``make build`` must always produce a byte-identical
archive (AGENTS.md rule 15). That means:

*   a fixed staging layout, assembled from the committed sources;
*   entries added in sorted order with a fixed timestamp and mode;
*   the previous archive removed first so a stale build can never linger.

Layout of the staged tree (the mod's install layout):

    Black Book_Data/StreamingAssets/Config/**/config_zh.yaml   generated
    BepInEx/plugins/BlackBookTcFont.dll                        compiled
    BepInEx/plugins/BlackBookTcFont/opencc_st.tsv              committed
    BepInEx/plugins/BlackBookTcFont/opencc_tw.tsv              committed
    BepInEx/plugins/BlackBookTcFont/tcserif                    committed (Unity-built)
"""

from __future__ import annotations

import argparse
import shutil
import sys
import zipfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent

# 1980-01-01 00:00:00 - the earliest timestamp the zip format can represent.
FIXED_DATE = (1980, 1, 1, 0, 0, 0)
GLOBAL_MODE = 0o644

BEPINEX_PLUGIN_DIR = "BepInEx/plugins"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--payload", type=Path, default=SCRIPT_DIR / "payload")
    parser.add_argument("--plugin", type=Path,
                        default=SCRIPT_DIR / "plugin" / "bin" / "Release" / "BlackBookTcFont.dll")
    parser.add_argument("--tables", type=Path, default=SCRIPT_DIR / "plugin" / "tables")
    parser.add_argument("--bundles", type=Path, default=SCRIPT_DIR / "plugin" / "bundles")
    parser.add_argument("--stage", type=Path, default=SCRIPT_DIR / "dist" / "stage")
    parser.add_argument("--dist", type=Path, default=SCRIPT_DIR / "dist")
    parser.add_argument("--name", required=True)
    args = parser.parse_args()

    if not args.payload.is_dir():
        sys.exit(f"ERROR: payload not found: {args.payload} - run `make generate` first")
    if not args.plugin.is_file():
        sys.exit(f"ERROR: plugin not built: {args.plugin} - run `make build-plugin` first")

    # ---- stage -----------------------------------------------------------
    if args.stage.exists():
        shutil.rmtree(args.stage)
    args.stage.mkdir(parents=True)

    # Game data: the config files only.
    game_src = args.payload / "Black Book_Data"
    if not game_src.is_dir():
        sys.exit(f"ERROR: expected {game_src}")
    shutil.copytree(game_src, args.stage / "Black Book_Data")

    # Plugin + its runtime data, in whichever layout BepInEx expects.
    plugin_dir = args.stage / BEPINEX_PLUGIN_DIR
    plugin_dir.mkdir(parents=True)
    shutil.copy2(args.plugin, plugin_dir / args.plugin.name)

    data_dir = plugin_dir / "BlackBookTcFont"
    data_dir.mkdir()
    for source in (args.tables, args.bundles):
        if not source.is_dir():
            sys.exit(f"ERROR: missing {source}")
        for entry in sorted(source.iterdir()):
            if entry.is_file():
                shutil.copy2(entry, data_dir / entry.name)

    # ---- package ---------------------------------------------------------
    args.dist.mkdir(parents=True, exist_ok=True)
    out = args.dist / args.name
    if out.exists():
        out.unlink()

    files = sorted(p for p in args.stage.rglob("*") if p.is_file())
    if not files:
        sys.exit("ERROR: nothing to package")

    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as zf:
        for path in files:
            arcname = path.relative_to(args.stage).as_posix()
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