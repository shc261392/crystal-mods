# Vortex Extension — Warhammer 40,000: Dawn of War — Definitive Edition

A [Vortex](https://www.nexusmods.com/about/vortex/) game extension that adds
modding support for **Warhammer 40,000: Dawn of War — Definitive Edition**.

## Features

- Auto-detects Steam (AppID `3556750`) install
- Generic file-replacement installer supporting all mod types
- Handles both game-root-relative archives and wrapper-folder layouts
- Case-insensitive directory matching for cross-platform compatibility

## Local development / install

1. Copy this folder to your Vortex plugins directory:
   - Windows: `%APPDATA%\Vortex\plugins\game-warhammer40kdawnofwar\`
2. Start Vortex. The extension will load on launch.
3. Add the game from the *Games* tab. Vortex should auto-detect it.

When iterating on `index.js`, restart Vortex (or use *File → Restart*) to
reload the extension.

## Packaging for Nexus

Per the [Vortex wiki](https://github.com/Nexus-Mods/Vortex/wiki/How-to-package-a-game-extension),
the archive MUST contain the files at the top level (no nested wrapper folder):

```
game-warhammer40kdawnofwar-1.0.6.zip
├── info.json
├── gameart.jpg
├── index.js
└── DESCRIPTION.md     (optional)
```

### Build and package

1. Increment `version` in `info.json` (semver)
2. Run the package script (from this directory):
   ```bash
   npm run package
   ```
   This produces `dist/game-warhammer40kdawnofwar-<version>.zip` at the repo root.
3. Verify the archive contains only the files above (no `package.json`, `node_modules`, or scripts):
   ```bash
   unzip -l dist/game-warhammer40kdawnofwar-*.zip
   ```
4. Submit the zip per [How to submit a game extension for review](https://github.com/Nexus-Mods/Vortex/wiki/How-to-submit-a-game-extension-for-review).

## Files

| File            | Required | Notes                                                   |
| --------------- | -------- | ------------------------------------------------------- |
| `info.json`     | yes      | Metadata. `version` must match the Nexus upload exactly |
| `index.js`      | yes      | Extension entry point                                   |
| `gameart.jpg`   | yes      | 640×360 JPG, ≤1 MB, no text overlay                     |
| `DESCRIPTION.md`| no       | Useful for the Nexus mod page                           |

## Important: gameart.jpg

The repo ships a placeholder `gameart.jpg`. **Replace it with proper game
art before submitting to Nexus** (640×360, 16:9, dark-bg-safe, no text — Vortex
overlays the game name automatically). See
[SteamGridDB](https://www.steamgriddb.com/) for source images.
