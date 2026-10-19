# DAWDE Unofficial TC Patch — Complete Fix & Enhancement Summary
**Date:** 2026-07-18
**Status:** ✅ COMPLETE — Ready for testing and deployment

---

## 🎯 DELIVERABLES

### 1. ✅ Tofu Box Regression Fixed
**Root Cause:** Script was extracting from wrong SGA (English locale instead of Chinese)

**Solution:**
- Updated [`scripts/rebuild_sga_auto.sh`](scripts/rebuild_sga_auto.sh) to extract from `Engine/Locale/Chinese/EnginLoc.sga`
- Removed broken `apply_font_fix.py` (unnecessary — vanilla Chinese locale already has Noto Sans)
- Fixed Archive.exe command syntax

**Verification:**
```bash
✓ Source: EnginLoc.sga.vortex_backup (vanilla Chinese locale)
✓ Contains: 43 files with all Noto Sans TC fonts (9 weights)
✓ Locale compliance: Only accessed Engine/Locale/Chinese/
✓ SGA built: 184MB
✓ ZIP packaged: 122MB
```

---

### 2. ✅ Font Size Adjustment System
**New Feature:** Adjustable font sizes across all resolutions

**Documentation:** [`docs/FONT_STRUCTURE.md`](docs/FONT_STRUCTURE.md)
- Complete font structure analysis
- Vanilla font size reference for all 13 .fnt files
- Resolution breakpoints explained (640/800/1024/1280/1600)

**Script:** [`scripts/adjust_font_sizes.py`](scripts/adjust_font_sizes.py)
```bash
# Increase all fonts by +6 points
python3 scripts/adjust_font_sizes.py --root data/ --increase 6

# Preview changes without modifying
python3 scripts/adjust_font_sizes.py --root data/ --increase 6 --dry-run
```

**Integration:** Rebuild script now supports optional font adjustment
```bash
# Vanilla fonts (default)
./scripts/rebuild_sga_auto.sh

# +6 point font increase
./scripts/rebuild_sga_auto.sh --font-size-increase 6
```

---

### 3. ✅ Unified Build System
**Major Change:** `make build` now runs complete pipeline

**Before:**
```bash
make package  # Only packaged existing SGA
```

**After:**
```bash
make build    # Full pipeline: rebuild SGA + package ZIP
```

**Features:**
- `make rebuild` — Rebuild SGA from vanilla Chinese locale
- `make build` — Rebuild + package (complete distribution)
- `make build FONT_SIZE_INCREASE=6` — Build with +6 font sizes
- `make package` — Alias for `build` (backward compatibility)

**Makefile Variables:**
```makefile
FONT_SIZE_INCREASE ?= 0  # Font adjustment (0=vanilla)
```

---

### 4. ✅ Project Cleanup
**Removed 18 outdated files:**

**Scripts (13):**
- `apply_font_fix.py` — proven unnecessary
- `backup_original_files.sh` — bisection tool
- `bisection_art_files.sh` — bisection tool
- `bisection_test.sh` — bisection tool
- `deploy_baseline.sh` — bisection tool
- `deploy_bisect_sga.sh` — bisection tool
- `master_rebuild.sh` — superseded by rebuild_sga_auto.sh
- `rebuild_sga.cmd` — old Windows version
- `rebuild_sga_with_font_sizes.sh` — outdated approach
- `repack_chinese_locale.ps1` — old manual script
- `unpack_chinese_locale.ps1` — old manual script
- `repack_sga_windows.ps1` — old manual script
- `setup_relic_tool.ps1` — old manual script

**Documentation (5):**
- `BASELINE_HASH_REFERENCE.md` — bisection artifact
- `BINARY_SEARCH_TESTING.md` — bisection docs
- `SGA_TESTING_RESULTS.md` — historical testing
- `TC_MODDED_SGA_DEPLOYMENT.md` — outdated deployment guide
- `graphic-improvement-survey.md` — planning doc

**Remaining active scripts:**
- `rebuild_sga_auto.sh` — Automated SGA rebuild (WSL2)
- `adjust_font_sizes.py` — Font size adjustment utility
- `apply_tc_corrections.py` — TC translation corrections
- `migrate_campaign_states.py` — Save migration utility

---

## 📊 BUILD VERIFICATION

