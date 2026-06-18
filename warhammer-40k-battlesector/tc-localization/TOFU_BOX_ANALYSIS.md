# Tofu Box (Missing Glyph) Issue — Technical Analysis

**Date:** 2026-06-07  
**Game:** Warhammer 40,000: Battlesector  
**Mod:** Traditional Chinese Localization  
**Status:** ⚠️ **CAMPAIGN DESCRIPTION TOFU BOXES UNRESOLVED**

---

## Problem Statement

**Tofu boxes** (□ squares) appear in Traditional Chinese text, particularly in **campaign/crusade description text**, where characters fail to render.

**Known Issues:**
- Campaign mission descriptions show tofu boxes for subset of TC characters
- Unity Player.log confirms characters "not found in font or any potential fallbacks"
- Estimated ~100-754 characters affected depending on UI context

---

## Root Cause: TextMesh Pro Fallback Limitation

### Font Cascade Chain

The game uses a multi-level fallback chain for description text:

```
futura medium condensed bt SDF - No Underlay (primary)
 ↓ fallback
Generated TMP font (m_AtlasPopulationMode=1, Dynamic, 3295 pre-baked chars)
 ↓ fallback  
No Underlay TMP font (m_AtlasPopulationMode=0, Static, 0 pre-baked TC chars)
 ↓ fallback
Roboto No Underlay
```

### Why Tofu Boxes Occur

1. **Primary font** (`futura`) looks up TC character `繼` (U+7E7C)
2. **Not found** in futura → falls to **Generated** font
3. **Generated font** has 3,295 pre-baked characters:
   - Simplified Chinese baseline
   - 1,246 Traditional Chinese characters
   - Character `繼` is **NOT** in this pre-baked set
4. **Critical limitation:** TMP **only generates glyphs dynamically for PRIMARY fonts**, NOT for fallback fonts
   - Generated is a **fallback** in this chain → no dynamic generation occurs
   - `m_SourceFontFile` reference to NotoSansCJKjp is ignored for fallback contexts
5. Falls through to **No Underlay** font:
   - Has **0 pre-baked TC characters** (empty atlas)
   - **Result:** □ tofu box

**Key Finding:** Despite Generated font having `m_AtlasPopulationMode=1` (Dynamic) and `m_SourceFontFile` pointing to NotoSansCJKjp-Regular, TMP runtime **does not invoke dynamic SDF generation for fallback fonts**. Pre-baking is the only solution.

---

## Attempted Solutions (Implementation Status)

### **Attempt 1-3: Enable Dynamic Generation (FAILED)**

**Approach:**
- Set `m_AtlasPopulationMode=1` on Generated font
- Set `m_IsMultiAtlasTexturesEnabled=1`
- Point `m_SourceFontFile` to embedded NotoSansCJKjp-Regular

**Result:** ❌ **FAILED**
- TMP dynamic SDF generator only runs for **primary fonts**
- Fallback fonts remain static regardless of `m_AtlasPopulationMode` setting
- Tofu boxes persist

### **Attempt 4: Pre-Bake TC Glyphs into No Underlay (IMPLEMENTED, UNTESTED)**

**Approach:** (`patch_font.py` - current implementation)

1. Calculate missing TC chars = (all TC in translation files) - (chars in Generated font)
2. Generate SDF bitmaps for ~754 missing chars using freetype-py + scipy
3. Pack into No Underlay atlas (2048×2048, replacing original 941 SC chars)
4. Update No Underlay font:
   - `m_AtlasPopulationMode = 0` (Static)
   - Rebuild `m_CharacterTable` (Unicode → GlyphIndex mappings)
   - Rebuild `m_GlyphTable` (metrics + atlas rect coordinates)

**Status:** ⚠️ **IMPLEMENTATION EXISTS, NO VERIFIED TEST RESULTS**

**Evidence:**
- Code in `patch_font.py` lines 1-2500 implements full pre-baking pipeline
- No test results confirming campaign descriptions render without tofu
- No Player.log verification that missing char errors are resolved

**Unknown:**
- Does Unity correctly load the pre-baked glyphs from modified atlas?
- Does TMP fallback chain correctly find chars in No Underlay static font?
- Are there additional font reference issues preventing glyph lookup?

