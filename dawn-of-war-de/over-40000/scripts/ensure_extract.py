#!/usr/bin/env python3
"""Ensure the DoW DE game data is extracted so the mod can be generated.

Auto-detects the Dawn of War Definitive Edition installation (via Steam library
folders or $DOW_GAME_DIR), sets up the SGA extraction tool, and extracts the
DXP2/DXP3/W40k/WXP data archives into an extraction tree if they are not already
present.

Usage:
    python3 scripts/ensure_extract.py [--game-dir PATH] [--extract-root PATH] [--force]

The extraction tree defaults to ../.copilot_workspace/extract (gitignored).
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import venv
from pathlib import Path

GAME_FOLDER = "Dawn of War Definitive Edition"
GAME_ID = "warhammer40kdawnofwar"
MODULES = ["W40k", "WXP", "DXP2", "DXP3"]


def _module_extracted(extract_root: Path, module: str) -> bool:
    """True if the module's SGA data has already been unpacked.

    The extractor writes backslash-containing directory names (e.g.
    `data/attrib\\racebps`), so we can't rely on a forward-slash marker path.
    Instead we require the `data` folder to exist and contain at least one .rgd.
    """
    data = extract_root / module / "data"
    if not data.is_dir():
        return False
    try:
        next(data.rglob("*.rgd"))
        return True
    except StopIteration:
        return False


def _win_to_wsl(p: str) -> str:
    p = p.replace("\\\\", "/")
    if len(p) >= 2 and p[1] == ":":
        drive = p[0].lower()
        return f"/mnt/{drive}{p[2:]}"
    return p


def _steam_library_roots() -> list[Path]:
    roots: set[Path] = set()
    if os.name == "nt":
        # native Windows
        pf = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        candidates = [Path(pf) / "Steam/steamapps/libraryfolders.vdf"]
        for drv in "cdefg":
            candidates.append(Path(f"{drv}:\\SteamLibrary\\steamapps\\libraryfolders.vdf"))
    else:
        home = Path.home()
        candidates = [
            home / ".steam/steam/steamapps/libraryfolders.vdf",
            home / ".local/share/Steam/steamapps/libraryfolders.vdf",
            home / "snap/steam/common/.local/share/Steam/steamapps/libraryfolders.vdf",
            home / ".var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/libraryfolders.vdf",
        ]
        for drv in "cdefg":
            candidates.append(Path(f"/mnt/{drv}/Program Files (x86)/Steam/steamapps/libraryfolders.vdf"))
            candidates.append(Path(f"/mnt/{drv}/SteamLibrary/steamapps/libraryfolders.vdf"))
    for vdf in candidates:
        if not vdf.is_file():
            continue
        for line in vdf.read_text(errors="ignore").splitlines():
            m = line.strip().split('"')
            if len(m) >= 3 and m[1] == "path":
                roots.add(Path(_win_to_wsl(m[3].strip())))
        roots.add(vdf.parent.parent)
    return sorted(roots)


def find_game_dir() -> Path | None:
    env = os.environ.get("DOW_GAME_DIR")
    if env and Path(env).is_dir():
        return Path(env)
    for root in _steam_library_roots():
        candidate = root / "steamapps/common" / GAME_FOLDER
        if candidate.is_dir():
            return candidate
        # case-insensitive fallback
        common = root / "steamapps/common"
        if common.is_dir():
            for sub in common.iterdir():
                if sub.name.lower() == GAME_FOLDER.lower() and sub.is_dir():
                    return sub
    return None


def _ensure_venv(extract_root: Path) -> Path:
    venv_dir = extract_root.parent / "sga-venv"
    if (venv_dir / "bin" / "relic").is_file() or (venv_dir / "Scripts" / "relic.exe").is_file():
        return venv_dir
    print("Setting up SGA extraction tool (relic-game-tool)...")
    venv.EnvBuilder(with_pip=True).create(venv_dir)
    pip = venv_dir / "bin/pip" if os.name != "nt" else venv_dir / "Scripts/pip.exe"
    subprocess.check_call([str(pip), "install", "--quiet", "relic-game-tool"])
    return venv_dir


def _relic_exe(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts/relic.exe" if os.name == "nt" else "bin/relic")


def extract_module(game_dir: Path, venv_dir: Path, extract_root: Path, module: str) -> None:
    sga = game_dir / module / f"{module}Data.sga"
    if not sga.is_file():
        print(f"warning: no {module}Data.sga at {sga}, skipping {module}", file=sys.stderr)
        return
    out = extract_root / module
    out.mkdir(parents=True, exist_ok=True)
    print(f"Extracting {sga.name} ... (this may take a few minutes)")
    relic = _relic_exe(venv_dir)
    subprocess.check_call([str(relic), "sga", "unpack", "-q", str(sga), "-o", str(out)])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--game-dir", type=Path, default=None)
    ap.add_argument("--extract-root", type=Path, default=None)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    extract_root = args.extract_root or Path(__file__).parent.parent.parent / ".copilot_workspace" / "extract"
    extract_root = extract_root.resolve()

    game_dir = args.game_dir
    if game_dir is None:
        game_dir = find_game_dir()
    if game_dir is None or not game_dir.is_dir():
        print("ERROR: could not auto-detect Dawn of War Definitive Edition.", file=sys.stderr)
        print("Set DOW_GAME_DIR or pass --game-dir.", file=sys.stderr)
        return 1
    print(f"Game dir: {game_dir}")

    missing = [
        m for m in MODULES
        if args.force or not _module_extracted(extract_root, m)
    ]
    if not missing:
        print(f"Extraction already present at {extract_root}; nothing to do.")
        return 0

    venv_dir = _ensure_venv(extract_root)
    for module in missing:
        extract_module(game_dir, venv_dir, extract_root, module)

    print(f"Extraction ready at {extract_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
