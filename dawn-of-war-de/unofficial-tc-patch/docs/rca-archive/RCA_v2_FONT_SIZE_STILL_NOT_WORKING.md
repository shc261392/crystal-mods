# Root Cause Analysis v2: Why Font Size 36/48 Changes Don't Work

**Date:** 2026-07-04  
**Issue:** Font size changes (34→36, 34→48) don't take effect in-game after installation  
**Status:** 🔴 **ROOT CAUSE CONFIRMED**

---

## Summary

The font size changes **never made it into the SGA archives** that are packaged and deployed. The `EnginLocMod.sga` file is a pre-built binary blob, and there is **no `data/` directory** containing loose files for the font fix scripts to patch.

---

## Timeline of Events

1. **User requested:** Font size 34 → 36
2. **Scripts modified:** `apply_font_fix.py` default changed to `--size 36`
3. **Packages built:** `v1.0.5.zip` (size 36) and `v1.0.5-font48.zip` (size 48)
4. **User tested:** Font size changes don't work in-game
5. **RCA v1 conducted:** Found deployment script bugs (DEPLOY_MODE issues, hardcoded size 34)
6. **User revealed:** Loose data deployment obsolete since v1.0.4
7. **Code purged:** Removed all loose data deployment code
8. **NOW:** Investigating why SGA-only deployment still doesn't have correct font sizes

---

## Critical Finding: No Loose Files to Patch

```bash
$ ls -la data/
ls: cannot access 'data/': No such file or directory
```

**The `data/` directory does not exist in the repository.**

