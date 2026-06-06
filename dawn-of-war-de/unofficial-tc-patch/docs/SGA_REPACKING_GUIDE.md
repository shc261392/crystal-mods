# SGA Repacking Guide — DoW DE Vanilla Locale Files

## Overview

This guide documents how to repack loose files back into Relic Archive (.sga) format for Warhammer 40K: Dawn of War — Definitive Edition.

**Key Finding:** Repacking is possible using `Archive.exe` with a structured buildfile.

## Process Summary

### 1. Extract Original SGA

```bash
# WSL2/Linux
GAME_PATH="/mnt/d/SteamLibrary/steamapps/common/Dawn of War Definitive Edition"
mkdir -p extract_source
"$GAME_PATH/Archive.exe" -a "$GAME_PATH/Engine/Locale/Chinese/EnginLoc.sga" -e extract_source
```

**Result:** 43 files extracted with original compression metadata

### 2. Create SGA Buildfile

The buildfile specifies compression settings for each file type. Archive.exe supports:
- `ct="0"` — Store (no compression): TTF/TTC fonts
- `ct="1"` — Compress Stream: GFX files  
- `ct="2"` — Compress Buffer: FNT config files, audio

**File:** `EnginLocFull.txt`

```
Archive
TOCStart alias="data" relativeroot="."
FileSettingsStart defcompression="1"
    Override wildcard=".*(gfx)$" minsize="-1" maxsize="-1" ct="1"
    Override wildcard=".*(fnt)$" minsize="-1" maxsize="-1" ct="2"
    Override wildcard=".*(ttf|ttc)$" minsize="-1" maxsize="-1" ct="0"
    Override wildcard=".*(fda|rat)$" minsize="-1" maxsize="-1" ct="2"
FileSettingsEnd
TOCEnd
```

**Important:** Buildfile MUST use **CRLF line endings** (Windows format). Archive.exe requires this.

```bash
# Linux: Convert to CRLF
sed -i 's/$/\r/' EnginLocFull.txt

# Or use unix2dos if available
unix2dos EnginLocFull.txt
```

### 3. Repack SGA with Archive.exe

```bash
GAME_PATH="/mnt/d/SteamLibrary/steamapps/common/Dawn of War Definitive Edition"

# Convert paths to Windows format (required by Archive.exe)
# WSL2 example: /home/shado → H:/home/shado (or similar)
# Paths must use backslashes

"$GAME_PATH/Archive.exe" \
  -c "EnginLocFull.txt" \
  -r "extract_source" \
  -a "EnginLocRepacked.sga" \
  -v
```

**Timing:** ~57 seconds for full 43-file SGA

### 4. Verify Repacked SGA

```bash
# Test integrity
"$GAME_PATH/Archive.exe" -a "EnginLocRepacked.sga" -t

# List contents
"$GAME_PATH/Archive.exe" -a "EnginLocRepacked.sga" -l
```

## Tested Results

| Metric | Value |
|--------|-------|
| Original EnginLoc.sga | 190M |
| Repacked EnginLocRepacked.sga | 193M |
| Integrity Test | ✓ PASSED |
| File Count | 43 ✓ |
| Build Time | 56.87 seconds |
| Extraction | Idempotent (43/43 files identical) |

## Key Insights

1. **Extraction is Idempotent**  
   Multiple extractions of the same SGA produce identical file content (byte-for-byte).

2. **No Files Missing from Loose Deployment**  
   Audit confirmed all 43 original SGA files are deployed when using loose file mode.

3. **Repacking Works**  
   Archive.exe successfully creates valid SGA archives with proper compression.

4. **Compression Matters**  
   - Repacked SGA is 3M larger (193M vs 190M)
   - Likely due to recompression differences
   - Still within acceptable range and fully functional

## Recommendations

### For TC Mod Development

**Option A: Keep loose files + recreate SGA for distribution**
- Deploy loosely for testing (fast iteration)
- Repack as SGA for final release
- Ensures maximum compatibility

**Option B: Dual-mode deployment**
- Support both SGA mode (compatibility) and loose mode (development)
- Use conditional loading based on file system hierarchy

### For Future Debugging

If loose file rendering fails in the future:
1. Compare loose file byte-by-byte with extracted SGA
2. Verify file compression matches original
3. Test with repacked SGA to isolate format issues from content issues
4. Use Archive.exe hash mode for structural debugging: `Archive.exe -a game.sga -hash`

## Archive.exe Command Reference

```
Archive.exe -a <archivefile> [-v] -t |-c <buildfile> -r <rootpath>|-l

Required: -a <archivefile>

Operations (choose one):
  -c <buildfile> -r <rootpath>   Create archive from buildfile
  -l                             List archive contents
  -t                             Test archive integrity
  -e <extract location>          Extract to folder
  -hash                          List archive hash

Optional:
  -v                             Verbose logging
```

## Line Endings Issue (Critical)

Archive.exe is Windows tool compiled for compatibility with ASCII tools. It expects:
- Buildfile with **CRLF** line endings (`\r\n`)
- Windows-style paths with backslashes
- Path format: `C:\path\to\file` (not `/mnt/c/path`)

If using WSL2, use sed/unix2dos to convert:
```bash
sed -i 's/$/\r/' buildfile.txt  # Add CR to LF
```

---

**Document Created:** 2026-06-05  
**Testing Environment:** WSL2 on Windows 11, DoW DE steam installation on D: drive  
**Archive.exe Tested:** Version in DoW DE installation directory
