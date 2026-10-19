# DAWDE Unofficial TC Patch - Regression Fix Verification
**Date**: 2026-07-18  
**Status**: ✅ FIX VERIFIED & BUILT

---

## 🔍 Issue Summary
**Problem**: Chinese text renders as tofu boxes in Dark Crusade/Soulstorm mode  
**Root Cause**: Regression in commit `70b37e3` (July 4, 2026) - broken TC fontdecor.gfx (989K) packed into mod SGA  
**Solution**: Replace with vanilla fontdecor.gfx (8.4MB) containing complete glyph tables

---

## ✅ Fix Implementation

### Modified Scripts
- `scripts/rebuild_sga_auto.sh` - Added fontdecor.gfx replacement logic
- `scripts/master_rebuild.sh` - Added fontdecor.gfx replacement step

### Build Process
```bash
bash scripts/rebuild_sga_auto.sh
```

**Output**:
```
✓ fontdecor.gfx replaced: 8.4M
✓ Using vanilla version (fixes tofu box rendering)
✓ Font size verified: sizeDefault = 36
✓ EnginLocMod.sga created successfully!
  Size: 212M
  Modified: 2026-07-18 08:32:02
```

---

## 📦 Distribution Package

**Package**: `dist/wh40k-dow-de-tc-mod-v1.0.5.zip`

### Contents
```
Engine/
  Locale/
    Chinese/
      EnginLoc.sga    (212M) ← Contains fixed fontdecor.gfx
      Engine.ucs      (1.5M)
```

### Verification
Extracted `EnginLoc.sga` and confirmed:
```bash
$ find .copilot_workspace/verify_fix -name "fontdecor.gfx" -exec ls -lh {} \;
-rw-r--r-- 1 shado shado 8.4M Jul 18 08:51 .../art/ui/swf/fontdecor.gfx
```

✅ **CONFIRMED**: Vanilla fontdecor.gfx (8.4MB) is included in the package

---

## 📊 Comparison

| Metric | Before Fix | After Fix | Change |
|--------|-----------|-----------|--------|
| fontdecor.gfx | 989K (broken) | 8.4M (vanilla) | ✅ Fixed |
| EnginLoc.sga | 205M | 212M | +7M |
| Font size | Mixed/broken | 36 (consistent) | ✅ Fixed |
| Tofu boxes | ❌ Present | ✅ Should be gone | Needs testing |

**Size Analysis**:
- Previous broken build: 205MB (included broken 989K fontdecor.gfx + bloat)
- Fixed build: 212MB (includes vanilla 8.4MB fontdecor.gfx)
- Size increase: +7MB (correct - vanilla fontdecor.gfx is 8.4MB vs 989K)

---

## 🧪 Testing Required

**Manual Deployment** (DO NOT AUTOMATE):
1. Extract `dist/wh40k-dow-de-tc-mod-v1.0.5.zip`
2. Copy `Engine/` folder to game directory
3. **IMPORTANT**: Backup original `Engine/Locale/Chinese/EnginLoc.sga` first!

**In-Game Testing**:
1. Launch Dawn of War: Dark Crusade
2. Start/continue a campaign
3. **Expected**: Chinese text renders correctly (no tofu boxes)
4. **Success Criteria**: All UI text, tooltips, and dialogue display proper Chinese characters

**If tofu boxes persist**:
- Check game directory for conflicting mods
- Verify `Engine/Locale/Chinese/EnginLoc.sga` was replaced (212M)
- Check locale setting in game options (should be Chinese)

---

## 📝 Technical Details

### Why fontdecor.gfx Matters

**Format**: Scaleform GFX (compiled SWF bytecode)

**Contents**:
- UI layout definitions
- **Glyph/font tables** (character bitmap references) ← Critical!
- Asset definitions
- Font binding metadata

**TC Mod Version** (broken):
- Size: 989K (87% smaller than vanilla)
- Font reference: "Noto Serif" (incomplete CJK coverage)
- Glyph data: **DELETED** ← This causes tofu boxes

**Vanilla Version** (working):
- Size: 8.4M
- Font reference: Full Chinese font stack
- Glyph data: **COMPLETE** ← Includes all Chinese character mappings

### Regression Timeline

1. **v1.0.2 (2026-06-06)**: Original fix - exclude fontdecor.gfx via rsync
2. **July 4, 2026 12:15**: Last working build (184MB)
3. **July 4, 2026 14:04**: Regression introduced (205MB) - commit `70b37e3`
4. **July 4, 2026 14:51**: Refactor commit pushed (new rebuild scripts)
5. **July 18, 2026 08:32**: Fix rebuilt (212MB) - fontdecor.gfx replacement logic added

---

## 🎯 Summary

✅ **Root cause identified**: SGA rebuild scripts packed broken TC fontdecor.gfx  
✅ **Fix implemented**: Scripts updated to replace with vanilla version  
✅ **Build verified**: EnginLoc.sga contains 8.4MB vanilla fontdecor.gfx  
✅ **Package ready**: `dist/wh40k-dow-de-tc-mod-v1.0.5.zip` (137MB compressed)  
⏸️ **Pending**: Manual deployment and in-game testing by user

---

## 📚 Related Documentation

- **Full analysis**: `.copilot_workspace/REGRESSION_ANALYSIS_2026-07-12.md`
- **Original fix**: `docs/FONTDECOR_ROOT_CAUSE_ANALYSIS.md`
- **Build logs**: `.copilot_workspace/rebuild_test_*.log`

---

**Next Steps**: Deploy manually and test Dark Crusade/Soulstorm campaigns for Chinese text rendering.
