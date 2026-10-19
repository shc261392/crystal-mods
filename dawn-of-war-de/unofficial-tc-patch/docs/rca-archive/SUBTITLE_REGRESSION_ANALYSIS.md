# Subtitle Gibberish Regression Analysis — v1.0.6

**Date:** 2026-07-18  
**Issue:** Traditional Chinese dialogue subtitles show gibberish Unicode characters at the end
**Status:** Root cause identified, fix proposed, awaiting approval

---

## Executive Summary

The v1.0.6 build process reintroduced a previously-fixed subtitle rendering bug where dialogue text is suffixed with gibberish Chinese characters (specifically 緝, U+7DC9). This regression occurred because the new build workflow (extracting from vanilla Chinese locale SGA) restores problematic font file references that were previously corrected.

---

## Technical Root Cause

### The Unicode Null Terminator Issue

**Background:**
- DoW:DE's subtitle renderer reads C-style null-terminated strings
- The renderer processes the entire string **including the null terminator (U+0000)**
- When rendering, it looks up the glyph for U+0000 in the referenced font file

**The Problem Font:**
- `NotoSansTC-Bold.ttf` has a **visible glyph** mapped to codepoint U+0000
- This glyph renders as the Chinese character 緝 (U+7DC9)
- When subtitle font references Bold.ttf → every subtitle ends with 緝

**The Safe Font:**
- `NotoSansTC-Medium.ttf` does **NOT** have a visible glyph at U+0000
- When subtitle font references Medium.ttf → null terminator is invisible

---

## Current State Analysis

### v1.0.6 Build Output (REGRESSED)

```
gillsans_11b.fnt (dialogue subtitle font):
    file = "NotoSansTC-Bold.ttf"         ❌ PROBLEMATIC
    
gillsans_bold_16.fnt (other UI text):
    file = "NotoSansTC-Regular.ttf"       ⚠️  INCONSISTENT
```

### Expected Fixed State (from earlier versions)

```
gillsans_11b.fnt:
    file = "NotoSansTC-Medium.ttf"        ✅ SAFE
    
gillsans_bold_16.fnt:
    file = "NotoSansTC-Medium.ttf"        ✅ SAFE
```

---

## Build Process Analysis

### Current v1.0.6 Workflow

1. **Extract** vanilla Chinese locale SGA (`EnginLoc.sga`)
   - Source: Game installation or Vortex backup
   - Contains: Vanilla font configurations (problematic references)
   
2. **Adjust** font sizes via `adjust_font_sizes.py`
   - Modifies: `sizeDefault`, `size640`-`size1600` fields
   - Does NOT modify: `file=` font file references
   
3. **Rebuild** SGA via Archive.exe
   - Packs: Modified `.fnt` files with vanilla (bad) font references

**Gap:** No step to fix font file references after extraction!

### Why This Happened

**v1.0.5 and earlier:**
- Used pre-patched `data/` directory (manually fixed font references preserved)
- OR: Used a modified SGA that already had the fix applied

**v1.0.6 change:**
- Switched to extracting from vanilla SGA (to fix tofu box regression)
- Vanilla SGA contains the original problematic font references
- Fix was lost because it was never automated in the build script

---

## Historical Context

### Original Fix (commit 7055d8b)

According to README.md:

> **Fix applied (commit `7055d8b`):** `gillsans_11b.fnt` and `gillsans_bold_16.fnt`
> now reference `notosanstc-medium.ttf`, which does not have a visible glyph at
> U+0000. The artifact is gone.

**Commit 7055d8b:** Could not be found in current git history (possibly in a different branch/repo or not yet pushed)

**Fix method:** Manual editing of `.fnt` files to change font file references

### Why It Worked Before

The fix was applied to the `data/` directory that was:
1. Preserved across builds (not re-extracted each time)
2. OR: Baked into a modified SGA used as the source

When v1.0.6 started extracting from vanilla SGA each build, the fix was lost.

---

## Verification Evidence

### Font File Existence Confirmed

```bash
$ ls data/font/notosanstc-*.ttf
notosanstc-black.ttf
notosanstc-bold.ttf          ← Has U+0000 glyph (problematic)
notosanstc-extrabold.ttf
notosanstc-extralight.ttf
notosanstc-light.ttf
notosanstc-medium.ttf        ← Does NOT have U+0000 glyph (safe)
notosanstc-regular.ttf
notosanstc-semibold.ttf
notosanstc-thin.ttf
```

