# Traditional Chinese (zh-TW) Locale - OpenCC Conversion

## Overview

The battlesector-tools website uses **OpenCC** to convert Simplified Chinese (zh-CN) to Traditional Chinese (zh-TW) for all game text.

**Why OpenCC?**
- The game does not have official Traditional Chinese localization
- OpenCC provides accurate character-by-character conversion (Simplified → Traditional)
- Covers ALL units, weapons, factions, and roles (base game + all DLC)

## Conversion Process

The `scripts/convert-zh-tw-opencc.cjs` script:
1. Loads `src/data/i18n.json`
2. Converts ALL zh-CN text to zh-TW using OpenCC
3. Updates `unitNames`, `weaponNames`, `factionNames`, `roleNames`

## Running the Conversion

```bash
# Install opencc-js if not already installed
pnpm add -D opencc-js

# Run conversion
node scripts/convert-zh-tw-opencc.cjs
```

## Verification

```bash
# Check a sample unit (Canoness Selicia)
node -e "const d = require('./src/data/i18n.json'); console.log('zh-TW:', d.unitNames['zh-TW']['2022']); console.log('zh-CN:', d.unitNames['zh-CN']['2022']);"

# Expected output:
# zh-TW: 修女長塞利西亞  (Traditional - note 長, 亞)
# zh-CN: 修女长塞利西亚  (Simplified - note 长, 亚)
```

## Example Conversions

| Entity | Simplified (zh-CN) | Traditional (zh-TW) |
|--------|-------------------|---------------------|
| Canoness Selicia | 修女长塞利西亚 | 修女長塞利西亞 |
| Sister Leona | 修女莱昂娜 | 修女萊昂娜 |
| Zephyrim | 风天使 | 風天使 |
| Dominions | 自治领 | 自治領 |

## When to Run

Re-run the OpenCC conversion when:
- New units/weapons are added to zh-CN locale
- zh-CN translations are updated
- DLC content is added to the game data

## Related Files

- `scripts/convert-zh-tw-opencc.cjs` - OpenCC conversion script
- `src/data/i18n.json` - Localization data file
- `package.json` - Contains opencc-js dependency

## Date Implemented

2026-07-26

## Notes

- OpenCC conversion is deterministic (same input → same output)
- Some proper nouns may have multiple valid Traditional forms; OpenCC uses Taiwan standard (tw)
- Manual review is recommended for character names and lore-specific terms
