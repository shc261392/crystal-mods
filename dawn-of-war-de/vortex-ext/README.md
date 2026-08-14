# Vortex Extension — Warhammer 40,000: Dawn of War - Definitive Edition

A [Vortex](https://www.nexusmods.com/about/vortex/) game extension for  
**Warhammer 40,000: Dawn of War – Definitive Edition** (Steam App ID `3556750`).

## Features

- **Auto-discovers** the game through Steam (App ID `3556750`)
- **Generic mod installer** handles any file replacement mod
- **Smart layout detection**:
  - Recognizes game-root-relative paths (`Engine/`, `W40k/`, `DXP2/`, `DXP3/`, etc.)
  - Auto-strips single wrapper folders when present
   - Defers `fomod/` installer archives to Vortex's built-in installer UI
  - Falls back to deploying files as-is
- **Case-insensitive** directory matching (handles `engine/`, `Engine/`, `ENGINE/` equally)
- **Production-ready**: Addresses all known edge cases from Vortex code review

## Installation

1. Download the extension ZIP from [GitHub Releases](https://github.com/shc261392/crystal-mods/releases)
2. Open Vortex → **Extensions** tab
3. Drag the ZIP onto the Extensions area (or use *Install from file*)
4. Click **Enable**
5. Restart Vortex

The game will appear under **Manage → Warhammer 40,000: Dawn of War - Definitive Edition**.

## Supported Mod Types

The extension handles **two kinds of mods**:

### 1. File-replacement mods → game directory

Packaged with game-root-relative paths; deployed into the game install folder:

- **Localization mods**: `Engine/Locale/Chinese/Engine.ucs`, `.fnt`, `.gfx`, `.sga`
- **Campaign data**: `W40k/`, `WXP/`, `DXP2/`, `DXP3/`
- **UI/Art assets**: `Engine/Data/art/`, `DoWDE/`
- **Tools**: `Tools/`, `Dev/`

### 2. Standalone `.module` mods → user-profile mods folder

Authored Dawn of War mods (an archive containing a `*.module` file) are **not**
loaded from the game directory. The Relic engine auto-loads them from the
user-profile mods folder, so the extension deploys them there instead:

- **Windows**: `%APPDATA%\Relic Entertainment\Dawn of War\mods\`
- **Linux/Proton**: `<library>/steamapps/compatdata/3556750/pfx/drive_c/users/steamuser/AppData/Roaming/Relic Entertainment/Dawn of War/mods/`

Expected archive layout (the mod keeps its own folder):

```
MyMod/
├── MyMod.module
├── pipeline.ini
└── Mod/Data/…
```

→ Deploys to `…/mods/MyMod/…`. Extra wrapper folders are stripped, and a loose
`.module` at the archive root is wrapped under a folder named after it.

### Layout A: Game-Root-Relative

Files already start with recognized game directories:

```
my-mod-v1.0.zip
├── Engine/Locale/Chinese/Engine.ucs
├── Engine/Locale/Chinese/data/font/font.fnt
└── W40k/data/attrib/gameplay.lua
```

**→ Deploys as-is** (paths preserved)

### Layout B: Wrapper Folder

Mod content wrapped in a single top-level folder:

```
my-mod-v1.0.zip
└── my-mod-v1.0/
    ├── Engine/Locale/Chinese/Engine.ucs
    └── DXP2/data/attrib/gameplay.lua
```

**→ Wrapper stripped** → deploys `Engine/...` and `DXP2/...` to game root

### Edge Cases Handled

✅ **Single file at root** (e.g., `readme.txt`)  
→ Deploys to game root, not treated as wrapper

✅ **FOMOD installer archives** (`fomod/ModuleConfig.xml`)  
→ Not handled by the generic installer; Vortex presents the installer choices instead

✅ **Lowercase paths** (e.g., `engine/locale/`)  
→ Correctly recognized via case-insensitive matching

✅ **Mixed content**  
→ Fallback deploys everything to game root if layout is unclear

## Game Directory Structure

```
Dawn of War Definitive Edition/
├── W40k.exe                    ← Main executable
├── W40kME.exe                  ← Mission Editor
├── W40k/                       ← Base game (DoW 2004)
├── WXP/                        ← Winter Assault expansion
├── DXP2/                       ← Dark Crusade expansion
├── DXP3/                       ← Soulstorm expansion
├── DoWDE/                      ← Definitive Edition content
├── Engine/
│   ├── Locale/
│   │   ├── Chinese/            ← Traditional Chinese locale
│   │   ├── English/            ← English locale
│   │   └── ... (13 locales total)
│   └── Data/
├── Dev/                        ← DevMode tools
└── Tools/                      ← Modding utilities
```

Recognized root directories: `W40k`, `WXP`, `DXP2`, `DXP3`, `DoWDE`, `Engine`, `Dev`, `Tools`

## Development

This extension is a plain **CommonJS module** — no build step required.

**Quick start:**

1. Clone the repo:
   ```bash
   git clone https://github.com/shc261392/crystal-mods.git
   cd crystal-mods/dawn-of-war-de/vortex-ext
   ```

2. Edit `game-warhammer40kdawnofwar/index.js`

3. Package for testing:
   ```bash
   make package
   ```

4. Install to Vortex:
   - Drag `dist/vortex-warhammer40kdawnofwar-v*.zip` onto Vortex Extensions tab
   - Restart Vortex to test

**Resources:**

- [Vortex Extension API](https://github.com/Nexus-Mods/Vortex/wiki/MODDINGWIKI-Developers-General-Introduction-to-Vortex-extensions)
- [Example extensions](https://github.com/Nexus-Mods/vortex-games)
- [Steam App ID lookup](https://steamdb.info/)

## Troubleshooting

### Game Not Detected

**Symptoms:** DoW:DE doesn't appear in Vortex supported games list

**Solutions:**
1. Verify Steam installation:
   - Open Steam → Library → Warhammer 40,000: Dawn of War - Definitive Edition
   - Right-click → Properties → Local Files → Browse
   - Confirm `W40k.exe` exists in the folder
2. Check Vortex settings:
   - Settings → Games → Scan for games
   - Manually add game path if auto-detection fails
3. Verify extension is enabled:
   - Extensions tab → ensure "Dawn of War - Definitive Edition" is enabled
   - Restart Vortex after enabling

### Mod Files Not Deploying

**Symptoms:** Mod shows as active in Vortex but files don't appear in game

**Solutions:**
1. Check deployment path:
   - Mods tab → click mod → *Open in File Manager*
   - Verify files deployed to correct location (compare with game directory structure)
2. Verify game directory permissions:
   - Right-click game folder → Properties → Security (Windows)
   - Ensure your user account has *Write* permission
3. Try manual deployment:
   - Disable deployment in Vortex
   - Deploy again (Vortex will re-create symlinks/hardlinks)
4. Check for conflicts:
   - Vortex notification panel may show file conflicts
   - Resolve via conflict resolution dialog

### Mod Shows Errors in Vortex

**Common issues:**

1. **"Invalid archive format"**
   - Archive likely corrupted during download
   - Re-download and try again
   
2. **"No valid installation path found"**
   - Mod packaged incorrectly (missing game-root directories)
   - Check with mod author or try manual installation
   
3. **"Permission denied"**
   - Game directory is read-only or in protected location
   - Run Vortex as administrator (Windows) or fix permissions (Linux)

### Extension Development Issues

**Debugging:**

1. Enable Vortex developer console:
   - Settings → Interface → Enable Advanced Mode
   - Help → Toggle Developer Tools (F12)
   
2. Check extension logs:
   - `%APPDATA%/Vortex/vortex.log` (Windows)
   - `~/.config/Vortex/vortex.log` (Linux)
   
3. Test with sample mod:
   - Create test archive: `test-mod.zip` containing `Engine/test.txt`
   - Install via Vortex
   - Check deployment to `<game>/Engine/test.txt`

---

## Support

**Extension Issues:**
- GitHub Issues: [https://github.com/shc261392/crystal-mods/issues](https://github.com/shc261392/crystal-mods/issues)
- Include: Vortex version, extension version, error messages, mod archive structure

**Vortex General Help:**
- [Vortex Support Wiki](https://wiki.nexusmods.com/index.php/Vortex)
- [Nexus Mods Forums](https://forums.nexusmods.com/index.php?/forum/4306-vortex-support/)

**Dawn of War Modding:**
- [Relicnews Modding Forums](https://www.relicnews.com/forums/)
- [PCGamingWiki: Dawn of War](https://www.pcgamingwiki.com/wiki/Warhammer_40,000:_Dawn_of_War)

---

## License

MIT — See [LICENSE](../../LICENSE)

---

## Version

**Extension:** 1.0.4  
**Vortex Compatibility:** 1.10+  
**Game:** Steam App ID 3556750 (Warhammer 40,000: Dawn of War - Definitive Edition)
