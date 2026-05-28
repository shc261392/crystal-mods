# Vortex Extension — Dawn of War Definitive Edition

A [Vortex](https://www.nexusmods.com/about/vortex/) game extension for  
**Warhammer 40,000: Dawn of War – Definitive Edition** (Steam App ID `3556750`).

## Features

- Auto-discovers the game through Steam (App ID `3556750`)
- Installs **locale mods** (`.ucs`, `.fnt`, `.gfx`, sound files) to  
  `Engine/Locale/<Locale>/`, defaulting to `Chinese` when no locale is specified
- Installs **general game-root mods** (SGA archives, race packs, map packs,  
  gameplay scripts) to the game root, stripping a single wrapper folder where needed
- Two installers run in priority order — the locale installer fires first;  
  unmatched mods fall through to the root installer

## Installation

1. Close Vortex.
2. Copy `game-warhammer40kdawnofwar/` into your Vortex plugins folder:
   ```
   %APPDATA%\Roaming\Vortex\plugins\game-warhammer40kdawnofwar\
   ```
3. Optionally place a 640 × 360 JPEG named `gameart.jpg` in the same folder  
   (Steam CDN banner, or any representative image).
4. Re-open Vortex — **Warhammer 40,000: Dawn of War - Definitive Edition**  
   will appear under *Supported Games*.

## ⚠️ Locale Mods: SGA Disable Step Required

When a locale mod is installed (e.g. the Traditional Chinese Font Fix),  
the game's packed locale archive must be disabled so the engine loads  
loose files instead:

```
Engine/Locale/Chinese/EnginLoc.sga  →  EnginLoc.sga.disabled
```

Run **`deploy.sh`** (Linux/WSL) or **`deploy.ps1`** (Windows) from this  
repository **after** Vortex finishes deploying a locale mod.  
The deploy script performs the SGA rename step and any font-fix passes  
automatically.

## Mod Archive Layouts

The extension detects mod type from archive content:

| Archive content | Detected as | Install target |
|---|---|---|
| Contains `Engine.ucs` or `EnginLoc.sga` | Locale mod | `Engine/Locale/Chinese/` |
| Contains `data/font/`, `data/art/ui/`, or `data/sound/` paths | Locale mod | `Engine/Locale/Chinese/` |
| Paths begin with `Engine/Locale/<name>/` | Locale mod | `Engine/Locale/<name>/` (preserved) |
| Top-level folder is a known locale (`Chinese`, `English`, …) | Locale mod | `Engine/Locale/<name>/` |
| Paths begin with `W40k/`, `WXP/`, `Engine/`, `DXP2/`, … | Root mod | Game root (preserved) |
| Single wrapper folder around game content | Root mod | Game root (wrapper stripped) |
| Everything else | Root mod | Game root |

## Game Structure Reference

```
Dawn of War Definitive Edition/
├── W40k.exe                    ← main executable
├── W40kME.exe                  ← Mission Editor
├── W40k/                       ← base game data
├── WXP/                        ← Winter Assault
├── DXP2/                       ← Dark Crusade
├── DXP3/                       ← Soulstorm
├── DoWDE/                      ← Definitive Edition extras
└── Engine/
    └── Locale/
        ├── Chinese/            ← Traditional Chinese locale
        │   ├── Engine.ucs      ← string table (our mod replaces this)
        │   ├── EnginLoc.sga    ← packed locale archive (must be disabled)
        │   └── data/
        │       ├── font/       ← FNT descriptor files
        │       ├── art/ui/swf/ ← GFX/SWF UI assets
        │       └── sound/      ← audio banks
        ├── English/
        └── … (13 locales total)
```

## Development

This extension is a plain CommonJS module — **no build step is required**.  
Edit `index.js` directly and reload Vortex to test changes.

To extend support (e.g. auto-disable `EnginLoc.sga` on deploy, or add  
launch tool registration for `W40kME.exe`), refer to the  
[Vortex Extension API wiki](https://github.com/Nexus-Mods/Vortex/wiki/MODDINGWIKI-Developers-General-Introduction-to-Vortex-extensions).
