# Nexus Mods description — Vortex Game Extension

> Paste into the Nexus page for the Vortex extension.

---

## Black Book — Vortex Support (Game Extension)

A **Vortex game extension** that adds mod management support for **Black Book**
(Steam App ID `1138660`, Windows).

### What it does

- **Game detection** via Steam (App ID `1138660`).
- **Mod deployment** to the game root for:
  - **Localization mods** — `Black Book_Data/StreamingAssets/Config/**` (e.g.
    the Traditional Chinese `config_zh.yaml` files).
  - **BepInEx plugins** — `BepInEx/plugins/*.dll` and their data folders.
  - **BepInEx framework** — `winhttp.dll`, `doorstop_config.ini`,
    `.doorstop_version` and `BepInEx/` (BepInEx 5.4.23.5 x64).
- **Automatic backup / restore** — Vortex renames overwritten game files to
  `*.vortex_backup` on deploy and restores them on purge, so your install stays
  clean and reversible.
- Handles both **game-root-relative** archives and **single-wrapper-folder**
  archives (the wrapper is stripped automatically).

### Installation

Install through Vortex's **Extensions** page (drag the extension archive in, or
use *Install from File*), then restart Vortex. The game appears under *Games* and
can be managed like any other.

### Recommended install order

Black Book's Traditional Chinese localization is split into two files, both
deployed by this extension:

1. **BepInEx Framework** — the BepInEx 5.4.23.5 x64 runtime (install once).
2. **Traditional Chinese Localization** — the `config_zh.yaml` files plus the
   `BlackBookTcFont` BepInEx plugin.

Install this extension, add Black Book in Vortex, then drag in the framework and
localization zips and click **Deploy Mods**. Launch the game once after the
framework is installed so BepInEx creates its working folders.

### Why it's needed

Black Book isn't natively supported by Vortex. This extension enables one-click
install/deploy/uninstall of localization and other mods, including mods that
ship the BepInEx runtime and plugins.

### Version

- **1.0.0** — initial release: Steam game detection and a generic installer for
  localization data, BepInEx plugins and the BepInEx framework.

### Notes

- Windows. Black Book's Steam build is Windows-only.
- Open source; contributions/issues welcome on the project repository.
- Not affiliated with Morteshka or HypeTrain Digital.
