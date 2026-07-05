# Build Guide — DoW DE Traditional Chinese Mod

**Target Audience:** Any developer with zero project knowledge who needs to reproduce the standard build process.

**Environment:** WSL2 (Ubuntu) on Windows 11 with DoW DE installed via Steam

---

## Prerequisites

### Required Tools
- **Python 3.x** with `uv` package manager
- **bash** shell (standard in WSL2)
- **Archive.exe** — bundled with DoW DE game installation (located at game root)
- **make** — for build automation

### Game Installation
- Dawn of War Definitive Edition installed via Steam
- Default path: `/mnt/d/SteamLibrary/steamapps/common/Dawn of War Definitive Edition`
- Set environment variable if different: `export DOW_GAME_DIR="/your/game/path"`

### Repository Setup
```bash
cd /home/shado/crystal-mods/dawn-of-war-de/unofficial-tc-patch
uv sync  # Install Python dependencies
```

---

## Standard Build Process

### Overview
The mod ships as a **pre-built SGA archive** containing:
- Font configuration files (`.fnt`) with Traditional Chinese font references
- Font files (`.ttf`/`.ttc`) including NotoSansTC family
- UI graphics (`.gfx`)
- Localization text (`Engine.ucs`)

Font size variants are created by:
1. Extracting original SGA to `data/` directory
2. Patching `.fnt` files with new `sizeDefault` values
3. Repacking `data/` into `EnginLocMod.sga` using Archive.exe
4. Packaging into distributable `.zip` with proper directory structure

---

## Step-by-Step Build Instructions

### 1. Extract Original SGA (First Time Only)

If `data/` directory doesn't exist, extract from backup or game's original SGA:

```bash
# Copy from most recent backup
cp -r backup/20260604-144320/data .
```

**Result:** 58 files in `data/` directory (fonts, graphics, audio)

### 2. Patch Font Sizes

**⚠️ CRITICAL:** You MUST use `--mode all` to patch ALL font size fields!

#### Why `--mode all` is Required

The game engine uses **resolution-specific font size fields** (`size640`, `size800`, `size1024`, `size1280`, `size1600`) instead of `sizeDefault` at common resolutions (640×480 and higher). Most players at 1920×1080 or higher use the `size1600` field.

- **`--mode fallback-only`** ❌ (default): Only patches `sizeDefault` → **All variants look the same in-game!**
  - Replacements: 13 (1 per .fnt file)
  - Result: size640-1600 fields remain at 32, fonts don't change
  
- **`--mode all`** ✅ (required): Patches ALL size fields → **Variants render at different sizes**
  - Replacements: 75-78 (6 per .fnt file)
  - Result: All size fields updated consistently

**See** [`.copilot_workspace/FONT_SIZE_RCA.md`](../.copilot_workspace/FONT_SIZE_RCA.md) for detailed root cause analysis.

#### Patch Commands

```bash
# For standard variant (SIZE=36)
python3 scripts/apply_font_fix.py --root . --size 36 --mode all

# For large font variant (SIZE=48)
python3 scripts/apply_font_fix.py --root . --size 48 --mode all

# For any custom size (32-48 tested and verified)
python3 scripts/apply_font_fix.py --root . --size 40 --mode all
```

**What it does:**
- Finds all `.fnt` files in `data/font/`
- Replaces `sizeDefault`, `size640`, `size800`, `size1024`, `size1280`, `size1600` with new value
- Creates `.fnt.bak` backups before modifying

**Verify ALL size fields were patched:**
```bash
grep -E "(sizeDefault|size640|size800|size1024|size1280|size1600)" data/font/notosans_m_16_xc.fnt

# Expected output (for SIZE=36):
#   sizeDefault = 36;
#   size640     = 36;
#   size800     = 36;
#   size1024    = 36;
#   size1280    = 36;
#   size1600    = 36;
```

**If you see mixed values (e.g., sizeDefault=48 but size640=32):**
- ❌ You used `--mode fallback-only` by mistake
- ✅ Re-run with `--mode all`

### 3. Rebuild SGA Archive

**CRITICAL:** Archive.exe must run **OUTSIDE the VS Code terminal sandbox**.

