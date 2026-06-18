# Dawn of War — Definitive Edition · Vortex Game Support Extension

Adds full mod management support for **Warhammer 40,000: Dawn of War — Definitive Edition** (Steam App ID 3556750) to Vortex.

---

## Game Detection

Automatically discovers the game installation via Steam (App ID `3556750`) and registers the executable `W40k.exe`.

---

## Mod Installer

### Generic File Replacement Installer *(priority 20)*

Handles **all mod types** by deploying files to their game-root-relative paths. Supports:

- Localization mods (`Engine/Locale/*/`)
- Campaign data (`W40k/`, `WXP/`, `DXP2/`, `DXP3/`)
- UI/Art assets (`Engine/Data/`, `DoWDE/`)
- Tools and editors (`Tools/`, `Dev/`)

**Two archive layouts are supported automatically:**

| Layout | Example archive structure | Result |
|--------|---------------------------|--------|
| **Game-root-relative** | `Engine/Locale/Chinese/Engine.ucs`<br>`DXP2/data/attrib/gameplay.lua` | Deployed as-is (paths preserved) |
| **Wrapper folder** | `my-mod-v1.0/`<br>`  Engine/Locale/Chinese/Engine.ucs`<br>`  DXP2/data/attrib/gameplay.lua` | Wrapper stripped → files deploy to game root |

**Edge cases handled:**
- ✅ Single files at root (`readme.txt`) — deployed to game root, not treated as wrapper
- ✅ Lowercase directory names (`engine/locale/`) — case-insensitive matching ensures correct detection
- ✅ Mixed content — falls back to deploying everything to game root

**Recognized game directories:**  
`W40k`, `WXP`, `DXP2`, `DXP3`, `DoWDE`, `Engine`, `Dev`, `Tools`

---

## Technical Details

**Implementation:** Simple, maintainable CommonJS module using Vortex API

**Key features:**
- Case-insensitive directory matching for cross-platform compatibility
- Uses `path.posix.relative()` for robust wrapper stripping
- Guards against edge cases identified in Vortex code review
- No special processing or file exclusions — deploy as-is

**Version:** 1.0.4 (June 2026)

---

## Source Code

<https://github.com/shc261392/crystal-mods/tree/main/dawn-of-war-de/vortex-ext/game-warhammer40kdawnofwar>