### **Attempt 5: Targeted SC Fallback (WORKAROUND, DISABLED BY DEFAULT)**

**Approach:** (`patch_resources.py`)

1. Extract missing char list from Player.log via `extract_missing_glyphs.py`
2. Store in `config/description_fallback_chars.json` (~100 chars)
3. When `MOD_ENABLE_SC_FALLBACK=1`:
   - Convert **only these 100 TC chars** back to SC in `resources.assets`
   - Allows chars to be found in pre-existing SC glyph set

**Status:** ⚠️ **WORKAROUND IMPLEMENTED, DISABLED BY DEFAULT**

**Trade-off:**
- ✅ Eliminates tofu boxes
- ❌ Those ~100 chars render as Simplified instead of Traditional
- ❌ Compromises translation accuracy

**Current Setting:** `MOD_ENABLE_SC_FALLBACK=0` (TC-first, accept tofu until font coverage is complete)

---

## Technical Details

### Pre-Baking Process (Theoretical)

```python
# From patch_font.py
1. Load unknownassets bundle
2. Extract NotoSansCJKjp-Regular font binary (path_id=-951123113223942216)
3. Get existing pre-baked chars from Generated font (path_id=-6634277187469610597)
4. Scan patched/*.txt + dist/resources.assets for TC chars
5. Calculate missing_chars = tc_chars_in_text - pre_baked_chars
6. For each missing char:
   - Render at 17pt with FreeType
   - Generate SDF using distance transform (oversample 4×, padding 9px)
   - Pack into atlas using shelf algorithm
7. Write atlas to No Underlay Texture2D (path_id=4927299259637123988)
8. Update No Underlay TMP_FontAsset (path_id=7178690147649604500):
   - Append to m_CharacterTable
   - Append to m_GlyphTable
   - Set m_AtlasPopulationMode=0 (Static)
```

### Atlas Constraints

- **Size:** 2048×2048 Alpha8 (4,194,304 bytes)
- **Capacity:** ~754 TC glyphs at 17pt + 9px padding
- **Coordinate System:** Bottom-up (Y=0 at bottom edge)

### Font Asset Structure

```
TMP_FontAsset:
  m_AtlasPopulationMode: 0=Static, 1=Dynamic
  m_SourceFontFile: PPtr<Font> // Only used for dynamic primary fonts
  m_CharacterTable: [
    { m_Unicode: 0x7E7C, m_GlyphIndex: 12345 }  // 繼
  ]
  m_GlyphTable: [
    { m_Index: 12345, m_GlyphRect: {x,y,w,h}, m_AtlasIndex: 0 }
  ]
  m_FallbackFontAssetTable: [...]
```

---

## Diagnostic Evidence

### Latest Runtime Capture (2026-06-08)

Captured from:
`/mnt/c/Users/shado/AppData/LocalLow/Black Lab Games/Warhammer 40,000 Battlesector/Player.log`

- Matched missing-glyph entries: **460**
- Observed unique missing codepoints: **80**
- Persisted fallback set (no-merge mode): **80** codepoints

The persisted fallback list is now written to:
`translation/zh-TW/config/description_fallback_chars.json`

This JSON file is the source of truth for runtime-proven fallback glyphs and must be kept in sync with fresh `Player.log` captures.

### Player.log Entries (Confirmed Failures)

```
Character with ASCII value of 32257 (縁) was not found in font or any potential fallbacks
Character with ASCII value of 25104 (拰) was not found in font or any potential fallbacks
The character with Unicode value \u4E26 was not found in the 
[futura medium condensed bt SDF - No Underlay] font asset for the text object [Description].
```

**Source:** `extract_missing_glyphs.py` scanning Player.log

### Affected UI Contexts

From code comments and documented failures:
- ✅ **Confirmed:** Campaign/crusade description text (`Description` text object)
- ❓ **Unknown:** Unit ability tooltips
- ❓ **Unknown:** Menu UI labels (Settings, Load/Save)
- ❓ **Unknown:** In-game barks/subtitles
- ❓ **Separate issue:** Map Builder (different bundle, requires `patch_mapbuilder_font.py`)

