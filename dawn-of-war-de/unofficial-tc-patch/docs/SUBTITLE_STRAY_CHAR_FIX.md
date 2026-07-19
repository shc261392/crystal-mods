# Subtitle Stray Character Regression Fix — v1.0.7+

## Issue Summary

**Symptom**: ALL dialogue subtitles show a stray Chinese character suffix (e.g., "餘", "緝") after every line, across all campaigns and modes.

**Affected Versions**: v1.0.7 deployed build (2026-07-19 and earlier)

**Fixed in**: v1.0.7+ (build script updated 2026-07-19)

## Root Cause Analysis

### The Problem

The vanilla Chinese locale SGA uses **`NotoSansTC-Regular.ttf`** for subtitle fonts, but the build script only fixed **`NotoSansTC-Bold.ttf`** → `NotoSansTC-Medium.ttf`.

**Why stray characters appeared:**

Both `NotoSansTC-Regular.ttf` and `NotoSansTC-Bold.ttf` have **visible glyphs mapped to Unicode U+0000** (null terminator). DoW's subtitle renderer includes null terminators in strings, causing the fonts' U+0000 glyphs to render as gibberish Chinese characters.

| Font                    | U+0000 Glyph | Renders As | Used In File         |
|------------------------|--------------|------------|---------------------|
| NotoSansTC-Bold.ttf    | ✓ HAS        | 緝 U+7DC9  | (was in old builds) |
| NotoSansTC-Regular.ttf | ✓ HAS        | 餘 U+9918  | gillsans_bold_16.fnt |
| NotoSansTC-Medium.ttf  | ✗ NONE       | (safe)     | (the fix)           |

### Build Script Gap

The original fix (commit 7055d8b) only handled `NotoSansTC-Bold.ttf`:

```bash
# OLD (incomplete)
sed -i 's/file.*"NotoSansTC-Bold\.ttf"/file = "NotoSansTC-Medium.ttf"/g' \
    "$DATA_DIR/font/gillsans_11b.fnt" \
    "$DATA_DIR/font/gillsans_bold_16.fnt"
```

**Problem**: Vanilla Chinese locale uses `NotoSansTC-Regular.ttf`, not Bold!

## The Fix

### Updated Build Script

Added second sed pattern to handle `NotoSansTC-Regular.ttf`:

```bash
# NEW (complete)
sed -i \
    -e 's/file.*"NotoSansTC-Bold\.ttf"/file = "NotoSansTC-Medium.ttf"/g' \
    -e 's/file.*"NotoSansTC-Regular\.ttf"/file = "NotoSansTC-Medium.ttf"/g' \
    "$DATA_DIR/font/gillsans_11b.fnt" \
    "$DATA_DIR/font/gillsans_bold_16.fnt"
```

### Verification

**Pre-fix (v1.0.7 deployed)**:
```
gillsans_11b.fnt:     file = "NotoSansTC-Medium.ttf"   ✅ (was already fixed)
gillsans_bold_16.fnt: file = "NotoSansTC-Regular.ttf"  ❌ (caused stray chars)
```

**Post-fix (v1.0.7+ rebuild)**:
```
gillsans_11b.fnt:     file = "NotoSansTC-Medium.ttf"   ✅
gillsans_bold_16.fnt: file = "NotoSansTC-Medium.ttf"   ✅
```

## Related Issues

This is the **same root cause** as the original "緝" suffix issue documented in README.md, but with a different symptom character because:

1. Original issue: `NotoSansTC-Bold.ttf` → renders 緝 (U+7DC9)
2. This issue: `NotoSansTC-Regular.ttf` → renders 餘 (U+9918)

Both fonts have different glyphs at U+0000, hence different suffix characters.

## Prevention

### For Future Releases

1. **After rebuilding SGA**, extract and verify subtitle fonts:
   ```bash
   # Extract built SGA
   Archive.exe -a EnginLocMod.sga -e verify/
   
   # Check both subtitle fonts
   grep 'file\s*=' verify/font/gillsans_11b.fnt
   grep 'file\s*=' verify/font/gillsans_bold_16.fnt
   
   # Both MUST show: file = "NotoSansTC-Medium.ttf"
   ```

2. **In-game test**: Launch any campaign and verify dialogue subtitles have NO stray characters

## Timeline

- **2026-07-19**: Issue reported (stray "餘" character in all subtitles)
- **2026-07-19**: Root cause identified (`gillsans_bold_16.fnt` → `NotoSansTC-Regular.ttf`)
- **2026-07-19**: Build script fixed to handle both Bold and Regular variants
- **2026-07-19**: Fix verified in rebuilt SGA

## References

- Original subtitle fix (commit 7055d8b): Fixed Bold → Medium
- This fix: Also handle Regular → Medium
- README.md: Documents the U+0000 glyph artifact issue
