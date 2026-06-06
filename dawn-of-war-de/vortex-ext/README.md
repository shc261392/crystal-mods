# Vortex Extension — Warhammer 40,000: Dawn of War - Definitive Edition

A [Vortex](https://www.nexusmods.com/about/vortex/) game extension for  
**Warhammer 40,000: Dawn of War – Definitive Edition** (Steam App ID `3556750`).

The extension is currently under Vortex review, so install it by dragging the zip onto Vortex's **Extensions** tab.

## Features

- Auto-discovers the game through Steam (App ID `3556750`)
- Installs **locale mods** (`.ucs`, `.fnt`, `.gfx`, sound files) to  
  `Engine/Locale/<Locale>/`, defaulting to `Chinese` when no locale is specified
- Installs **general game-root mods** (SGA archives, race packs, map packs,  
  gameplay scripts) to the game root, stripping a single wrapper folder where needed
- Automatically excludes backup files (`.bak`) and broken assets (`fontdecor.gfx`)
- Two installers run in priority order — the locale installer fires first;  
  unmatched mods fall through to the root installer

## Installation

1. Download `vortex-ext-game-warhammer40kdawnofwar-v*.zip` from Nexus Mods.
2. Open Vortex, drag the zip onto the **Extensions** tab, and click *Enable*.
3. Re-open Vortex — **Warhammer 40,000: Dawn of War - Definitive Edition**  
  will appear under *Supported Games*.

---

## ⚠️ Locale Mods: Required Setup Step

When deploying **locale mods** (e.g., Traditional Chinese Patch), you must choose one approach:

### Option A: Loose Files (Recommended)

1. **ONE-TIME SETUP:** Disable the vanilla locale SGA:
   ```
   Engine/Locale/Chinese/EnginLoc.sga  →  EnginLoc.sga.disabled
   ```
   
2. **Deploy:** Use Vortex normally
   - Extension auto-detects locale mod
   - Files deploy to `Engine/Locale/Chinese/data/`, `Engine/Locale/Chinese/Engine.ucs`
   - Game loads loose files with priority over vanilla SGA

3. **Optional:** Run deploy script for advanced features:
   ```bash
   # Linux/WSL: apply font fixes, migrate saves, etc.
   bash deploy.sh
   
   # Windows (PowerShell):
   .\deploy.ps1
   ```

**✅ Advantages:**
- Simple setup
- Vortex handles all deployment
- Easy to inspect/modify files
- Automatic file exclusions

**ℹ️ Note:** Backup files (`.bak`) and broken assets (`fontdecor.gfx`) are automatically excluded.

---

### Option B: SGA-Packaged Mode (Advanced Users)

If you prefer compact, archived deployment (60–80MB compressed vs 200MB+ loose files):

#### Step 1: Prepare Buildfile

Create `build.txt` (**CRITICAL: Use CRLF line endings, not LF**):

```
Archive
TOCStart alias="data" relativeroot="."
FileSettingsStart defcompression="1"
    Override wildcard=".*(gfx)$" minsize="-1" maxsize="-1" ct="1"
    Override wildcard=".*(fnt)$" minsize="-1" maxsize="-1" ct="2"
    Override wildcard=".*(ttf|ttc|ucs)$" minsize="-1" maxsize="-1" ct="0"
FileSettingsEnd
TOCEnd
```

**Compression Types:**
- `ct="0"` → Store (no compression) — fonts, UCS
- `ct="1"` → Compress Stream — `.gfx` files
- `ct="2"` → Compress Buffer — `.fnt` files

#### Step 2: Pack the SGA

```bash
# Copy Archive.exe from game installation
Archive.exe -c build.txt -r wh40k-dow-de-tc-mod-v1.0.3 -a EnginLocMod.sga
```

**Output:** `EnginLocMod.sga` (~60–80MB)

#### Step 3: Create Vortex Package

```
wh40k-dow-de-tc-mod-v1.0.3.zip
└── wh40k-dow-de-tc-mod-v1.0.3/
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
