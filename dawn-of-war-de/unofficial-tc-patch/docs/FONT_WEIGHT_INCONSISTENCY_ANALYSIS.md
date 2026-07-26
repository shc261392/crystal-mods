# Font Weight Inconsistency Analysis

## Issue Report

**Observed Problem**: Text display shows visual inconsistency in character weight and smoothness.

**Example**: In "懷言者軍團", the character "言" appears heavier/bolder than the other 4 characters, and overall font rendering appears less smooth than standard Noto Sans TC.

## Root Cause Analysis

### Current Font Configuration

The mod currently uses **3 different Noto Sans TC font weights** across UI elements:

| `.fnt` File | TTF Font | Weight | Usage |
|-------------|----------|--------|-------|
| `gillsans_11.fnt` | NotoSansTC-Regular.ttf | 400 (Regular) | UI text (small) |
| `gillsans_11b.fnt` | NotoSansTC-Bold.ttf | 700 (Bold) | UI text (bold) |
| `gillsans_16.fnt` | NotoSansTC-Regular.ttf | 400 (Regular) | UI text (medium) |
| `gillsans_bold_16.fnt` | NotoSansTC-Regular.ttf | 400 (Regular) | UI text (bold medium) ⚠️ |
| `albertus extra bold12.fnt` | NotoSansTC-Medium.ttf | 500 (Medium) | Small headers |
| `albertus extra bold14.fnt` | NotoSansTC-Medium.ttf | 500 (Medium) | Medium headers |
| `albertus extra bold16.fnt` | NotoSansTC-Regular.ttf | 400 (Regular) | Large headers |
| `albertus extra bold20.fnt` | NotoSansTC-Bold.TTF | 700 (Bold) | Title headers |

### Why This Causes Visual Inconsistency

**Problem 1: Mixed Weights in Same Context**

When the game renders text that spans multiple `.fnt` files (e.g., unit names mixing regular and header fonts), characters are drawn from different font weight files:

- Character "懷" might use Regular (weight 400) → thinner strokes
- Character "言" might use Bold (weight 700) → **thicker strokes** ← This explains the heavier appearance
- Characters "者軍團" use Regular again → thinner strokes

**Result**: Visual "weight jumping" where some characters appear bolder than others in the same text string.

**Problem 2: Rendering Quality Differences**

Different font weights (Regular/Medium/Bold) may have:
- Different hinting optimizations
- Different anti-aliasing behavior at game render sizes
- Different glyph outline complexity

This causes the "not as smooth as regular Noto Sans TC" observation — the font IS Noto Sans TC, but mixing weights disrupts consistent rendering.

---

## Proposed Solution

### Option 1: Standardize to Medium Weight (Recommended)

**Change all `.fnt` files to use `NotoSansTC-Medium.ttf` (weight 500)**

**Rationale**:
- ✅ Medium provides good readability at all sizes
- ✅ Heavier than Regular (more visible on background textures)
- ✅ Lighter than Bold (won't appear "too heavy" for body text)
- ✅ Single weight = consistent rendering across all UI elements
- ✅ Already used for headers (albertus extra bold12/14)

**Implementation**:
```bash
# Update build_sga.sh to replace all font references
sed -i 's/NotoSansTC-Regular\.ttf/NotoSansTC-Medium.ttf/g' data/font/*.fnt
sed -i 's/NotoSansTC-Bold\.ttf/NotoSansTC-Medium.ttf/gi' data/font/*.fnt
```

### Option 2: Use Regular Weight Everywhere

**Change all `.fnt` files to use `NotoSansTC-Regular.ttf` (weight 400)**

**Pros**:
- Lightest weight, most "standard" appearance
- Closest to original English fonts

**Cons**:
- May be too thin for readability on textured backgrounds
- Chinese characters have more strokes → thinner weight can reduce legibility

### Option 3: Use Two-Weight System (Regular + Bold)

**Keep Regular for body text, Bold only for explicit headers**

**Pros**:
- Maintains typographic hierarchy

**Cons**:
- ❌ **Doesn't solve the inconsistency problem** if headers and body mix in same text
- ❌ Still have weight jumping in unit names/tooltips

---

## Testing Plan

### Before Fix
1. Extract screenshot of "懷言者軍團" showing weight inconsistency
2. Note which character appears heavier
3. Document current `.fnt` → TTF mappings

### After Fix (Option 1)
1. Rebuild SGA with all fonts using Medium weight
2. Deploy to game
3. Screenshot same text ("懷言者軍團")
4. Verify uniform character weight
5. Check overall smoothness/readability

### Validation Criteria
- ✅ All characters in same text string have visually consistent stroke weight
- ✅ Font rendering appears smooth (no jagged edges, consistent anti-aliasing)
- ✅ Readability maintained across all UI contexts (tooltips, unit cards, dialogues)

---

## Implementation Checklist

- [ ] User approval for Option 1 (Medium weight standardization)
- [ ] Update `scripts/build_sga.sh` to include font weight normalization
- [ ] Add sed commands to replace all font file references
- [ ] Document the change in BUILD_GUIDE.md
- [ ] Rebuild SGA with fix applied
- [ ] **Manual test deployment** (user performs)
- [ ] Visual verification via screenshot
- [ ] User approval before final release

---

## Recommendation

**Proceed with Option 1: Standardize to NotoSansTC-Medium.ttf**

This provides the best balance of:
- Visual consistency (single weight)
- Readability (Medium is designed for UI text)
- Alignment with existing header fonts (already using Medium)

**CRITICAL**: This is a data modification. Following Rule #5:
- ✅ Hypothesis documented here
- ✅ Awaiting explicit user approval before implementation
- ✅ Manual testing required after build
- ✅ No automated deployment