---

## Current Status & Open Questions

### ⚠️ Critical Unknowns

1. **Does pre-baking work?**
   - Code exists to generate and inject pre-baked glyphs
   - **NO test confirmation** that game loads them correctly
   - **NO verification** that TMP fallback chain finds them

2. **Why do campaign descriptions fail?**
   - Is it a font reference issue?
   - Is it an atlas loading issue?
   - Is it a coordinate system problem?
   - Is it a glyph table corruption?

3. **What is the actual missing char count?**
   - Code comments say "~754 chars"
   - Player.log evidence shows "~100 chars" in campaign descriptions
   - Are these the same subset or different sets?

### 🔧 What Needs Investigation

1. **Test current build in-game:**
   ```bash
   make build
   make deploy
   # Launch game → campaign screen → check for tofu
   # Check Player.log for "was not found in font" errors
   ```

2. **Verify atlas loading:**
   - Dump modified No Underlay atlas as PNG
   - Confirm SDF bitmaps are correctly packed
   - Verify Y-coordinate flipping is correct (bottom-up vs top-down)

3. **Verify font table integrity:**
   - Check m_CharacterTable has all ~754 entries
   - Check m_GlyphTable glyph indices match Character table
   - Verify m_GlyphRect coordinates are within atlas bounds

4. **Test isolated glyph lookup:**
   - Create minimal test scene with single TMP text object
   - Test fallback chain with known missing char
   - Confirm whether issue is font-specific or system-wide

---

## Next Steps (Recommended)

### Immediate Actions

1. **Run deployment test:**
   ```bash
   cd /home/shado/crystal-mods/warhammer-40k-battlesector/tc-localization
   bash deploy.sh --dry-run  # Preview
   bash deploy.sh            # Deploy to game
   ```

2. **Launch game and document failures:**
   - Navigate to Campaign menu
   - Open mission description
   - Screenshot any tofu boxes
   - Note which characters fail (Unicode values)

3. **Check Player.log:**
   ```bash
   # After playing with TC enabled
   python3 tools/scripts/extract_missing_glyphs.py --tail-lines 20000
   ```

4. **Compare expected vs actual:**
   - Does config/description_fallback_chars.json match Player.log output?
   - Are tofu chars in the ~754 pre-baked set or outside it?

### If Pre-Baking Fails

Consider alternative approaches:
- **Option A:** Inject SC glyphs for ALL missing chars (not just 100)
- **Option B:** Replace campaign description strings with SC entirely
- **Option C:** Redesign font chain to make NotoSans primary (not fallback)
- **Option D:** Multi-atlas support (if 754 chars exceed single atlas capacity)

### Current Fallback Policy (Updated)

- `MOD_ENABLE_SC_FALLBACK=1` is restricted to **campaign Chinese repositories only** (TC-first hard requirement).
- Fallback replacement is still **character-scoped** (only chars from `description_fallback_chars.json` are converted TC→SC).
- Latest fallback-enabled build reverted **2,648** character occurrences to SC in campaign repositories only (with current 80-char fallback set).

---

## Key Files

| File | Purpose | Status |
|------|---------|--------|
| `patch_font.py` | Pre-bake TC glyphs into No Underlay | ⚠️ Implemented, untested |
| `patch_resources.py` | SC fallback workaround | ⚠️ Implemented, disabled |
| `extract_missing_glyphs.py` | Parse Player.log for tofu chars | ✅ Working |
| `config/description_fallback_chars.json` | Known missing char list | ⚠️ May be outdated |
| `dist/unknownassets_*.bundle` | Modified font assets | ⚠️ Unknown if correct |

---

## Conclusion

**Campaign description tofu boxes in WH40K Battlesector TC mod are UNRESOLVED.**

**Root cause identified:** TMP does not generate glyphs dynamically for fallback fonts.

**Attempted solution exists:** Pre-bake ~754 TC chars into No Underlay static atlas.

**Current blocker:** No test verification that pre-baking implementation works.

**Required next action:** Deploy current build, test in-game, document actual vs expected behavior, investigate why pre-baked glyphs are not being found by TMP runtime.

---

