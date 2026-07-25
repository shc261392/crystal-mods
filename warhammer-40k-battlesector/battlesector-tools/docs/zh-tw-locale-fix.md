# Traditional Chinese (zh-TW) Locale Fix

## Issue

The zh-TW locale in `src/data/i18n.json` was using Simplified Chinese (zh-CN) text instead of Traditional Chinese.

**Example:**
- ❌ Before: `智库` (Simplified)
- ✅ After: `智庫` (Traditional)

## Root Cause

During the v1.7.4 game update migration, the game's bundled Chinese localization switched from Traditional to Simplified. The battlesector-tools zh-TW locale should use Traditional Chinese from the tc-localization mod, but it was incorrectly populated with Simplified Chinese.

## Solution

Created `scripts/update-zh-tw-locale.cjs` to:
1. Read Traditional Chinese translations from `../tc-localization/translation/zh-TW/patched/units.txt`
2. Match unit/weapon nameIds to their Traditional Chinese names
3. Update the zh-TW section in `src/data/i18n.json`

## Running the Script

```bash
node scripts/update-zh-tw-locale.cjs
```

**Prerequisites:**
- tc-localization mod must be in `../tc-localization/` (relative to battlesector-tools)
- tc-localization must have `translation/zh-TW/patched/units.txt`

## Verification

```bash
# Check that zh-TW has Traditional Chinese
node -e "const d = require('./src/data/i18n.json'); console.log('zh-TW unit 1:', d.unitNames['zh-TW']['1']); console.log('zh-CN unit 1:', d.unitNames['zh-CN']['1']);"

# Expected output:
# zh-TW unit 1: 智庫  (Traditional - note the 庫 character)
# zh-CN unit 1: 智库  (Simplified - note the 库 character)
```

## Coverage

- **122 units** with Traditional Chinese translations
- **298 weapons** with Traditional Chinese translations
- Some DLC units/weapons may be missing (will fall back to English)

## Related Files

- `src/data/i18n.json` - Main localization data file
- `../tc-localization/translation/zh-TW/patched/units.txt` - Source TC translations
- `scripts/update-zh-tw-locale.cjs` - Update script

## Date Fixed

2026-07-26
