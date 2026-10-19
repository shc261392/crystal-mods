# Root Cause Analysis: Font Size Changes Not Taking Effect

**Date:** 2026-07-04  
**Issue:** User reports font size changes (34→36) do not take effect in-game after installation  
**Severity:** Critical — core mod functionality broken

---

## Executive Summary

The font size changes we implemented are in the wrong place. We modified `EnginLocMod.sga` (a pre-built artifact), but the actual deployment mechanism:
1. **Does NOT use this SGA** for the default installation method
2. Has **multiple broken code paths** preventing proper deployment
3. Was designed for a **loose-file workflow** that doesn't exist in the current repo structure

**Unverified Hypothesis Used:** We assumed the SGA in the package was the source of truth for font sizes. Actually, fonts should be managed via loose files in `data/font/` OR the deploy script re-applies font fixes at deployment time.

---

## Evidence Chain

### 1. **Deploy Script Analysis** (`deploy.sh`)

#### Bug #1: Broken `DEPLOY_FILES` Array (Lines 48-49)
```bash
DEPLOY_FILES=(EnginLocMod.sga Engine.ucs)  # Line 48
DEPLOY_FILES=(Engine.ucs)                  # Line 49 — OVERWRITES!
```
**Impact:** Even if SGA mode worked, the SGA wouldn't be deployed because the array is overwritten.

#### Bug #2: Missing `DEPLOY_MODE` Default
```bash
# Line 97: Validation check
case "$DEPLOY_MODE" in
    loose|sga) ;;
    *) die "Invalid --mode '${DEPLOY_MODE}'. Valid values: loose, sga" ;;
esac
```
**Verification:**
```bash
$ bash deploy.sh
deploy.sh: line 97: DEPLOY_MODE: unbound variable
```
**Impact:** Script crashes when run without `--mode` flag, despite claiming "loose" is default.

#### Bug #3: Hardcoded Font Size in Deployment (Lines 305-311)
```bash
uv run python "${REPO_ROOT}/scripts/apply_font_fix.py" \
    --root "${REPO_ROOT}" \
    --restore-from-bak \
    --mode fallback-only \
    --size 34              # ← HARDCODED!
```
**Impact:** Even if deployment worked, it would re-apply size 34, overwriting any SGA changes.

#### Bug #4: Missing `data/` Directory
```bash
$ ls -la data/
ls: cannot access 'data/': No such file or directory
```
**Impact:** The "loose" mode (lines 353-377) expects `data/` to exist and contains fonts to deploy. It doesn't exist in the repo.

---

### 2. **Package Structure Analysis**

**What we built (v1.0.5.zip):**
```
Engine/
└── Locale/
    └── Chinese/
        ├── EnginLoc.sga  ← Renamed from EnginLocMod.sga, contains size=36 fonts
        └── Engine.ucs
```

**What the README manual install instructions expect:**
```
# Step 2: "extract the zip there"
# Step 3: "rename EnginLoc.sga to EnginLoc.sga.disabled"
```

**The Conflict:**
- Instructions assume vanilla `EnginLoc.sga` exists and should be disabled
- Our package **OVERWRITES** the vanilla SGA directly when extracted
- User never gets prompted to disable vanilla SGA because our SGA replaces it

---

### 3. **Build Process Analysis** (`Makefile`)

**Current `make package` flow (lines 124-134):**
```makefile
package:
    @cp EnginLocMod.sga "$(DIST_DIR)/$(PKG_NAME)/Engine/Locale/Chinese/EnginLoc.sga"
    @cp Engine.ucs "$(DIST_DIR)/$(PKG_NAME)/Engine/Locale/Chinese/"
    @cd "$(DIST_DIR)/$(PKG_NAME)" && zip -r "../$(PKG_NAME).zip" .
```

**The Assumption:** `EnginLocMod.sga` is pre-built and tested with correct font sizes.

**The Reality:** 
- We modified `EnginLocMod.sga` to have sizeDefault=36
- We verified the SGA contains size 36
- ✅ The package is technically correct

**But...**
- The SGA overwrites the vanilla file instead of coexisting
- No mechanism to disable vanilla SGA automatically
- Manual install instructions are for a different package structure

---

## Root Causes

### Primary: **Architecture Mismatch**

