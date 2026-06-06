# SGA Builder Tool

Automated helper for packaging locale mods as SGA archives for Vortex deployment.

## Features

- ✅ Auto-detects Archive.exe from Steam installation
- ✅ Validates mod directory structure
- ✅ Prevents invalid files (fontdecor.gfx, .bak)
- ✅ Generates proper buildfile with CRLF line endings
- ✅ Verifies SGA integrity after packing
- ✅ Provides next-steps guidance

## Installation

### Linux / WSL2

```bash
# No installation needed — script uses Python standard library
python3 build_sga.py --help
```

### Windows (PowerShell)

```powershell
python build_sga.py --help
# Or use Build-LocaleSGA.ps1 for native PowerShell
.\Build-LocaleSGA.ps1 -InputDir "wh40k-dow-de-tc-mod-v1.0.3"
```

## Usage

### Python (All Platforms)

**Quick Build:**
```bash
python3 build_sga.py --input wh40k-dow-de-tc-mod-v1.0.3
```

**Full Options:**
```bash
python3 build_sga.py \
  --input wh40k-dow-de-tc-mod-v1.0.3 \
  --output EnginLocMod.sga \
  --archive-exe "/path/to/Archive.exe" \
  --skip-verify
```

| Option | Required | Description |
|--------|----------|-------------|
| `--input` | ✅ YES | Mod directory to package |
| `--output` | ❌ NO | Output filename (default: `EnginLocMod.sga`) |
| `--archive-exe` | ❌ NO | Path to Archive.exe (auto-detect if omitted) |
| `--skip-verify` | ❌ NO | Skip integrity check |

### PowerShell (Windows)

**Quick Build:**
```powershell
.\Build-LocaleSGA.ps1 -InputDir "wh40k-dow-de-tc-mod-v1.0.3"
```

**Full Options:**
```powershell
.\Build-LocaleSGA.ps1 `
  -InputDir "wh40k-dow-de-tc-mod-v1.0.3" `
  -OutputFile "EnginLocMod.sga" `
  -ArchiveExe "D:\SteamLibrary\steamapps\common\Dawn of War Definitive Edition\archive\Archive.exe"
```

## Workflow

### Step 1: Build SGA

```bash
# Linux/WSL
python3 tools/python/sga-builder/build_sga.py \
  --input dawn-of-war-de/unofficial-tc-patch

# Windows
python tools\python\sga-builder\build_sga.py ^
  --input dawn-of-war-de\unofficial-tc-patch
```

**Output:** `EnginLocMod.sga` (~60–80MB)

### Step 2: Create Vortex Package

```bash
mkdir -p wh40k-dow-de-tc-mod-v1.0.3
cp EnginLocMod.sga wh40k-dow-de-tc-mod-v1.0.3/
```

### Step 3: Add Metadata

Create `wh40k-dow-de-tc-mod-v1.0.3/modinfo.json`:

```json
{
  "id": "unofficial-tc-patch",
  "name": "Unofficial Traditional Chinese Patch",
  "version": "1.0.3",
  "description": "Fixed Traditional Chinese localization with correct fonts and no tofu boxes",
  "author": "Crystal Mods",
  "modVersion": "1.0.3",
  "gameVersion": ""
}
```

### Step 4: Package for Vortex

```bash
zip -r wh40k-dow-de-tc-mod-v1.0.3.zip wh40k-dow-de-tc-mod-v1.0.3/
```

### Step 5: Deploy via Vortex

1. Drag `wh40k-dow-de-tc-mod-v1.0.3.zip` onto Vortex
2. Vortex detects SGA locale mod
3. Copy SGA to `Engine/Locale/Chinese/`
4. Done!

## Buildfile Format

The tool automatically generates the optimal buildfile:

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
- `ct="0"` → Store (fonts, UCS strings)
- `ct="1"` → Compress Stream (GFX files)
- `ct="2"` → Compress Buffer (FNT files)

## Validation Rules

### ✅ Required (Locale Mod Markers)

- `Engine.ucs` (unicode strings)
- OR `data/font/` (font files)
- OR `data/art/ui/swf/` (GFX UI files)

### ❌ Forbidden

- `fontdecor.gfx` (use vanilla version)
- `*.bak` (backup files)

### ✅ Recommended

- All `.ttf`/`.ttc` font files
- All `.fnt` font configs
- All `.gfx` except fontdecor.gfx
- All `.fda`/`.rat` audio files

## Troubleshooting

### "Archive.exe not found"

Copy from game installation:
```
<game>\archive\Archive.exe
```

Specify explicitly:
```bash
python3 build_sga.py \
  --input wh40k-dow-de-tc-mod-v1.0.3 \
  --archive-exe "D:\SteamLibrary\steamapps\common\Dawn of War Definitive Edition\archive\Archive.exe"
```

### "fontdecor.gfx found"

This file is broken in TC version. Delete it:
```bash
rm dawn-of-war-de/unofficial-tc-patch/data/art/ui/swf/fontdecor.gfx
```

### "No locale mod markers found"

Ensure at least one is present:
- `Engine.ucs`
- `data/font/`
- `data/art/ui/swf/`

### SGA integrity test failed

Possible causes:
- Invalid buildfile format (line endings)
- Archive.exe corruption
- Output file permission issue

Try:
```bash
python3 build_sga.py --input <dir> --skip-verify
Archive.exe -a EnginLocMod.sga -t  # Manual test
```

## Performance

| Operation | Time |
|-----------|------|
| Validation | < 1s |
| SGA Build | 30–60s |
| Verification | 10–15s |
| **Total** | **~1 minute** |

## Requirements

- Python 3.6+
- Archive.exe (from DoW DE game installation)
- 200+ MB free disk space
- CRLF line ending support

## License

MIT — See root [LICENSE](../../../LICENSE)

---

**Questions?** See [Vortex Extension README](../../vortex-ext/README.md) for SGA deployment details.