## 2026-06-09 Evidence Update (Strict, No-Guess Audit)

### What was verified in this session

1. **Primary pipeline execution is operational and deterministic at file level**
    - `MOD_FONT_PIPELINE=primary_full_tc` completed end-to-end.
    - Dist→game deployment hash verification passed for core artifacts.

2. **Runtime tofu still present after the latest fallback-shell attempt**
    - Recent Player.log parse (tail window) showed:
       - missing events: **326**
       - unique missing codepoints: **25**
       - all warnings attributed to: `futura medium condensed bt SDF - No Underlay`
       - top objects: `PointCostText`, `UnitNameText`, `ArmyCohesionLimit`

3. **Mapbuilder evidence is now concrete (not guessed)**
    - `UnitNameText` GameObject exists in `mapbuildertools_assets_all.bundle`.
    - Its TMP component references local mapbuilder Futura font PID:
       - TMP text component pid: `-5849040548317839404`
       - `m_fontAsset`: `-9186138612217653668` (futura in mapbuilder bundle)

4. **Object locality is broader than unknownassets**
    - Token scans indicate relevant UI tokens in additional bundles:
       - `startup_assets_all.bundle` (cohesion-related)
       - multiple faction bundles (point-cost related tokens)
       - `mapbuildertools_assets_all.bundle` (`UnitNameText`)
    - Therefore, patching only unknownassets cannot be assumed sufficient.

5. **No-blind-fix rule enforced**
    - A strict external audit was run before further implementation.
    - The audit flagged unresolved proof gaps and required gating tests.

### Current confidence statement

- **High confidence** in diagnosis that tofu is multi-bundle/UI-scope, not single-font-file scope.
- **Low confidence** that current unknownassets-only font strategy can reach zero tofu globally.
- **Not release-ready** until bundle/object mapping and validation matrix are completed.

---

## Implementation Plan for Full Functional TC Mod (Evidence-Gated)

### Acceptance gates (must all pass)

1. Zero tofu across campaign/battle/mapbuilder screens in scope.
2. No unintended SC fallback outside explicitly allowed exceptions.
3. Layout remains usable (no severe clipping/overlap regressions).
4. Both deploy paths remain valid: `.ps1` and `.sh`.
5. Deterministic build and deploy hash verification.

### Phase 1 — Asset Topology Mapping (no fixing yet)

Goal: prove where each problematic text object lives and which font asset it binds to.

Tasks:
- Build an evidence table of:
   - bundle file
   - GameObject name
   - TMP MonoBehaviour path ID
   - `m_fontAsset` path ID
   - fallback chain of bound font
- Minimum required object coverage:
   - `PointCostText`
   - `ArmyCohesionLimit`
   - `UnitNameText`
   - `Description`
   - `TitleText`

Exit criteria:
- Every runtime-warning object from Player.log is mapped to a concrete asset path and font PID.

### Phase 2 — Font Binding/Content Strategy by Bundle Class

Goal: choose one deterministic strategy per asset class, not global guessing.

Candidate classes:
- `unknownassets_*` UI
- `startup_assets_all.bundle`
- `mapbuildertools_assets_all.bundle`
- faction-specific bundles

Per-class decision (recorded explicitly):
- A) rebind TMP component font to Noto font asset, or
- B) keep Futura but pre-bake verified missing set into that exact font asset.

Exit criteria:
- Design matrix documented with per-bundle implementation method and rationale.

### Phase 3 — Controlled Implementation

Rules:
- Implement in smallest safe increments.
- One bundle class at a time.
- After each change, run structure validation before deploy.

Required validations after each increment:
- TMP table integrity:
   - `m_CharacterTable` sorted
   - no duplicate Unicode entries
   - all glyph refs valid
   - atlas bounds valid
- Hash verification dist→game for touched artifacts.

### Phase 4 — Runtime Verification Matrix

For each target screen flow:
- Launch and navigate specific UI paths.
- Parse fresh Player.log tail.
- Report:
   - total missing events
   - unique codepoints
   - unique font assets
   - top text objects

Pass/fail gate:
- **Fail if any tofu warnings remain in in-scope screens.**

### Phase 5 — Release Hardening

