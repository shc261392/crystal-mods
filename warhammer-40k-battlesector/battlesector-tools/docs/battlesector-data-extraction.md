# Warhammer 40K Battlesector - Data Extraction Guide

**Last updated**: 2026-07-10

This document explains the complete data extraction and processing pipeline for the Battlesector Tools website.

---

## Overview

Game data flows through three stages:

1. **Unity Asset Extraction** - AssetRipper exports Unity game files to YAML
2. **Stats Parsing** - Python scripts extract stats from YAML into JSON
3. **Website Preparation** - Python scripts transform stats into website-ready JSON

---

## Source Data Location

**Raw Unity Assets (YAML)**:
```
/mnt/d/mods/battlesector/ExportedProject/Assets/MonoBehaviour/
├── UnitDataTable.asset          (190 units, ~600KB)
├── WeaponDataTable.asset        (442 weapons, ~2MB)
├── AbilityDataTable.asset       (abilities)
└── [other game tables]
```

**Extracted via**: AssetRipper (Unity asset extraction tool)

---

## Stage 1: Parse Stats from YAML

**Script**: `.copilot_workspace/battlesector-data/parse_stat_assets.py`

**What it does**:
- Reads `UnitDataTable.asset` and `WeaponDataTable.asset` (Unity YAML format)
- Decodes hex-encoded integer keys to game IDs
- Extracts complete stat blocks (damage, armor, abilities, etc.)
- Merges with text repository names from previous extraction
- **Extracts weapon abilities** (added 2026-07-10)

**Output**: `complete_stats/`
```
├── units_complete.json          (190 units, full stats)
├── weapons_complete.json        (442 weapons, full stats + abilities)
├── units_complete.csv           (CSV export)
└── weapons_complete.csv         (CSV export)
```

**Run**:
```bash
cd .copilot_workspace/battlesector-data
python3 parse_stat_assets.py
```

---

## Stage 2: Prepare Website Data

**Script**: `.copilot_workspace/battlesector-data/prepare_website_data.py`

**What it does**:
- Reads `complete_stats/*.json`
- Resolves localization IDs to actual text (en/zh-CN/zh-TW/etc.)
- Includes zh-TW translations from TC mod source files
- Filters out placeholder/unknown entries
- Adds computed fields (isMelee, weapon types, etc.)
- **Includes weapon abilities** (added 2026-07-10)
- Generates search index

**Output**: `src/data/` (written directly)
```
├── units.json                   (~158KB, 187 units)
├── weapons.json                 (~205KB, 439 weapons with abilities)
├── abilities.json
├── factions.json
├── roles.json
├── i18n.json                    (multilingual strings)
└── public/search-index.json
```

**Run**:
```bash
cd .copilot_workspace/battlesector-data
python3 prepare_website_data.py
```

---

## Weapon Abilities Discovery (2026-07-10)

### Bug Found and Fixed

**Problem**: Weapon abilities were not being extracted from game data.

**Root Cause**:
1. `parse_stat_assets.py` - Missing line: `'abilities': weapon.get('Abilities', [])`
2. `prepare_website_data.py` - Missing line: `"abilities": w.get("abilities")`

**Impact**: Website showed 0 weapons with abilities (actual: 23 weapons)

**Fix Applied**: Added ability extraction to both scripts

### Weapons with Abilities

**Total**: 23 weapons have abilities attached

**Ability #20000 (Blessed Ammunition)**:
- Bolt Pistol (ID 2003, 2035)
- Storm Bolter (ID 2034)
- Godwyn De'az Pattern Bolter (ID 2036)
- Effect: +50% Ranged Damage, -10 Graze Chance, 2 ammo, 3 turn cooldown
- StartsLocked: 1 (must be unlocked in-game)

**Other Common Abilities**:
- Ability #80030 - Found on Missile Launcher, Spore Mine Launcher, etc.
- Ability #70002 - Found on Ion weapons (Ion Rifle, Ion Cannon, Ion Accelerator)

---

## Data Schema

### Weapon Abilities Format

In `weapons.json`:
```json
{
  "id": 2036,
  "name": "Godwyn De'az Pattern Bolter",
  "abilities": [
    {
      "Ability": 20000,
      "StartsLocked": 1
    }
  ]
}
```

- `Ability`: Integer ID referencing ability in abilities data
- `StartsLocked`: 0 = available immediately, 1 = must unlock

---

## Verification Commands

### Check weapon abilities in complete stats
```bash
cd .copilot_workspace/battlesector-data/complete_stats
python3 -c "
import json
data = json.load(open('weapons_complete.json'))
count = sum(1 for w in data if w.get('abilities') and len(w['abilities']) > 0)
print(f'Weapons with abilities: {count}')
"
```

### Find weapons with specific ability
```bash
cd .copilot_workspace/battlesector-data/complete_stats
python3 -c "
import json
ability_id = 20000
data = json.load(open('weapons_complete.json'))
for w in data:
    if w.get('abilities'):
        for a in w['abilities']:
            if a.get('Ability') == ability_id:
                print(f'ID {w[\"weapon_id\"]}: {w[\"name\"]}')
"
```

### Verify website data includes abilities
```bash
cd warhammer-40k-battlesector/battlesector-tools/src/data
python3 -c "
import json
data = json.load(open('weapons.json'))
weapon = next((w for w in data if w['id'] == 2036), None)
print(f'{weapon[\"name\"]}: {weapon.get(\"abilities\")}')
"
```

---

## Troubleshooting

### Abilities showing as `null` or `[]`

**Check**: Did you run both scripts after adding the ability extraction lines?

```bash
# Re-extract from YAML
cd .copilot_workspace/battlesector-data
python3 parse_stat_assets.py

# Re-prepare website data
python3 prepare_website_data.py
```

### File not found errors

**Check**: Are you running from the correct directory?

Scripts expect to be run from `.copilot_workspace/battlesector-data/`

### Name resolution issues

**Check**: Text repository data in `parsed_data/` and `extracted_text_assets/`

If names show as "Unknown Weapon X", the localization ID mapping may be incomplete.

---

## Future Enhancements

### Potential Additions
- Extract ability definitions (name, description, effects) from `AbilityDataTable.asset`
- Extract status effects from game data
- Add unit model counts and squad composition
- Extract voice bark assignments (currently skipped - see weapon abilities false positive)

### Known Limitations
- Some localization IDs don't resolve (show as "Unknown")
- Weapon variant detection is based on different entries, not explicit variant flags
- Abilities must be cross-referenced with ability definitions separately

---

## Related Documentation

- [Data Extraction Verification](./data-extraction-verification.md) - Ability #20000 investigation
- [Weapon Abilities UI Implementation Plan](../../.copilot_workspace/weapon-abilities-ui-implementation-plan.md)
- Main README: Tool usage and deployment

---

## Questions?

If extraction results don't match expectations:
1. Check source YAML files exist at expected paths
2. Verify Python environment has `pyyaml` installed
3. Check for Unity YAML format changes (AssetRipper version differences)
4. Review extraction script output for warnings/errors
