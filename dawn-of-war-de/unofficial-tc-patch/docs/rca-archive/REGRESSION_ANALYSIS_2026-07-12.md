# Regression Analysis: Tofu Box Issue Returns
**Date**: 2026-07-12  
**Issue**: Chinese text renders as tofu boxes in Dark Crusade/Soulstorm mode  
**Status**: ✅ ROOT CAUSE IDENTIFIED

---

## Executive Summary

The tofu box rendering issue has **regressed** after being fixed in v1.0.2/v1.0.4. The regression occurred on **July 4, 2026 at ~14:04** due to the SGA rebuild refactor (commit `70b37e3`).

### Timeline
| Date | Event | Evidence |
|------|-------|----------|
| **2026-06-06** | Original fix implemented (commit `5a99ccc`) | Excluded fontdecor.gfx via rsync |
| **2026-07-04 12:15** | Last working build | `EnginLocMod.sga` = 184MB ✅ |
| **2026-07-04 14:04** | **REGRESSION STARTS** | `EnginLocMod.sga` = 205MB ❌ |
| **2026-07-04 14:51** | Refactor commit pushed (`70b37e3`) | New rebuild scripts introduced |

---

## Root Cause Analysis

### Original Issue (Fixed in v1.0.2)
**Problem**: TC mod's `fontdecor.gfx` was incorrectly stripped (1.0MB vs 8.7MB vanilla), removing critical glyph table data. This caused Chinese text to render as tofu boxes.

**Solution (commit `5a99ccc`)**: Exclude `fontdecor.gfx` from deployment using:
```bash
rsync -a --exclude="*.bak" --exclude="fontdecor.gfx" "${local_src}/" "${LOCALE_TARGET}/${d}/"
```
This let the game engine use the **vanilla fontdecor.gfx** from the original `EnginLoc.sga`, which has complete glyph data.

**Documentation**: `docs/FONTDECOR_ROOT_CAUSE_ANALYSIS.md` contains full technical analysis with binary search test results.

---

### Regression (July 4, 2026)

**What Changed**: Commit `70b37e3` refactored the SGA rebuild process, introducing new scripts:
- `scripts/rebuild_sga_auto.sh`
- `scripts/rebuild_sga_with_font_sizes.sh`
- `scripts/master_rebuild.sh`
- `scripts/repack_sga_windows.ps1`

**The Problem**: These new scripts:
1. Extract the **full vanilla SGA** (including all `data/art/` files)
2. Apply font patches to `data/font/`
3. **Rebuild the SGA from the entire `data/` directory**

**Critical Issue**: The rebuild scripts pack **ALL** files from `data/`, including:
- ❌ `data/art/ui/swf/fontdecor.gfx` (broken TC version - 1.0MB)
- ❌ Other art/sound files not needed in the mod

The original fix's `--exclude="fontdecor.gfx"` exclusion **was not carried forward** to the SGA build phase.

---

## Evidence

### File Size Comparison
```
Before Regression (working):
  EnginLocMod.sga.20260704-121520.bak  →  184M  ✅
  EnginLocMod.sga.20260704-140204.bak  →  184M  ✅

After Regression (broken):
  EnginLocMod.sga.20260704-140414.bak  →  205M  ❌
  EnginLocMod.sga.20260704-144739.bak  →  205M  ❌
  EnginLocMod.sga (current)            →  205M  ❌

Size difference: +21MB (includes 8.7MB fontdecor.gfx + other art/sound files)
```

### Script Analysis

**Original deployment (deploy.sh, commit 5a99ccc)**:
```bash
rsync -a --exclude="*.bak" --exclude="fontdecor.gfx" \
    "${local_src}/" "${LOCALE_TARGET}/data/${subdir}/"
```
✅ Correctly excludes fontdecor.gfx

**New rebuild script (rebuild_sga_auto.sh, commit 70b37e3)**:
```bash
cat > "$BUILD_FILE" <<'EOF'
Archive
TOCStart alias="data" relativeroot="."
FileSettingsStart defcompression="1"
    Override wildcard=".*(gfx)$" minsize="-1" maxsize="-1" ct="1"
    Override wildcard=".*(fnt)$" minsize="-1" maxsize="-1" ct="2"
    ...
TOCEnd
EOF

"$ARCHIVE_EXE" -c "$WIN_BUILD" -r "$WIN_DATA" -a "$WIN_OUTPUT" -v
```
❌ No fontdecor.gfx exclusion - packs everything from `data/`

**New rebuild script (rebuild_sga_with_font_sizes.sh)**:
```bash
# Extract vanilla SGA
"$ARCHIVE_EXE" -a "$VANILLA_SGA" -e "."

# Apply font patches
$PYTHON scripts/apply_font_fix.py --root . --size "$FONT_SIZE"

# Rebuild SGA from data/
"$ARCHIVE_EXE" -build "$BUILDFILE_WIN" -sourcedir "$DATA_WIN" ...
```
❌ Extracts FULL vanilla SGA (including fontdecor.gfx), rebuilds without exclusion

