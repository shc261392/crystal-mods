# Warhammer 40,000: Battlesector

Community mods for **Warhammer 40,000: Battlesector** (Black Lab Games / Slitherine).

## Available Mods

### [BepInEx Framework](bepinex-framework/)
The BepInEx 6 (IL2CPP) modding runtime, packaged as a one-click install. A
**shared dependency** required by plugin mods (TC Localization's font fix, Red
Laser Lasgun). Install once; adds no game-file changes. Ships the official
BepInEx Bleeding-Edge build #785 (SHA-256 documented on the mod page).

- **Installation:** Vortex Mod Manager (install first, launch game once)
- **Status:** Packaged v1.0.0
- **Repository:** [bepinex-framework/](bepinex-framework/)

### [TC Localization](tc-localization/)
Traditional Chinese (zh-TW) localization mod. Directly patches the game's asset bundle to replace Simplified Chinese with Traditional Chinese. **In-game:** Select **Chinese (Simplified)** locale. **Requires the BepInEx Framework mod** (for its runtime font fix).

- **Installation:** Vortex Mod Manager (recommended) or script-based deploy
- **Requires:** BepInEx Framework
- **Status:** Ready for testing
- **Repository:** [tc-localization/](tc-localization/)

### [The Great Crusade](the-great-crusade/)
Gameplay tuning for the Crusade / Planetary Supremacy (Warzone) roguelite: fast
flat leveling (+100 XP/level), max level raised to 15 for more upgrade picks,
top-tier (Rare/Legendary) upgrade cards guaranteed at the upper levels (~level 8+,
with a small fallback so the offer never empties), and reduced per-tier upgrade
point-costs. Data-only asset edit; levers were validated in-game.

- **Installation:** Vortex Mod Manager (recommended) or script-based deploy
- **Builds:** standalone, plus a TC-localization-compatible build (optional file)
- **Status:** Built; core levers validated in-game
- **Repository:** [the-great-crusade/](the-great-crusade/)

### [Army Painter](army-painter/)
BepInEx plugin that recolors the **local player's army** at runtime — primary +
secondary paint colours (e.g. Blood Angels red → Ultramarines blue) — with an
in-game color-changing UI (F10 or on-screen button). Per-faction schemes persist
in the BepInEx config; new units are auto-repainted. Uses MaterialPropertyBlock +
cached albedo remap, so **no game asset is modified** and **Reset** fully
restores the original paint. **Requires the BepInEx Framework mod.**

- **Installation:** Vortex Mod Manager (install BepInEx Framework first)
- **Requires:** BepInEx Framework
- **Status:** Built v1.0.0; DiagMode provided for in-game validation
- **Repository:** [army-painter/](army-painter/)

### [Red Laser Lasgun](red-laser-lasgun/)
BepInEx plugin that renders the Astra Militarum lasgun as a glowing red laser beam
(muzzle → target) for all AM las weapons, with zero side effects on other weapons.
**Requires the BepInEx Framework mod.**

- **Installation:** Vortex Mod Manager (install BepInEx Framework first)
- **Requires:** BepInEx Framework
- **Status:** Built v1.1.0; validated in-game
- **Repository:** [red-laser-lasgun/](red-laser-lasgun/)

## Vortex Extension

### [Game Extension](vortex-ext/game-warhammer40kbattlesector/)
Vortex mod manager extension that enables modding support for Battlesector.

- **Features:**
  - Auto-detects Steam and GOG installations
  - Automatic backup of `sharedassets1.assets` on first deploy
  - Custom installer for asset-replacement mods

- **Installation:**
  - Download from Nexus Mods or local folder
  - Drag onto Vortex **Extensions** tab → **Enable**
  - Restart Vortex

## Quick Start

### For Mod Users

1. Install Vortex Mod Manager
2. Drag the Vortex extension zip onto Vortex
3. Install the TC Localization mod via Vortex
4. Click **Deploy Mods**
5. Launch the game

### For Mod Developers

See individual mod folders for build/development instructions:
- [TC Localization Development](tc-localization/README.md)

---

## Project Structure

```
warhammer-40k-battlesector/
├── metadata.jsonc                    # Game metadata (engine, stores, etc.)
├── README.md                         # This file
├── tc-localization/                  # TC localization mod
│   ├── README.md
│   ├── modinfo.json
│   ├── deploy.sh / deploy.ps1
│   ├── uninstall.sh / uninstall.ps1
│   ├── dist/                         # Built assets (ready to deploy)
│   ├── source/                       # Extracted game sources
│   ├── config/                       # Build configuration
│   └── tools/scripts/                # Build & deploy utilities
├── the-great-crusade/                # Crusade-mode gameplay tuning mod
│   ├── README.md
│   ├── build.py                      # Tuned config as code
│   ├── Makefile                      # standalone / tccompat targets
│   ├── deploy.sh / deploy.ps1
│   ├── uninstall.sh / uninstall.ps1
│   └── dist/                         # Built ZIPs
└── vortex-ext/
    └── game-warhammer40kbattlesector/    # Vortex extension
        ├── index.js
        ├── info.json
        ├── gameart.png
        └── README.md
```

---

## Links

- **Game:** [Steam](https://store.steampowered.com/app/1295500/Warhammer_40000_Battlesector/) · [GOG](https://www.gog.com/game/warhammer_40k_battlesector)
- **Nexus Mods:** [WH40K Battlesector Mods](https://www.nexusmods.com/warhammer40kbattlesector)
- **PCGamingWiki:** [Warhammer 40,000: Battlesector](https://www.pcgamingwiki.com/wiki/Warhammer_40%2C000%3A_Battlesector)

## Research provenance (for contributors)

- Manual reference source: `.copilot_workspace/battlesector-data/Battlesector_manual_EBOOK.pdf`
- Structured mechanics/localization source: `.copilot_workspace/battlesector-data/**`
- Precedence rule: when manual text conflicts with extracted game data,
  **extracted game data is authoritative**.