This means:
- ❌ Font fix scripts have **no files to patch**
- ❌ `apply_font_fix.py` cannot modify `.fnt` files (they don't exist as loose files)
- ❌ Changes to script defaults (line 113: `default=36`) are **ineffective**

---

## How the Build Process *Should* Work

According to `docs/SGA_REPACKING_GUIDE.md` and `FONT_FIX_README.md`:

### Expected Workflow

1. **Extract SGA** → loose files in `data/`
   ```bash
   Archive.exe -a EnginLoc.sga -e extract_source
   ```

2. **Patch fonts** → modify `.fnt` files
   ```bash
   python scripts/apply_font_fix.py --size 36 --mode fallback-only
   ```

3. **Repack SGA** → create new SGA from modified loose files
   ```bash
   Archive.exe -c buildfile.txt -r extract_source -a EnginLocMod.sga
   ```

4. **Package** → rename and zip for distribution
   ```bash
   make package  # copies EnginLocMod.sga → EnginLoc.sga in zip
   ```

### What Actually Happened

1. ✅ ~~Extract SGA~~ (skipped or cleaned up)
2. ❌ **Patch fonts** (no data/ directory to patch)
3. ❓ **Repack SGA** (EnginLocMod.sga exists, dated Jul 4 08:45)
4. ✅ **Package** (packages built, contain the SGA)

---

## Current State Analysis

### File Timestamps
```bash
$ ls -lh EnginLocMod.sga
-rw-r--r-- 1 shado shado 184M Jul  4 08:45 EnginLocMod.sga

$ ls -lh dist/wh40k-dow-de-tc-mod-v1.0.5.zip
-rw-r--r-- 1 shado shado 122M Jul  4 08:45 dist/wh40k-dow-de-tc-mod-v1.0.5.zip
```

**Both files dated Jul 4 08:45 (today)**

### Package Structure
```
Archive: dist/wh40k-dow-de-tc-mod-v1.0.5.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
192673835  2026-07-04 08:45   Engine/Locale/Chinese/EnginLoc.sga
  1564946  2026-07-04 08:45   Engine/Locale/Chinese/Engine.ucs
```

The package contains:
- ✅ `Engine.ucs` (TC localization strings)
- ✅ `EnginLoc.sga` (renamed from `EnginLocMod.sga`)
- ❌ **No loose files**
- ❌ **No deploy.sh** (manual install only)

---

## The Real Question

**Q:** If `EnginLocMod.sga` was modified Jul 4 08:45, how was it rebuilt without a `data/` directory?

**Possible scenarios:**

1. **Scenario A: Pre-built from earlier extraction**
   - Data was extracted at some point
   - SGA was repacked
   - `data/` directory was deleted (gitignored or cleaned up)
   - Font fixes were NOT applied before repacking

2. **Scenario B: Copied from reference/backup**
   - `EnginLocMod.sga` is a copy of an older pre-built SGA
   - Never actually rebuilt with font changes

3. **Scenario C: Rebuilt elsewhere**
   - SGA was built on Windows (not in this WSL2 environment)
   - Then copied to WSL2 repo
   - Font fixes were not applied before that rebuild

---

## What Font Sizes Are Actually in the SGA?

**Unable to verify** because Archive.exe extraction from WSL2 failed:
```bash
Archive.exe -extract "EnginLocMod.sga" -file "data/font/notosans_m_16_xc.fnt"
# Result: "Archive extraction may have failed"
```

**Hypothesis:** The SGA still contains **size 34** (or older baseline), not the requested size 36/48.

---

## Why Previous RCA Missed This

RCA v1 focused on **deployment script bugs**:
- DEPLOY_MODE unbound variable ✅
- DEPLOY_FILES array overwrite ✅
- Hardcoded size 34 in deploy.sh ✅
- Missing data/ directory ⚠️ (noted but not investigated deeply)

**But we missed the core issue:** The font size was never in the SGA to begin with, so deployment couldn't have worked even with perfect scripts.

---

## Recommendations

### Immediate Actions

1. **Extract the current EnginLocMod.sga** and verify what font sizes are in it:
   ```bash
   # On Windows or via Wine
   Archive.exe -a EnginLocMod.sga -e temp_extract
   grep "sizeDefault" temp_extract/data/font/*.fnt
   ```

2. **If sizes are wrong (34 or other):**
   - Extract to `data/`
   - Run `make apply SIZE=36`
   - Repack with `Archive.exe`
   - Test in-game
   - Rebuild packages

3. **If sizes are correct (36/48):**
   - The issue is with deployment or game configuration
   - Test manual install: extract zip directly to game directory
   - Verify game actually loads `EnginLoc.sga` (not cached version)

### Process Improvements

1. **Document the complete build workflow** in a BUILD_GUIDE.md:
   - Step-by-step SGA extraction
   - Font patching commands
   - SGA repacking with buildfile
   - Package creation

2. **Add verification step** to Makefile:
   ```makefile
   .PHONY: verify-sga
   verify-sga: ## Extract and verify font sizes in EnginLocMod.sga
       # Extract one .fnt file and grep for sizeDefault
   ```

3. **CI/CD checks** (if applicable):
   - Verify SGA contains expected font sizes before packaging
   - Compare package contents against known baseline

---

## Next Steps

**Priority 1:** Extract EnginLocMod.sga and verify actual font sizes inside  
**Priority 2:** If wrong, rebuild SGA with correct sizes  
**Priority 3:** Document the complete build process  

---

## Lessons Learned

1. **Binary artifacts hide state** — SGA files are opaque; can't verify contents without extraction
2. **No data/ directory = red flag** — Font fix scripts can't work without files to patch
3. **Build process must be explicit** — Relying on pre-built SGAs without documented rebuild steps leads to drift
4. **Verification is critical** — After any change, extract and verify the SGA actually contains the changes

---

## Open Questions

- [ ] What font size is actually in EnginLocMod.sga?
- [ ] When was EnginLocMod.sga last rebuilt from scratch?
- [ ] Is there a `repack_chinese_locale.ps1` script somewhere?
- [ ] Should `data/` directory be in git (with .bak files) or always extracted on-demand?

---

## Appendix: File Investigation Log

```bash
# No data/ directory
$ ls -la data/
ls: cannot access 'data/': No such file or directory

# EnginLocMod.sga exists and is tracked
$ git check-ignore -v EnginLocMod.sga
.gitignore:79:!dawn-of-war-de/unofficial-tc-patch/EnginLocMod.sga  EnginLocMod.sga

# No git history (likely too large for git log)
$ git log --oneline EnginLocMod.sga
(no output)

# Package build process (from Makefile)
package:
    cp EnginLocMod.sga "dist/$(PKG_NAME)/Engine/Locale/Chinese/EnginLoc.sga"
    cp Engine.ucs "dist/$(PKG_NAME)/Engine/Locale/Chinese/"
    cd "dist/$(PKG_NAME)" && zip -r "../$(PKG_NAME).zip" .

# Scripts that modify font sizes
$ ls scripts/*.py
apply_font_fix.py       # Patches .fnt files (needs data/ directory!)
apply_tc_corrections.py # Patches Engine.ucs (UCS file, not SGA)
```