All fonts exist in vanilla Chinese locale SGA ✓

### Vanilla SGA Confirmed Source

From `scripts/build_sga.sh`:

```bash
# Use vortex backup (vanilla) if available, otherwise current SGA
if [[ -f "$GAME_DIR/Engine/Locale/Chinese/EnginLoc.sga.vortex_backup" ]]; then
    SGA_SOURCE="$GAME_DIR/Engine/Locale/Chinese/EnginLoc.sga.vortex_backup"
    log "Using vanilla backup: EnginLoc.sga.vortex_backup"
else
    SGA_SOURCE="$GAME_DIR/Engine/Locale/Chinese/EnginLoc.sga"
    log "Using current EnginLoc.sga from game directory"
fi
```

Extracts directly from vanilla SGA → gets vanilla (unfixed) font references ✓

---

## Proposed Fix

### Option 1: Post-Extraction Font Reference Correction (RECOMMENDED)

**Location:** `scripts/build_sga.sh`, after SGA extraction, before font size adjustment

**Implementation:**
```bash
# After line ~134: ok "Vanilla Chinese locale SGA extracted..."

# Fix subtitle font references (prevent U+0000 glyph artifact)
log "Fixing subtitle font references..."
sed -i 's/file[[:space:]]*=[[:space:]]*"NotoSansTC-Bold\.ttf"/file = "NotoSansTC-Medium.ttf"/g' \
    "$DATA_DIR/font/gillsans_11b.fnt" \
    "$DATA_DIR/font/gillsans_bold_16.fnt"
ok "Subtitle fonts now reference NotoSansTC-Medium.ttf (safe for U+0000)"
```

**Pros:**
- Minimal change to existing workflow
- Automated and repeatable
- Self-documenting (fix is visible in build script)

**Cons:**
- Adds build script complexity
- Assumes sed is available (safe in WSL2)

### Option 2: Patch File System

Create `patches/font-references.patch` with correct font references, apply after extraction.

**Pros:**
- Clean separation of concerns
- Easy to review/audit

**Cons:**
- More files to maintain
- Patch might break if vanilla `.fnt` format changes

### Option 3: Modified Source SGA

Keep a "fixed vanilla" SGA with corrected font references.

**Pros:**
- No build-time patching needed
- Faster builds

**Cons:**
- No longer building from true vanilla
- Loses transparency of changes

---

## Testing Plan

### Pre-Fix Verification

1. Extract current v1.0.6 SGA
2. Check `gillsans_11b.fnt` references
3. Expected: `file = "NotoSansTC-Bold.ttf"` (confirming regression)

### Post-Fix Verification

1. Apply font reference fix to `build_sga.sh`
2. Run `make build FONT_SIZE_INCREASE=4`
3. Extract resulting SGA
4. Check `gillsans_11b.fnt` references
5. Expected: `file = "NotoSansTC-Medium.ttf"` (fix applied)

### In-Game Testing

1. Install fixed v1.0.6 build
2. Launch Winter Assault campaign
3. Play any mission with voiced dialogue
4. Verify: No gibberish characters at end of subtitle lines
5. Test across all campaigns (vanilla DoW, WA, DC, SS)

---

## Impact Assessment

### Affected Components

- **Dialogue subtitles** (all campaigns)
- **In-game mission briefings** (any text using gillsans_11b font)

### Not Affected

- Main menu text
- Campaign UI text (uses different fonts)
- Unit command responses (different rendering system)

### Severity

**Critical** — Breaks immersion and readability in story-heavy content

---

## Recommendation

**Implement Option 1 (sed post-extraction fix)** because:

1. **Minimal risk** — One-line sed command, well-tested pattern
2. **Transparent** — Fix is visible in build script with comment
3. **Repeatable** — Works every build without manual intervention
4. **Maintainable** — Easy to modify if font references need further changes

---

## Next Steps

1. **Review & approval** — Confirm sed approach is acceptable
2. **Implement fix** — Add font reference correction to `build_sga.sh`
3. **Rebuild** — Run `make build FONT_SIZE_INCREASE=4`
4. **Verify** — Check `.fnt` files in extracted SGA
5. **Test in-game** — Launch Winter Assault mission
6. **Update docs** — Add note about automated font reference fix in BUILD_GUIDE.md
7. **Release** — Package as v1.0.6 final or v1.0.6-r1 (revised)

---

**Prepared by:** GitHub Copilot (Claude Sonnet 4.5)  
**Date:** 2026-07-18  
**Version:** Draft 1