#### Why Sandbox Matters
- Archive.exe is a Windows executable that requires WSL interop
- VS Code's terminal sandbox blocks WSL's ability to call Windows executables
- **Symptom:** `<3>WSL (N) ERROR: UtilConnectUnix:524: socket failed 1`
- **Solution:** Request unsandboxed execution when running via automation tools

#### Method A: Using the Automated Script

```bash
bash scripts/rebuild_sga_auto.sh
```

**If running from VS Code / automation tool:** Request unsandboxed execution or the Archive.exe call will fail.

**The script performs:**
1. Verifies `data/` directory exists
2. Creates Archive.exe buildfile with CRLF line endings
3. Converts Linux paths to Windows UNC format:
   - `/home/user/...` → `\\wsl.localhost\Ubuntu\home\user\...`
   - `/mnt/d/...` → `D:\...`
4. Backs up existing `EnginLocMod.sga` with timestamp
5. Calls Archive.exe with Windows paths
6. Verifies output SGA was created

**Build time:** ~45-65 seconds for 58 files

#### Method B: Manual Archive.exe Invocation

```bash
cd /home/shado/crystal-mods/dawn-of-war-de/unofficial-tc-patch

GAME_DIR="/mnt/d/SteamLibrary/steamapps/common/Dawn of War Definitive Edition"

# Create buildfile (must have CRLF line endings)
cat > .copilot_workspace/EnginLocBuild.txt <<'EOF'
Archive
TOCStart alias="data" relativeroot="."
FileSettingsStart defcompression="1"
    Override wildcard=".*(gfx)$" minsize="-1" maxsize="-1" ct="1"
    Override wildcard=".*(fnt)$" minsize="-1" maxsize="-1" ct="2"
    Override wildcard=".*(ttf|ttc)$" minsize="-1" maxsize="-1" ct="0"
    Override wildcard=".*(fda|rat)$" minsize="-1" maxsize="-1" ct="2"
FileSettingsEnd
TOCEnd
EOF

# Convert to CRLF (required by Archive.exe)
sed -i 's/$/\r/' .copilot_workspace/EnginLocBuild.txt

# Convert paths to Windows UNC format
WIN_BUILD="\\wsl.localhost\\Ubuntu\\home\\shado\\crystal-mods\\dawn-of-war-de\\unofficial-tc-patch\\.copilot_workspace\\EnginLocBuild.txt"
WIN_DATA="\\wsl.localhost\\Ubuntu\\home\\shado\\crystal-mods\\dawn-of-war-de\\unofficial-tc-patch\\data"
WIN_OUTPUT="\\wsl.localhost\\Ubuntu\\home\\shado\\crystal-mods\\dawn-of-war-de\\unofficial-tc-patch\\EnginLocMod.sga"

# Build SGA (must run unsandboxed if in VS Code)
"$GAME_DIR/Archive.exe" \
    -c "$WIN_BUILD" \
    -r "$WIN_DATA" \
    -a "$WIN_OUTPUT" \
    -v
```

**Expected output:**
```
14:02:05.329 : Parsing Build File '...'
14:02:05.330 : Creating TOC Entry Name:'enginlocbuild'  Alias:'data'
[... compression progress for 58 files ...]
14:02:48.158 : Calculating Hash
Build Operation took 62.86 seconds.
```

**Verify:**
```bash
ls -lh EnginLocMod.sga
# Should be ~205M (192673835 bytes) and have current timestamp
```

### 4. Package Distribution Zip

```bash
make package
```

**What it does:**
1. Creates `dist/wh40k-dow-de-tc-mod-v1.0.5/` directory structure:
   ```
   Engine/
     Locale/
       Chinese/
         EnginLoc.sga    (renamed from EnginLocMod.sga)
         Engine.ucs
   ```
2. Zips the directory
3. Reports size (~130M compressed from 205M SGA + 1.5M UCS)

**Output:** `dist/wh40k-dow-de-tc-mod-v1.0.5.zip`

### 5. Build Font Size Variants

To create both standard (36) and large (48) variants:

```bash
# Standard variant (SIZE=36)
python3 scripts/apply_font_fix.py --root . --size 36 --mode fallback-only
bash scripts/rebuild_sga_auto.sh  # (request unsandboxed if automated)
make package
# Result: dist/wh40k-dow-de-tc-mod-v1.0.5.zip

# Large font variant (SIZE=48)
python3 scripts/apply_font_fix.py --root . --size 48 --mode fallback-only
bash scripts/rebuild_sga_auto.sh  # (request unsandboxed if automated)
make package
mv dist/wh40k-dow-de-tc-mod-v1.0.5.zip dist/wh40k-dow-de-tc-mod-v1.0.5-font48.zip
```

**Final artifacts:**
```
dist/wh40k-dow-de-tc-mod-v1.0.5.zip         (130M, SIZE=36)
dist/wh40k-dow-de-tc-mod-v1.0.5-font48.zip  (130M, SIZE=48)
```

---

## Troubleshooting

### Error: `WSL (N) ERROR: UtilConnectUnix:524: socket failed 1`

**Cause:** Archive.exe is being called from a sandboxed environment that blocks WSL interop.

**Solutions:**
1. **If using VS Code Copilot / automation:** Request unsandboxed execution via tool parameters
2. **If running manually:** Ensure you're in a standard WSL2 terminal (not sandboxed)
3. **Test Archive.exe directly:**
   ```bash
   "/mnt/d/SteamLibrary/steamapps/common/Dawn of War Definitive Edition/Archive.exe"
   # Should show usage help, not socket error
   ```

### Error: `Archive.exe not found`

**Cause:** Game directory path is incorrect or game is not installed.

**Solutions:**
1. Verify game path:
   ```bash
   ls -lh "/mnt/d/SteamLibrary/steamapps/common/Dawn of War Definitive Edition/Archive.exe"
   ```
2. Set custom path:
   ```bash
   export DOW_GAME_DIR="/your/custom/game/path"
   ```

### Error: `data/ directory not found`

**Cause:** SGA has never been extracted.

**Solution:**
```bash
# Use existing backup
cp -r backup/20260604-144320/data .
```

### Font size changes don't appear in-game

**Cause:** The `EnginLocMod.sga` was not rebuilt with new font sizes.

**Solution:**
1. Verify fonts are patched in `data/`:
   ```bash
   grep "sizeDefault" data/font/*.fnt
   ```
2. Rebuild SGA: `bash scripts/rebuild_sga_auto.sh`
3. Verify SGA timestamp is recent: `ls -lh EnginLocMod.sga`
4. Repackage: `make package`

---

## Build Verification

### Checklist After Build

1. **SGA file exists and is recent:**
   ```bash
   ls -lh EnginLocMod.sga
   # Size: ~205M, timestamp: within last few minutes
   ```

2. **Font size is correct in data/:**
   ```bash
   grep "sizeDefault" data/font/notosans_m_16_xc.fnt
   # Should show: sizeDefault = 36; (or 48 for large variant)
   ```

3. **Package exists:**
   ```bash
   ls -lh dist/wh40k-dow-de-tc-mod-v1.0.5.zip
   # Size: ~130M
   ```

4. **Package contents are correct:**
   ```bash
   unzip -l dist/wh40k-dow-de-tc-mod-v1.0.5.zip
   # Should list:
   #   Engine/Locale/Chinese/EnginLoc.sga  (~192M)
   #   Engine/Locale/Chinese/Engine.ucs    (~1.5M)
   ```

5. **SGA integrity test:**
   ```bash
   "$GAME_DIR/Archive.exe" -a "$(wslpath -w EnginLocMod.sga)" -t
   # Should complete without errors
   ```

---

## Technical Details

### Archive.exe Compression Settings

| File Type | Wildcard Pattern | Compression Type | Flag |
|-----------|-----------------|------------------|------|
| Graphics | `.*gfx$` | Compress Stream | `ct="1"` |
| Font Config | `.*fnt$` | Compress Buffer | `ct="2"` |
| Font Files | `.*ttf\|ttc$` | Store (no compression) | `ct="0"` |
| Audio | `.*fda\|rat$` | Compress Buffer | `ct="2"` |

### Path Conversion for Archive.exe

Archive.exe is a Windows executable and requires Windows-style paths:

| Linux Path | Windows UNC Path |
|------------|------------------|
| `/home/user/...` | `\\wsl.localhost\Ubuntu\home\user\...` |
| `/mnt/d/Games/...` | `D:\Games\...` |

The `_linux_to_win()` function in scripts handles this conversion automatically.

### File Counts

| Component | File Count | Notes |
|-----------|------------|-------|
| Font config (`.fnt`) | 13 | Patched with `sizeDefault` |
| Font config backups (`.fnt.bak`) | 13 | Created by apply_font_fix.py |
| Font files (`.ttf`/`.ttc`) | 24 | NotoSansTC, NotoSerifTC, gulim, msyh, gakmob |
| Graphics (`.gfx`) | 5 | fonthead, fontbody, fontaux, fontdecor, font_glyphs |
| Audio (`.fda`/`.rat`) | 4 | _default, dow_intro |
| **Total** | **58** | All packed into EnginLocMod.sga |

### Build Performance

| Operation | Duration | Notes |
|-----------|----------|-------|
| Font patching | ~1 second | 13 files, simple regex replacement |
| SGA repacking | 45-65 seconds | 58 files, compression varies by type |
| Packaging (zip) | ~10 seconds | Deflate compression on 205M SGA |
| **Total** | **~60-80 seconds** | Per variant |

---

## Common Mistakes

### ❌ Assuming Wine is required
**Reality:** Archive.exe runs natively in WSL2 via Windows interop. Wine is NOT needed and was never used in this project.

### ❌ Running Archive.exe from sandboxed terminals
**Reality:** VS Code terminal sandbox blocks WSL interop. Request unsandboxed execution or run from standard WSL2 terminal.

### ❌ Using loose file deployment
**Reality:** Loose data deployment is **obsolete since v1.0.4**. All deployment scripts have been purged of loose mode logic. SGA-only is the canonical method.

### ❌ Forgetting to rebuild SGA after font changes
**Reality:** Editing `data/` fonts does NOT automatically update `EnginLocMod.sga`. You must explicitly run `rebuild_sga_auto.sh` for changes to take effect in-game.

### ❌ Using LF-only line endings in buildfile
**Reality:** Archive.exe **requires CRLF** line endings in buildfiles. Use `sed -i 's/$/\r/'` to convert.

---

## Quick Reference

### One-Command Build (Standard SIZE=36)
```bash
cd /home/shado/crystal-mods/dawn-of-war-de/unofficial-tc-patch && \
python3 scripts/apply_font_fix.py --root . --size 36 --mode fallback-only && \
bash scripts/rebuild_sga_auto.sh && \
make package
```

### One-Command Build (Large SIZE=48)
```bash
cd /home/shado/crystal-mods/dawn-of-war-de/unofficial-tc-patch && \
python3 scripts/apply_font_fix.py --root . --size 48 --mode fallback-only && \
bash scripts/rebuild_sga_auto.sh && \
make package && \
mv dist/wh40k-dow-de-tc-mod-v1.0.5.zip dist/wh40k-dow-de-tc-mod-v1.0.5-font48.zip
```

### File Locations Summary
```
Repository Root:
  ├── EnginLocMod.sga          (205M, working SGA, rebuilt on each build)
  ├── Engine.ucs               (1.5M, Traditional Chinese localization strings)
  ├── data/                    (extracted SGA files for patching)
  │   ├── font/*.fnt           (13 font config files)
  │   ├── font/*.fnt.bak       (13 backups)
  │   ├── font/*.ttf/*.ttc     (24 font files)
  │   ├── art/*.gfx            (5 graphics files)
  │   └── sound/*.fda/*.rat    (4 audio files)
  ├── scripts/
  │   ├── apply_font_fix.py           (patches .fnt sizeDefault values)
  │   └── rebuild_sga_auto.sh         (automates SGA repacking)
  └── dist/                    (build output)
      ├── wh40k-dow-de-tc-mod-v1.0.5.zip        (130M, SIZE=36)
      └── wh40k-dow-de-tc-mod-v1.0.5-font48.zip (130M, SIZE=48)
```

---

**Last Updated:** 2026-07-04  
**Build System Version:** v1.0.5  
**Tested Environment:** WSL2 (Ubuntu 22.04) on Windows 11, DoW DE via Steam
