# Vortex Extension — Black Book

A [Vortex](https://www.nexusmods.com/about/vortex/) game extension that adds
modding support for **Black Book** (Steam App ID `1138660`, Windows).

## Features

- Auto-detects the Steam install (App ID `1138660`)
- A generic installer that deploys mod files to their game-root-relative paths:
  - **Localization data** — `Black Book_Data/StreamingAssets/Config/**/config_zh.yaml`
  - **BepInEx plugins** — `BepInEx/plugins/**`
  - **BepInEx framework** — root-level `winhttp.dll`, `doorstop_config.ini`,
    `.doorstop_version` plus `BepInEx/`
- Handles both **game-root-relative** archives and **single-wrapper-folder**
  archives (the wrapper is stripped automatically)
- Overwritten originals (e.g. the game's Simplified Chinese `config_zh.yaml`
  files) are backed up and restored automatically by Vortex
  (`*.vortex_backup`); *Purge Mods* reverts the game to vanilla — no manual
  restore needed

Only the **Steam** install is registered (App ID `1138660`). Black Book is also
sold on GOG (GOG id `2098791460`), but GOG discovery is not implemented in this
extension — see *Open items* below. The Steam build is Windows-only.

## The three Black Book mods and install order

The Traditional Chinese localization is split into a shared runtime plus the
localization itself. Install them in this order:

1. **BepInEx Framework** (`bepinex-framework-v*.zip`) — the BepInEx 5.4.23.5
   runtime. Required by the localization's plugin. Install once.
2. **Traditional Chinese Localization** (`tc-localization-v*.zip`) — the
   `config_zh.yaml` files plus the `BlackBookTcFont` BepInEx plugin.
3. **This extension** (`game-black-book-*.zip`) — install it first of all if
   Vortex does not yet list Black Book under *Games*; the two mods above are
   deployed by it.

In practice: install the extension, add Black Book in Vortex, then drag in the
BepInEx Framework and the TC localization zips and click **Deploy Mods**.
Launch the game once after the framework is installed so BepInEx creates its
working folders.

## Local development / install

1. Copy this folder to your Vortex plugins directory:
   - Windows: `%APPDATA%\Vortex\plugins\game-black-book\`
2. Start Vortex. The extension loads on launch.
3. Add the game from the *Games* tab. Vortex should auto-detect it.

When iterating on `index.js`, restart Vortex (or use *File → Restart*) to reload
the extension.

## Packaging for Nexus

Per the [Vortex wiki](https://github.com/Nexus-Mods/Vortex/wiki/How-to-package-a-game-extension),
the archive MUST contain the files at the top level (no nested wrapper folder):

```
game-black-book-1.0.0.zip
├── info.json
├── index.js
├── gameart.jpg
└── README.md          (optional)
```

### Build and package

From this directory:

```bash
node scripts/package.js
```

This produces `../dist/game-black-book-<version>.zip` (i.e.
`black-book/vortex-ext/dist/`), containing only the four files above — no
`scripts/`, no nested folder. Verify with:

```bash
unzip -l ../dist/game-black-book-*.zip
```

## Files

| File          | Required | Notes                                                   |
| ------------- | -------- | ------------------------------------------------------- |
| `info.json`   | yes      | Metadata. `version` must match the Nexus upload exactly |
| `index.js`    | yes      | Extension entry point                                   |
| `gameart.jpg` | yes      | 640×360 JPG, ≤1 MB, no text overlay                     |
| `README.md`   | no       | Useful for the Nexus mod page                           |
| `scripts/`    | no       | Packaging + game-art helpers (not shipped in the zip)   |

## gameart.jpg

`gameart.jpg` in this folder is a 640×360 crop of the official Steam header
image (App ID `1138660`). Regenerate or replace it with:

```bash
bash scripts/fetch-gameart.sh
```

**Hand-review before Nexus submission** — 640×360, dark-background-safe, no text
(Vortex overlays the game name automatically). See
[SteamGridDB](https://www.steamgriddb.com/) for alternative source images.

## Open items

- The Nexus mod page ID for this extension is unknown; `info.json` intentionally
  carries no Nexus mod ID. Add it once the page exists.
- **GOG is not registered.** `black-book/metadata.jsonc` lists GOG id
  `2098791460`, and the live GOG API confirms a *Black Book* release with that id
  (slug `black_book`). This contradicts the assumption that Black Book is
  Steam-only. Adding it is a one-line change (`findByAppId([STEAM_APP_ID,
  GOG_APP_ID])` plus `details.gogAppId`), but it was deliberately left out of
  this revision pending a decision.