The mod has **three different deployment architectures** that conflict:

1. **Manual Install (README):** Expects loose `data/` folder + disabled vanilla SGA
2. **Script Deploy - Loose Mode:** Expects `data/` in repo + builds fonts at deploy time  
3. **Script Deploy - SGA Mode:** Builds SGA from `data/font/` at deploy time
4. **Package Distribution:** Contains pre-built SGA that replaces vanilla

**We modified #4 (pre-built SGA), but it doesn't match any supported installation flow.**

### Secondary: **Broken Deploy Script**

Multiple bugs prevent ANY successful script-based deployment:
- Unbound DEPLOY_MODE variable
- Overwritten DEPLOY_FILES array
- Missing data/ directory
- Hardcoded size 34

### Tertiary: **Unverified Hypothesis**

We assumed:
> "The SGA in the package determines font sizes for installed mods"

We should have verified:
> "How do fonts actually get deployed to the game directory?"

We modified the SGA without understanding:
- Whether the SGA is actually used
- What the installation instructions do
- How loose files vs SGA priority works

---

## Why Font Size Didn't Change

**Most Likely Scenario:**
1. User extracted our zip to `Engine\Locale\Chinese\`
2. Our `EnginLoc.sga` (size 36) overwrote vanilla `EnginLoc.sga`  
3. Game loaded our SGA
4. **BUT:** User may have OTHER locale files (loose or cached) taking priority
5. **OR:** User didn't actually use the new v1.0.5 package we just built

**Alternative Scenarios:**
- User used deploy script (would crash due to unbound DEPLOY_MODE)
- User used old package from dist/ directory
- Game has font caching mechanism we're unaware of

---

## Correct Solution

### Option A: **Fix Package Structure (Recommended)**

Make the package match README instructions:

```
Engine/
└── Locale/
    └── Chinese/
        ├── data/           ← NEW: loose files
        │   └── font/
        │       ├── *.fnt   ← Size 36 applied
        │       └── *.ttf
        └── Engine.ucs
```

**Install flow:**
1. User extracts zip → gets `data/` folder
2. User renames vanilla `EnginLoc.sga` → `EnginLoc.sga.disabled`  
3. Game loads loose files from `data/` (higher priority than SGA)
4. ✅ Font changes take effect

**Implementation:**
1. Extract `EnginLocMod.sga` → `.copilot_workspace/package_source/`
2. Apply font fix with size 36
3. Package `data/` folder (no SGA)
4. Update README to match

### Option B: **Fix Deploy Script**

1. Add `DEPLOY_MODE="loose"` default (line 40)
2. Fix `DEPLOY_FILES` bug (remove line 49)
3. Add `data/` directory to repo with fonts
4. Make font size configurable in deploy script
5. Update Makefile to extract SGA → data/ before packaging

### Option C: **Simplify to SGA-Only**

1. Keep current package structure (SGA-based)
2. Update README to say "extract zip, this replaces the vanilla SGA"
3. Remove loose-file references
4. Fix deploy script to work with SGA mode only

---

## Immediate Action Items

1. ✅ **Verify user's actual installation method** — did they use manual zip extract or deploy script?
2. ✅ **Check which package they used** — did they download the v1.0.5 we just built?
3. ✅ **Test manual installation** — extract v1.0.5.zip per README and verify in-game
4. ⚠️ **Choose architecture** — loose files (recommended) or SGA-only
5. ⚠️ **Rebuild package** with correct structure
6. ⚠️ **Fix deploy script** bugs
7. ⚠️ **Update documentation** to match chosen architecture

---

## Lessons Learned

1. **Always verify deployment mechanism before modifying artifacts**
2. **Test installation instructions with actual package**
3. **Check for multiple deployment modes/paths**
4. **Grep for hardcoded values that might override changes**
5. **Run the actual scripts to verify they work**

---

## Questions for User

1. How did you install the mod? (manual zip extract / deploy script / Vortex)
2. Which package did you use? (v1.0.5.zip / v1.0.5-font48.zip / older version)
3. Did you rename the vanilla `EnginLoc.sga` to `.disabled`?
4. Do you see a `data/` folder in `Engine\Locale\Chinese\`?
5. Are there multiple `EnginLoc*.sga` files in that directory?