- Re-run deterministic build check (repeat build hash consistency).
- Verify both deployment scripts (`deploy.sh`, `deploy.ps1`) reflect final pipeline.
- Update docs with:
   - exact scope
   - known exclusions (if any)
   - reproducible verification steps.

---

## Immediate Next Work Items (ordered)

1. Complete mapping for `PointCostText` and `ArmyCohesionLimit` (currently unresolved object-level binding evidence).
2. Generate a single source-of-truth CSV/MD table for object→font bindings across bundles.
3. Only then implement targeted per-bundle patching (starting with mapbuilder/startup paths verified by evidence).

No additional broad font rewrites should be attempted before (1) and (2) are complete.

---

## 2026-06-09 Independent Harsh Review (No-Guess Protocol)

This section records an adversarial review pass and supersedes any speculative
assumptions. The following items are now mandatory gates before further font
mutation work.

### Critical findings

- Diagnosis scope and implementation scope were misaligned: evidence points to
   multiple bundles (`startup`, faction bundles, `mapbuildertools`), while core
   mutation logic mainly targeted `unknownassets` (+ mapbuilder).
- `primary_full_tc` path currently mixes potentially conflicting intents
   (Futura bake + Futura shell-normalize), which can obscure causal attribution.
- Pipeline default remains `legacy`; comparisons must be explicitly pinned to
   avoid mode drift.
- Existing log extraction has filtering that can miss real offenders (ASCII log
   format, non-target font names, object names outside fixed allowlist).
- Campaign SC fallback policy does not explain current top offenders
   (`PointCostText`, `ArmyCohesionLimit`, `UnitNameText`).

### No-guess evidence protocol (must run in order)

1. Freeze run conditions per test case:
    - pipeline mode, commit SHA, deploy hashes, cache-clear status, log boundary.
2. Parse full-spectrum missing glyph telemetry (Unicode + ASCII line formats).
3. Build complete bundle inventory for TMP components and bound font assets in:
    - `unknownassets_*`, `startup_assets_all.bundle`, all faction bundles,
       `mapbuildertools_assets_all.bundle`.
4. Resolve PPtr reference integrity (local vs cross-bundle vs unresolved).
5. Join runtime warnings to concrete `(bundle, component pid, font chain)`.
6. Validate bound font table integrity:
    - sorted CharacterTable, no duplicate Unicode, valid glyph refs, in-bounds
       rects, valid atlas/material references.
7. Reproduce by flow-isolated runs, then compare deltas.

### Phased implementation with hard gates

- **Phase 0 — Observability hardening**
   - Build machine-readable reports for warnings + object/font inventory.
   - Gate: warning tuples can be mapped deterministically.

- **Phase 1 — Complete offender mapping**
   - Map all warning tuples from latest run to concrete assets/components.
   - Gate: 100% mapped or explicitly marked unresolved with evidence.

- **Phase 2 — Minimal-risk fixes first (binding integrity)**
   - Fix proven bad bindings/PPtr integrity before glyph redesign.
   - Gate: targeted flow warnings drop with no collateral increase.

- **Phase 3 — Coverage fixes by bundle class**
   - Apply per-bundle strategy only after mapping (pre-bake or deterministic
      fallback proven by runtime evidence).
   - Gate: per-flow tofu reaches zero before moving to next class.

- **Phase 4 — Regression hardening**
   - Two consecutive clean runs with identical verification outcomes.

### Validation matrix (pass thresholds)

- Missing-glyph events (in-scope flows): **0**
- Unique missing codepoints: **0**
- Warning tuple attribution: **100% mapped**
- Duplicate Unicode in CharacterTable: **0**
- Invalid glyph references: **0**
- Out-of-bounds glyph rects: **0**
- Dist→game deployment hash: **100% match**
- New warnings in previously clean flows: **0 increase**

### Anti-patterns (explicitly disallowed)

- Treating deploy/hash success as rendering correctness proof.
- Broad font rewrites before full offender mapping.
- Mixed `legacy`/`primary_full_tc` comparisons without explicit pinning.
- Using filtered log parsers as exhaustive telemetry.
- Letting stale Player.log windows contaminate new runs.