---

## The Fix

### Correct Approach: Replace Broken TC fontdecor.gfx with Vanilla Version

The documentation (`docs/FONTDECOR_ROOT_CAUSE_ANALYSIS.md`) specifies the mod SGA should contain:
- ✅ **VANILLA fontdecor.gfx (8.4MB)** - working version with complete glyph data
- ❌ NOT the broken TC fontdecor.gfx (989K) - stripped version missing glyphs

**Implementation**:

```bash
# In rebuild_sga_auto.sh and rebuild_sga_with_font_sizes.sh
# After extraction, before building:

log "Replacing broken TC fontdecor.gfx with vanilla version..."
VANILLA_FONTDECOR=".copilot_workspace/game_chinese_fonts/art/ui/swf/fontdecor.gfx"
TARGET_FONTDECOR="data/art/ui/swf/fontdecor.gfx"

if [[ -f "$VANILLA_FONTDECOR" ]]; then
    mkdir -p "$(dirname "$TARGET_FONTDECOR")"
    cp "$VANILLA_FONTDECOR" "$TARGET_FONTDECOR"
    ok "fontdecor.gfx replaced with vanilla (8.4MB working version)"
else
    warn "Vanilla fontdecor.gfx not found at $VANILLA_FONTDECOR"
    err "Cannot proceed without vanilla fontdecor.gfx"
    exit 1
fi
```

**Why This Approach**:
1. Makes the mod **standalone** (doesn't rely on EnginLoc.sga)
2. Matches the documented fix in `FONTDECOR_ROOT_CAUSE_ANALYSIS.md`
3. Explicit and verifiable (SGA size should be ~198MB)
4. Original fix attempted exclusion, but docs show inclusion is correct

---

## Recommended Action Plan

1. **Immediate Fix** (Option 1):
   - Add fontdecor.gfx deletion to all rebuild scripts
   - Rebuild SGA: `bash scripts/rebuild_sga_auto.sh`
   - Verify output is ~184MB (not 205MB)
   
2. **Test**:
   - Deploy to game: `bash deploy.sh`
   - Launch Dark Crusade campaign
   - Verify Chinese text renders correctly (no tofu boxes)

3. **Document**:
   - Update `docs/FONTDECOR_ROOT_CAUSE_ANALYSIS.md` with regression details
   - Add comment in rebuild scripts explaining why fontdecor.gfx is excluded
   - Update CHANGELOG

4. **Prevent Future Regressions**:
   - Add SGA size check to CI/tests (should be ~180-190MB, alert if >200MB)
   - Document the "fontdecor.gfx must be excluded" requirement prominently

---

## Files to Modify

```
scripts/rebuild_sga_auto.sh           ← Add fontdecor.gfx deletion
scripts/rebuild_sga_with_font_sizes.sh ← Add fontdecor.gfx deletion
scripts/master_rebuild.sh             ← Add fontdecor.gfx deletion
docs/FONTDECOR_ROOT_CAUSE_ANALYSIS.md ← Document regression
docs/CHANGELOG.md                     ← Add v1.0.6 regression fix entry
```

---

## Technical Details

### Why fontdecor.gfx Causes Tofu Boxes

The `.gfx` files are **Scaleform GFX compiled bytecode** (binary SWF format) containing:
1. UI layout definitions
2. **Glyph/font tables** (character bitmap references)
3. Asset definitions
4. Font binding metadata

TC mod's fontdecor.gfx:
- ❌ Size: 1.0MB (87% smaller than vanilla 8.7MB)
- ❌ Font reference: "Noto Serif" (incomplete for CJK)
- ❌ Glyph table data: **deleted**

Result: Engine looks up glyphs → table missing → renders tofu boxes

### Why Vanilla fontdecor.gfx Works

Vanilla EnginLoc.sga:
- ✅ Size: 8.7MB (complete)
- ✅ Font reference: "Noto Sans TC SemiBold"
- ✅ Glyph table data: **intact**

When mod's SGA doesn't include fontdecor.gfx, the game engine falls back to vanilla EnginLoc.sga and finds the working version.

---

## References

- Original fix commit: `5a99ccc` (2026-06-06)
- Regression commit: `70b37e3` (2026-07-04)
- Root cause analysis: `docs/FONTDECOR_ROOT_CAUSE_ANALYSIS.md`
- Binary search test methodology: 7 test iterations confirming fontdecor.gfx as culprit

---

## Checklist for Fix Verification

- [ ] fontdecor.gfx deletion added to rebuild scripts
- [ ] SGA rebuilt, size verified (~184MB)
- [ ] Deployed to test environment
- [ ] Dark Crusade campaign tested (no tofu boxes)
- [ ] Soulstorm campaign tested (no tofu boxes)
- [ ] Documentation updated
- [ ] CHANGELOG entry added
- [ ] CI size check implemented (future prevention)
