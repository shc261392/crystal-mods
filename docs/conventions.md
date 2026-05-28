# Repository conventions

## Game folder naming (`<normalized-game-name>/`)

- Lowercase, hyphen-separated, ASCII only.
- Use the **shortest unambiguous** form. Drop publisher/franchise prefixes when
  the title is unique enough; keep series prefixes when the suffix alone is
  ambiguous.
- Use the well-known abbreviation when one exists (`dow`, `dos2`, `botw`,
  `eldenring`).
- Edition / re-release suffix at the end: `-de` (definitive), `-remake`,
  `-remastered`, `-ee` (enhanced).

Examples:

| Game | Folder |
| --- | --- |
| Warhammer 40,000: Dawn of War – Definitive Edition | `dawn-of-war-de` |
| Divinity: Original Sin 2 | `divinity-original-sin-2` |
| Elden Ring | `elden-ring` |
| Cyberpunk 2077 | `cyberpunk-2077` |

If unsure, ask the user — do **not** invent a folder name with <90% confidence.

## Mod folder naming (`<game>/<mod-name>/`)

- Lowercase, hyphen-separated, ASCII.
- Prefer descriptive over branded names: `unofficial-tc-patch`,
  `wasd-camera-keybinds`, `4k-ui-scale`.
- Variants of the same mod share a prefix: `keybinds-vanilla`,
  `keybinds-wasd-camera`, `keybinds-wasd-camera-ingame`.

## `<game>/metadata.jsonc` schema

JSONC (JSON + comments + trailing commas). Sourced from PCGamingWiki via
`tools/python/pcgw-fetch`. Hand-edits are allowed but should be marked with
`"_manual": true` on overridden fields.

```jsonc
{
  "$schema": "../docs/schemas/game-metadata.schema.json",
  "pcgwPage": "Warhammer 40,000: Dawn of War – Definitive Edition",
  "displayName": "Warhammer 40,000: Dawn of War – Definitive Edition",
  "released": "2025-09-04",
  "developers": ["Relic Entertainment"],
  "publishers": ["SEGA"],
  "engine": ["Essence Engine 1"],
  "graphicsApi": ["Direct3D 9"],
  "stores": {
    "steam":  { "appId": "3556750" },
    "gog":    null,
    "epic":   null,
    "ubisoft": null
  },
  "os": {
    "windows": "primary",
    "linuxProton": "supported",   // "primary" | "supported" | "untested" | "unsupported"
    "macos":   "unsupported"
  },
  "modding": {
    "framework": null,            // e.g. "BepInEx", "UE4SS", "SMAPI"
    "vortexExtension": true
  },
  "links": {
    "pcgw": "https://www.pcgamingwiki.com/wiki/...",
    "nexus": "https://www.nexusmods.com/..."
  },
  // Fields below are populated by tools/python/pcgw-fetch.
  // Hand-edit only with "_manual": true to prevent overwrite on refresh.
  "_source": "pcgw-fetch v0.1.0",
  "_fetchedAt": "2026-05-29T00:00:00Z"
}
```

## Per-mod folder layout

```
<mod-name>/
├── README.md                 Install + uninstall + uninstall verification
├── modinfo.json              Machine-readable mod manifest
├── deploy.ps1                Windows / Vortex post-deploy
├── deploy.sh                 Linux / WSL2
├── uninstall.ps1
├── uninstall.sh
├── data/                     Mod source files (tracked)
├── scripts/                  Build / patch scripts
├── docs/                     Optional per-mod docs
├── vortex-ext/               Optional Vortex extension shipped with the mod
└── .gitkeep / LICENSE        License if it differs from repo default
```

### Required: `modinfo.json`

Minimal example:

```json
{
  "id": "unofficial-tc-patch",
  "name": "Unofficial Traditional Chinese Patch",
  "game": "dawn-of-war-de",
  "version": "1.0.0",
  "author": "Community",
  "category": "Localization",
  "platforms": ["windows", "linux-proton"],
  "supportedVersions": ["2.02.0"],
  "vortex": { "extensionId": "game-warhammer40kdawnofwar" },
  "links": {
    "nexus": "https://www.nexusmods.com/warhammerdawnofwardefinitiveedition/mods/41"
  }
}
```

## Deploy script contract

Both `deploy.ps1` and `deploy.sh` MUST:

1. Auto-detect the game install (Steam primary; allow `--game-path` override).
2. Take a backup before mutating any game file. Backups live in
   `<mod>/backup/` (gitignored) with a timestamped manifest.
3. Be idempotent — re-running must not double-apply.
4. Ship an `uninstall.{ps1,sh}` sibling that restores from the manifest.
5. Exit non-zero on failure with a clear message.

## Platform priority

| Tier | OS | Tooling |
| --- | --- | --- |
| Primary | Windows 11 | `.bat`, `.ps1`, Vortex |
| Dev | WSL2 (Ubuntu) | `.sh` mirroring `.ps1` |
| Secondary | Native Linux / Proton | `.sh` |
| Best-effort | macOS / Crossover | `.sh` |

## Storefront priority

Steam first (App ID auto-detect). GOG / Epic / Ubisoft Connect optional and
per-mod opt-in.
