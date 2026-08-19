# Skip All Intros — Dawn of War Definitive Edition

A small **Vortex-installable** mod that makes every intro / cinematic movie in
*Warhammer 40,000: Dawn of War – Definitive Edition* play for an instant instead
of forcing you to sit through them (or press Esc each time).

## What it disables

| Folder | Files replaced |
|--------|----------------|
| `Engine/Movies/` | `blur_intro.webm`, `relic_intro.webm`, `warhammer_intro.webm`, `rivalry.webm`, `credits.avi`, `dow_intro.avi`, `wxp_credits.avi` |
| `DXP2/Movies/` | `dark_crusade_intro.webm` (Dark Crusade campaign intro) |
| `DXP3/Movies/` | `soulstorm_intro.webm` (Soulstorm campaign intro) |

> **Path note:** the campaign intros live in `DXP2/Movies/` and `DXP3/Movies/`
> — not `DXP2/Engine/Movies/`. There is no `Engine` subfolder under DXP2/DXP3.

## How it works (and why not 0-byte stubs)

The engine plays movies via the `.lua` files that sit next to each movie (e.g.
`Engine/Movies/blur_intro.lua`). Those `.lua` files only declare the movie
filename and an optional external audio stream — they carry **no "enabled"
flag**, so you can't cleanly switch a movie off by editing them. The engine
itself triggers playback.

This mod replaces each movie with a **0-byte empty file**. The engine finds the
file, tries to open it, and — per its own strings (`MOV -- Movie does not
exist`, `MOV -- Error starting movie`) — errors out and skips playback. Because
the movie fails to start, its declared `audio = "..."` stream is never played
either, so the whole intro (picture and audio) is skipped.


## Build (Linux / WSL2 / Windows)

Requires `python3` (and `make` + `zip` on Linux/WSL2). No ffmpeg needed.

```bash
cd dawn-of-war-de/skip-all-intro
make build            # Linux / WSL2  → dist/skip-all-intro-v0.1.0.zip
# or
bash build.sh         # Linux / WSL2
.\build.ps1           # Windows PowerShell
```

Output: `dist/skip-all-intro-v0.1.0.zip` (9 empty files, ~4 KB).

Override the version: `make build VERSION=0.1.1` / `bash build.sh --version 0.1.1`.

## Install (Vortex / manual)

**Vortex:** drag `dist/skip-all-intro-v0.1.0.zip` onto Vortex, click *Install*,
then *Deploy Mods*. Files deploy to `Engine/Movies/`, `DXP2/Movies/`,
`DXP3/Movies/` in the game install. Uninstall / purge in Vortex to restore the
originals (Vortex keeps the vanilla files untouched).

**Manual:** extract the zip into your game root so the `Engine/`, `DXP2/`,
`DXP3/` folders merge with the existing ones, overwriting the movie files. Back
up the originals first if you want an easy manual revert.

## Repository layout

```
skip-all-intro/
├── Makefile                    # build / generate / verify / lint
├── pyproject.toml              # uv project (stdlib only)
├── modinfo.json                # mod metadata (not shipped in the zip)
├── README.md
├── build.sh                    # Linux / WSL2 build
├── build.ps1                   # Windows build
├── scripts/
│   └── generate_movies.py      # generator for the 0-byte replacements
├── mod/                        # generated mod tree (gitignored)
└── dist/                       # build output (gitignored)
```
