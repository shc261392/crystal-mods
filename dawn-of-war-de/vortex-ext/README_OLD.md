# Vortex Extension — Warhammer 40,000: Dawn of War - Definitive Edition

A [Vortex](https://www.nexusmods.com/about/vortex/) game extension for  
**Warhammer 40,000: Dawn of War – Definitive Edition** (Steam App ID `3556750`).

## Features

- **Auto-discovers** the game through Steam (App ID `3556750`)
- **Generic mod installer** handles any file replacement mod
- **Smart layout detection**:
  - Recognizes game-root-relative paths (`Engine/`, `W40k/`, `DXP2/`, `DXP3/`, etc.)
  - Auto-strips single wrapper folders when present
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

The extension handles **any mod** packaged with game-root-relative paths:

- **Localization mods**: `Engine/Locale/Chinese/Engine.ucs`, `.fnt`, `.gfx`, `.sga`
- **Campaign data**: `W40k/`, `WXP/`, `DXP2/`, `DXP3/`
- **UI/Art assets**: `Engine/Data/art/`, `DoWDE/`
- **Tools**: `Tools/`, `Dev/`

Mods can be packaged in two ways:

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
    ├── EnginLocMod.sga
    └── modinfo.json
```

#### Step 4: Deploy via Vortex

- Drag zip onto Vortex
- Extension detects as locale SGA mod
- Vortex copies `EnginLocMod.sga` to `Engine/Locale/Chinese/`
- Engine loads it alongside vanilla SGA

**✅ Advantages:**
- Compact (60–80MB vs 200MB+)
- Professional packaging
- Preserves mod integrity

**⚠️ Trade-offs:**
- Requires Archive.exe + buildfile setup
- CRLF line endings mandatory (LF fails silently)
- Not easily inspectable once packed

---

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

---

## Archive.exe Reference

**Location in Game:** `<game>/archive/Archive.exe`

**Command Syntax:**
```bash
Archive.exe [-a <archive.sga> [-c <buildfile> -r <rootpath>] | -e <target> | -l | -t]
```

| Flag | Purpose | Example |
|------|---------|---------|
| `-a` | Create or list archive | `Archive.exe -a mod.sga` |
| `-c` | Buildfile path | `Archive.exe -c build.txt` |
| `-r` | Root directory to pack | `Archive.exe -r ./data` |
| `-e` | Extract to folder | `Archive.exe -a mod.sga -e ./extract` |
| `-l` | List archive contents | `Archive.exe -a mod.sga -l` |
| `-t` | Test archive integrity | `Archive.exe -a mod.sga -t` |

**Important:**
- Buildfile **must** have CRLF (Windows) line endings — LF fails silently
- Paths with spaces must be quoted
- Test all builds with `-t` before deployment
- Maximum SGA size: 4 GB

---

## Troubleshooting

### Tofu Boxes (□□□) in Game

**Cause:** Broken `fontdecor.gfx` file (missing glyph tables)

**Fix:**
1. Ensure `fontdecor.gfx` is NOT included in deployment
2. Verify vanilla `fontdecor.gfx` (8.7MB) exists in game installation
3. See [FONTDECOR_ROOT_CAUSE_ANALYSIS.md](../unofficial-tc-patch/docs/FONTDECOR_ROOT_CAUSE_ANALYSIS.md) for technical details

### Chinese Text Not Displaying

**Check:**
1. All font files (`.ttf`/`.ttc`) are deployed to `data/font/`
2. `Engine.ucs` is present in `Engine/Locale/Chinese/`
3. Game files are not corrupted (Steam Verify)

**Reset:**
1. Disable mod in Vortex
2. Verify game files (right-click game in Steam → Properties → Verify)
3. Re-enable mod

### Mod Fails to Deploy in Vortex

**Possible Causes:**
- Archive format unrecognized
- Missing `modinfo.json` metadata
- File permissions issue

**Solution:**
1. Check Vortex notification panel for detailed error
2. Verify archive structure: files at mod root (not nested)
3. Ensure `modinfo.json` is valid JSON (use online validator if unsure)
4. Try deploying manually to `Mods/` folder

### SGA Build Fails with Archive.exe

**Error: "Cannot open buildfile"**
- Ensure buildfile has CRLF line endings (not LF)
- Use Windows Notepad or online CRLF converter
- Quote paths with spaces

**Error: "Invalid compression type"**
- Compression values: `ct="0"` (Store), `ct="1"` (Stream), `ct="2"` (Buffer)
- Check syntax for typos

**Error: "File not found"**
- Root path (`-r`) must point to existing directory
- Use absolute paths or verify relative path

---

## File Exclusion Rules (Locale Mods)

| File | Include? | Reason |
|------|----------|--------|
| `.ttf`, `.ttc` | ✅ YES | Required for text rendering |
| `.fnt` | ✅ YES | Font configuration |
| `.gfx` (except fontdecor.gfx) | ✅ YES | UI assets |
| `fontdecor.gfx` | ❌ NO | Broken in TC version (use vanilla) |
| `.bak` | ❌ NO | Backup files, not needed |
| `.ucs` | ✅ YES | Unicode strings |
| `.fda`, `.rat` | ✅ YES | Audio banks |

---

## Technical Specifications

| Property | Value |
|----------|-------|
| **Engine** | Relic Essence Engine (DirectX 9, 32-bit) |
| **Archive Format** | `.sga` (Relic binary, max 4GB) |
| **UI Format** | `.gfx` (Scaleform Flash 8.x bytecode) |
| **Font Format** | `.ttf`/`.ttc` (TrueType) |
| **String Format** | `.ucs` (UTF-16 LE Unicode) |
| **Config Format** | `.fnt` (text-based font metadata) |
| **Audio Format** | `.fda`/`.rat` (Relic audio banks) |

---

## Support

**For Extension Issues:**
1. Review mod package structure
2. Check Vortex notification panel (Settings → Notifications)
3. Consult [FONTDECOR_ROOT_CAUSE_ANALYSIS.md](../unofficial-tc-patch/docs/FONTDECOR_ROOT_CAUSE_ANALYSIS.md)
4. Report with:
   - Archive structure (list files)
   - Vortex version
   - Extension version
   - Error message (screenshots helpful)

---

## License

MIT — See [LICENSE](../../LICENSE)

## Version

- **Extension Version:** 1.1.0
- **Vortex Compatibility:** 1.10+
- **Game:** Steam App ID 3556750
