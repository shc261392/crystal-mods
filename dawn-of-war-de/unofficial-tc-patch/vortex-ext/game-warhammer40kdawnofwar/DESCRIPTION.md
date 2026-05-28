# Dawn of War — Definitive Edition · Vortex Game Support Extension

Adds full mod management support for **Warhammer 40,000: Dawn of War — Definitive Edition** (Steam App ID 3556750) to Vortex.

---

## Game Detection

Automatically discovers the game installation via Steam (App ID `3556750`) and registers the executable `W40k.exe`.

---

## Mod Installers

### Locale Mod Installer *(priority 20)*

Handles Traditional Chinese, Simplified Chinese, Japanese, Korean, Russian, and all other locale mods.

**Detection** — an archive is identified as a locale mod when it contains any of:
- `Engine.ucs` or `EnginLoc.sga` (by filename)
- `data/font/`, `data/art/ui/`, or `data/sound/` (by path segment)
- An `Engine/Locale/` prefix already in the archive
- A known locale folder at the archive root (e.g. `Chinese/`, `English/`, `Japanese/`, …)

**Three archive layouts are handled automatically:**

| Layout | Example archive path | Deployed to |
|--------|----------------------|-------------|
| Full path present | `Engine/Locale/Chinese/Engine.ucs` | Deployed as-is (game-root-relative) |
| Locale folder at root | `Chinese/Engine.ucs` | `Engine/Locale/Chinese/Engine.ucs` |
| Files at locale root | `Engine.ucs`, `data/font/…` | `Engine/Locale/Chinese/Engine.ucs`, etc. |

### Root Mod Installer *(priority 50 — fallback)*

Handles all other mod types: SGA archives, race packs, map packs, gameplay scripts, and loose-file mods.

A single wrapper folder is automatically detected and stripped, so both wrapped (`MyMod/W40k/data/…`) and already-correct (`W40k/data/…`) archive layouts work without manual adjustment.

---

## Automatic SGA State Management

Dawn of War DE ships a packed locale archive (`EnginLoc.sga`) that takes priority over loose files. This extension hooks into Vortex's deploy/purge lifecycle to manage that automatically:

- **On deploy** — if loose locale mod files are present under `Engine/Locale/Chinese/data/`, `EnginLoc.sga` is renamed to `EnginLoc.sga.disabled` so the engine reads the loose files instead of the pack.
- **On purge** — `EnginLoc.sga.disabled` is restored to `EnginLoc.sga`, returning the game to its vanilla state.

A Vortex notification is displayed whenever the SGA state changes.

---

## Source Code

<https://github.com/shc261392/wh40k-dow-de-tc-mod/tree/master/vortex-ext/game-warhammer40kdawnofwar>