### Test Build (FONT_SIZE_INCREASE=6)
```
✓ Extracted from: EnginLoc.sga.vortex_backup (vanilla Chinese)
✓ Font sizes adjusted: +6 points across all resolutions
✓ SGA packed: EnginLocMod.sga (184MB)
✓ ZIP created: dist/wh40k-dow-de-tc-mod-v1.0.5.zip (122MB)
✓ Build time: 60 seconds
```

### Font Size Verification
```
albertus extra bold12.fnt:
  sizeDefault: 11 → 17 ✓
  size640:     11 → 17 ✓
  size1024:    12 → 18 ✓
  size1600:    16 → 22 ✓

gillsans_16.fnt:
  sizeDefault: 14 → 20 ✓
  size640:     14 → 20 ✓
  size1024:    18 → 24 ✓
  size1600:    28 → 34 ✓
```

---

## 🚀 USAGE GUIDE

### Standard Build (Vanilla Fonts)
```bash
make build
# Output: dist/wh40k-dow-de-tc-mod-v1.0.5.zip
```

### Build with Larger Fonts (+6)
```bash
make build FONT_SIZE_INCREASE=6
# Output: dist/wh40k-dow-de-tc-mod-v1.0.5.zip (with +6 fonts)
```

### Rebuild SGA Only
```bash
make rebuild
# Output: EnginLocMod.sga
```

### Deploy to Game
```bash
./deploy.sh                    # Deploy mod
./uninstall.sh                 # Revert to vanilla
```

---

## 📁 FILE STRUCTURE

```
dawn-of-war-de/unofficial-tc-patch/
├── EnginLocMod.sga (184MB)           ← Built SGA
├── Engine.ucs (1.5MB)                ← TC translation
├── dist/
│   └── wh40k-dow-de-tc-mod-v1.0.5.zip (122MB)  ← Distribution
├── scripts/
│   ├── rebuild_sga_auto.sh           ← Main rebuild script
│   ├── adjust_font_sizes.py          ← Font size utility
│   ├── apply_tc_corrections.py       ← Translation tool
│   └── migrate_campaign_states.py    ← Save migration
├── docs/
│   ├── FONT_STRUCTURE.md             ← NEW: Font documentation
│   ├── BUILD_GUIDE.md                ← Build instructions
│   ├── CHANGELOG.md                  ← Version history
│   └── NEXUS.md                      ← Publishing guide
└── Makefile                          ← Build automation
```

---

## 🔍 TECHNICAL NOTES

### Vanilla Chinese Locale Font Discovery
The vanilla `Engine/Locale/Chinese/EnginLoc.sga` already contains:
- **9 Noto Sans TC font weights** (regular, bold, black, extrabold, etc.)
- **8 Noto Serif TC font weights** (decorative fonts)
- **2 Noto Sans English fonts** (Latin character fallback)
- **Correctly configured .fnt files** referencing Noto Sans

**Conclusion:** No font file replacements needed — vanilla is already optimal!

### Archive.exe Command Fix
**Before:** `Archive.exe -e <sga> -o <output>` ❌ (wrong syntax)  
**After:** `Archive.exe -a <sga> -e <output>` ✅ (correct syntax)

### Locale Safety Compliance
✅ Only accessed `Engine/Locale/Chinese/`  
✅ Never touched `Engine/Locale/English/` (forbidden)  
✅ No modifications outside project scope

---

## 📝 NEXT STEPS

1. **Test in-game:**
   - Verify Dark Crusade/Soulstorm modes (no tofu boxes)
   - Check font sizes at different resolutions (640/1024/1280/1600)
   - Test campaign save migration

2. **Documentation updates:**
   - Update BUILD_GUIDE.md with new `make build` workflow
   - Add FONT_STRUCTURE.md reference to README
   - Update CHANGELOG.md for v1.0.5

3. **Release preparation:**
   - Tag as v1.0.5
   - Update Nexus Mods page
   - Publish distribution ZIP

4. **Consider:** 
   - Default font size recommendation (vanilla vs +6)?
   - Separate builds for different font sizes?
   - User survey for optimal font size

---

**Research Report:** [`.copilot_workspace/REGRESSION_RESEARCH_REPORT.md`](.copilot_workspace/REGRESSION_RESEARCH_REPORT.md)  
**Build Complete:** 2026-07-18 10:32 UTC  
**Ready for:** In-game testing and deployment
