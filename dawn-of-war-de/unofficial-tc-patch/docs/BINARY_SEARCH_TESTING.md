# Binary Search Testing Protocol — SGA Rendering Issue

**Objective:** Isolate which TC mod component causes Chinese text tofu boxes in SGA mode.

**Status:** Hybrid SGAs created, awaiting game testing.

---

## Test Hypothesis

**Observation:** 
- TC-modded SGA deployed → Game shows tofu boxes (Chinese rendered as placeholder glyphs)
- Loose TC files had same issue
- Need to identify which specific modification causes failure

**Test Strategy:** Binary search via hybrid archives
- **Hybrid 1:** TC FONTS + Original ART/SOUND → Isolates font changes
- **Hybrid 2:** TC ART/SOUND + Original FONTS → Isolates art/UI changes

---

## Test Execution Plan

### Phase 1: Deploy Hybrid 1 (TC FONTS + Original ART/SOUND)

**Expected Result If FONTS Are Culprit:**
- ✓ Renders correctly (proves fonts work)
- OR ✗ Shows tofu boxes (proves fonts cause issue)

**Steps:**
```bash
# 1. Backup current state
cp /mnt/d/.../EnginLoc.sga backup/

# 2. Deploy Hybrid 1
cp EnginLocHybrid1_TCFonts.sga /mnt/d/.../EnginLoc.sga

# 3. Launch game
# 4. Test Dark Crusade campaign
# 5. Document rendering behavior
```

---

### Phase 2: Deploy Hybrid 2 (TC ART/SOUND + Original FONTS)

**Expected Result If ART/SOUND Are Culprit:**
- ✓ Renders correctly (proves art/sound OK)
- OR ✗ Shows tofu boxes (proves art/sound cause issue)

**Steps:**
```bash
# 1. Deploy Hybrid 2
cp EnginLocHybrid2_TCArt.sga /mnt/d/.../EnginLoc.sga

# 2. Launch game
# 3. Test Dark Crusade campaign
# 4. Document rendering behavior
```

---

## Expected Outcomes & Next Steps

### Scenario A: Hybrid 1 renders correctly, Hybrid 2 fails
- **Conclusion:** TC art/UI files cause the issue
- **Next:** Bisect art/ folder (5 .gfx files)
- **Analysis:** Likely font_glyphs.gfx or UI modification

### Scenario B: Hybrid 1 fails, Hybrid 2 renders correctly
- **Conclusion:** TC font modifications cause the issue
- **Next:** Bisect font changes
- **Analysis:** Font reference corruption or encoding issue

### Scenario C: Both render correctly
- **Conclusion:** Issue is NOT in SGA content
- **Next:** Investigate SGA metadata or engine loading
- **Analysis:** File system vs archive-level difference

### Scenario D: Both show tofu boxes
- **Conclusion:** Multiple issues or fundamental engine problem
- **Next:** Fallback to loose mode or manual debugging
- **Analysis:** Issue is at engine level, not content level

---

## Archive Details

| Archive | Source Files | Size | Compression |
|---------|--------------|------|-------------|
| EnginLocHybrid1_TCFonts.sga | 58 (TC fonts + original art/sound) | TBD | gfx=Stream, fnt=Buffer, ttf=Store |
| EnginLocHybrid2_TCArt.sga | 43 (TC art/sound + original fonts) | TBD | gfx=Stream, fnt=Buffer, ttf=Store |

---

## Deployment Checklist

```
Pre-Test:
  [ ] Both hybrid archives created
  [ ] Integrity tests PASSED
  [ ] Backups in place (.copilot_workspace/)
  [ ] Game installation accessible
  [ ] Original vanilla SGA backed up

Test 1 - Hybrid 1 (TC Fonts):
  [ ] Deploy archive
  [ ] Launch game
  [ ] Navigate to campaign
  [ ] Check Chinese rendering
  [ ] Document result (tofu/correct/mixed)
  [ ] Take screenshot if possible

Test 2 - Hybrid 2 (TC Art/Sound):
  [ ] Deploy archive
  [ ] Launch game
  [ ] Navigate to campaign
  [ ] Check Chinese rendering
  [ ] Document result (tofu/correct/mixed)
  [ ] Take screenshot if possible

Analysis:
  [ ] Compare results
  [ ] Determine culprit component
  [ ] Plan next bisection if needed
  [ ] Document findings
```

---

## Test Results Template

### Hybrid 1: TC Fonts + Original Art/Sound

**Deployed:** `EnginLocHybrid1_TCFonts.sga` (90M)  
**Date/Time:**  
**Tester:**  

**Chinese Text Rendering:**
- [ ] Renders correctly (no tofu)
- [ ] Shows tofu boxes
- [ ] Mixed (some correct, some tofu)
- [ ] Cannot test (game error)

**Campaign Access:** Working / Broken  
**Error Messages:** (if any)  
**Screenshot:** (if available)  

**Conclusion:**

---

### Hybrid 2: TC Art/Sound + Original Fonts

**Deployed:** `EnginLocHybrid2_TCArt.sga` (TBD)  
**Date/Time:**  
**Tester:**  

**Chinese Text Rendering:**
- [ ] Renders correctly (no tofu)
- [ ] Shows tofu boxes
- [ ] Mixed (some correct, some tofu)
- [ ] Cannot test (game error)

**Campaign Access:** Working / Broken  
**Error Messages:** (if any)  
**Screenshot:** (if available)  

**Conclusion:**

---

## Rollback Instructions

If any test breaks the game, restore vanilla state:

```bash
# 1. From WSL2
GAME_PATH="/mnt/d/SteamLibrary/steamapps/common/Dawn of War Definitive Edition"
LOCALE_PATH="$GAME_PATH/Engine/Locale/Chinese"

# 2. Restore backup
cp "$LOCALE_PATH/EnginLoc.sga.disabled" "$LOCALE_PATH/EnginLoc.sga"

# 3. Verify game launches
```

---

## Archive Locations

**Created:** `/home/shado/crystal-mods/.copilot_workspace/`

```
EnginLocHybrid1_TCFonts.sga     → TC fonts + original art/sound
EnginLocHybrid2_TCArt.sga       → TC art/sound + original fonts
```

**Backups & References:**
```
EnginLocTC.sga                  → Full TC-modded (200M, baseline)
EnginLocRepacked.sga            → Vanilla repacked (193M, reference)
EnginLoc.sga.disabled           → Original vanilla (190M, game dir)
```

---

## Success Criteria

**Binary search successful when:**
- [x] Both hybrid archives created
- [x] Integrity tests passed
- [ ] Game launches with at least one hybrid
- [ ] Chinese rendering testable
- [ ] Clear culprit identified (fonts vs art/sound)

**Follow-up:**
- If fonts culprit → Bisect 24 font files
- If art/sound culprit → Bisect 5 .gfx files + 4 audio files
- If both fail → Investigate engine-level SGA handling

---

**Document Version:** 1.0  
**Created:** 2026-06-06  
**Status:** Ready for testing
