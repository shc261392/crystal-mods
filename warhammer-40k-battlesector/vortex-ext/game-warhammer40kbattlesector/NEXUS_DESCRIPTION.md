# Nexus Mods description — Vortex Game Extension

> Paste into the Nexus page for the Vortex extension.

---

## Warhammer 40,000: Battlesector — Vortex Support (Game Extension)

A **Vortex game extension** that adds mod management support for
**Warhammer 40,000: Battlesector** (Steam / GOG).

### What it does

- **Game detection** via Steam (App ID 1295500) and GOG (1248481392).
- **Mod deployment** to the game root for:
  - **Asset-replacement mods** — `sharedassets*.assets`, `.resS`, `.bundle`,
    `resources.assets`, launcher files, etc.
  - **BepInEx runtime mods** — the BepInEx framework (`winhttp.dll` + `BepInEx/` +
    `dotnet/`) and BepInEx plugins (`BepInEx/plugins/*.dll`).
- **Automatic backup / restore** — Vortex renames overwritten game files to
  `*.vortex_backup` on deploy and restores them on purge, so your install stays
  clean and reversible.
- Handles both **game-root-relative** archives and **single-wrapper-folder**
  archives (auto-strips the wrapper).

### Installation

Install through Vortex's Extensions page (drag the extension archive in, or use
"Install from File"), then restart Vortex. The game will appear under Games and can
be managed like any other.

### Why it's needed

Battlesector isn't natively supported by Vortex. This extension enables one-click
install/deploy/uninstall of localization and other mods, including mods that ship
the BepInEx modding framework alongside asset files.

### Version

- **1.1.0** — added BepInEx framework/plugin deployment support (recognizes
  `BepInEx/`, `dotnet/`, and the `winhttp.dll` / `doorstop_config.ini` root files).
- 1.0.0 — initial release (asset-replacement mods).

### Notes

- Windows primary; Linux/Proton supported by Vortex's usual mechanisms.
- Open source; contributions/issues welcome on the project repository.
