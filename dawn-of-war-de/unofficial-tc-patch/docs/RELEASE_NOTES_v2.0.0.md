# Release Notes — DoW DE TC Mod v2.0.0 (Fontdecor Fix)

**Release Date:** 2026-06-06  
**Status:** ✅ Ready for Distribution  

---

## What's Fixed

### Dark Crusade Campaign Tofu Box Issue ✅

**Problem (v1.x):** Dark Crusade campaign showed Chinese text as tofu boxes (□□□) when TC mod deployed.

**Root Cause:** TC's modified `fontdecor.gfx` file was broken—intentionally stripped (1.0MB vs 8.7MB vanilla) but incorrectly done, removing critical glyph/font table data needed for rendering.

**Solution (v2.0.0):** Removed `fontdecor.gfx` from mod distribution. Engine now automatically uses the vanilla `fontdecor.gfx` from the original `EnginLoc.sga`, which has complete glyph data.

**Result:** ✅ Chinese text renders perfectly everywhere, including Dark Crusade campaign.

---

## What's Included

| Component | Status | Note |
|-----------|--------|------|
| TC Fonts (24 .ttf/.ttc) | ✅ Included | Noto Sans/Serif TC, Microsoft YaHei, Gulim |
| Font Config Files (36 .fnt) | ✅ Included | High-DPI sized, TC font references |
| Engine.ucs | ✅ Included | Traditional Chinese text corrections |
| fontdecor.gfx | ❌ Removed | Uses vanilla from EnginLoc.sga |
| fontaux.gfx | ✅ Included | TC optimized (410KB) |
| fontbody.gfx | ✅ Included | TC optimized (410KB) |
| fonthead.gfx | ✅ Included | TC optimized (411KB) |
| font_glyphs.gfx | ✅ Included | TC Chinese glyph atlas (1.0MB) |
| Sound Files | ✅ Included | Optional audio (identical to vanilla) |

---

## Installation (Unchanged)

### Vortex Mod Manager (Recommended)
1. Download `wh40k-dow-de-tc-mod-v2.0.0.zip` from releases
2. Drag onto Vortex → Deploy Mods
3. Launch game

### Manual (Linux / WSL2 / Windows)
```bash
# Linux / WSL2
bash deploy.sh

# Windows (PowerShell)
.\deploy.ps1
```

### Important
- ✅ Game automatically uses vanilla `fontdecor.gfx` (no user action needed)
- ✅ All TC modifications remain active
- ✅ Chinese text renders correctly throughout the game

---

## Technical Details

### Binary Search Testing (7 iterations)

To isolate the cause, we tested:

| Test | Configuration | Result |
|------|---|---|
| Hybrid 1 | TC fonts + vanilla art | ✅ PASS |
| Hybrid 2 | vanilla fonts + TC art/sound | ❌ TOFU |
| Hybrid 3 | vanilla fonts + vanilla art + TC sound | ✅ PASS |
| Test 4A | TC fontaux+fontbody + vanilla fontdecor+fonthead | ✅ PASS |
| Test 4B | TC fontdecor+fonthead + vanilla fontaux+fontbody | ❌ TOFU |
| Test 4C | **TC fontdecor only** → ❌ TOFU | **CULPRIT FOUND** |
| Test 4D | TC fonthead only | ✅ PASS |

**Conclusion:** `fontdecor.gfx` was the sole culprit.

### Why Vanilla fontdecor.gfx Works

The `.gfx` files are compiled Scaleform GFX bytecode (binary Flash format) containing:
- UI layout definitions
- Glyph/font tables (character bitmap references)
- Asset definitions
- Font binding metadata

TC's stripped version lacked critical glyph table data. Vanilla version has complete data → rendering works.

---

## Changes

### Code Changes
- `deploy.sh` (loose + SGA modes): Added `--exclude="fontdecor.gfx"` to rsync commands
- Removed `data/art/ui/swf/fontdecor.gfx` from distribution

### New Documentation
- `docs/FONTDECOR_ROOT_CAUSE_ANALYSIS.md` — Full technical analysis with hex dumps, test results, and recommendations

---

## Compatibility

| Mode | Status | Note |
|------|--------|------|
| Vortex Deploy | ✅ | Automatic |
| Manual Loose Deploy | ✅ | Using updated deploy.sh |
| SGA Mode | ✅ | Using updated deploy.sh |
| Custom Deployment | ⚠️ | Just exclude fontdecor.gfx |

---

## Upgrade Path

If using v1.x:

**Option 1 (Recommended):**
1. Uninstall v1.x mod
2. Install v2.0.0
3. Launch game

**Option 2 (Keep progress):**
1. Download v2.0.0
2. Delete old `data/art/ui/swf/fontdecor.gfx` from game directory (if deployed)
3. Deploy v2.0.0
4. Launch game

---

## Known Issues

None. Rendering fully functional.

---

## Verification Checklist

After deployment, verify:
- [ ] Main menu Chinese text displays correctly
- [ ] Campaign selection screen shows Chinese properly
- [ ] Dark Crusade campaign opens without crash
- [ ] In-game Chinese text renders (unit names, tooltips, subtitles)
- [ ] No tofu boxes appear anywhere
- [ ] Performance unchanged

---

## Credits

**Bug Investigation:** 7-iteration binary search isolating fontdecor.gfx  
**Root Cause Analysis:** Binary format inspection (hex dumps, string extraction)  
**Fix:** Deployment automation updated to exclude broken file

---

## Support

For issues or questions:
1. Check `docs/FONTDECOR_ROOT_CAUSE_ANALYSIS.md` for technical details
2. Verify vanilla `EnginLoc.sga` is not corrupted
3. Try fresh deployment (revert old mod, deploy v2.0.0)

---

## Version History

| Version | Date | Status |
|---------|------|--------|
| v2.0.0 | 2026-06-06 | ✅ Release (fontdecor fix) |
| v1.x | Earlier | Archived (fontdecor tofu issue) |

---

**End of Release Notes**
