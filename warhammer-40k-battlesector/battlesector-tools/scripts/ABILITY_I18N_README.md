# Ability i18n Integration Helper

Semi-automated tool to integrate multi-language support for unit abilities using in-game translation data.

## Overview

This script matches English ability text from `ability-overrides.source.json` to game localization entries in `text_repository` files, then extracts all available translations to generate an i18n-ready data structure.

## Data Sources (Priority Order)

1. **Game extracted text** (primary authority):
   - `.copilot_workspace/battlesector-data/extracted_text_assets/text_repository-*.txt`
   - English, German, French, Spanish, Korean, Polish, Portuguese (BR), Russian, Chinese (Simplified)

2. **TC localization mod** (Traditional Chinese):
   - `../tc-localization/translation/zh-TW/source/zh-TW/text_repository-*.txt`

3. **Manual overrides** (when automated matching fails):
   - Add to `ability-overrides.source.json` or review output

## Usage

### Basic Usage

```bash
# Run integration (writes output files)
pnpm run i18n:integrate-abilities

# Dry run (preview only, no files written)
pnpm run i18n:integrate-abilities:dry
```

### Output Files

1. **`src/data/ability-i18n.json`** (main output):
   ```json
   {
     "generatedAt": "2026-07-04T...",
     "source": "ability-overrides.source.json + game text_repository files",
     "stats": {
       "totalAbilities": 61,
       "matched": 58,
       "exact": 45,
       "fuzzy": 13,
       "manual": 0,
       "needsReview": 3
     },
     "abilities": [
       {
         "abilityId": 1,
         "textId": 12345,
         "locales": {
           "en": { "description": "..." },
           "zh-CN": { "description": "..." },
           "zh-TW": { "description": "..." },
           "de": { "description": "..." }
         },
         "confidence": "exact"
       }
     ]
   }
   ```

2. **`.copilot_workspace/ability-i18n-review.json`** (if fuzzy matches exist):
   - Lists abilities that need manual review
   - Shows top candidate matches with similarity scores
   - Use this to verify fuzzy matches or add textIds to source

## Matching Logic

### Text Normalization
- Removes extra whitespace
- Normalizes line breaks
- Case-insensitive comparison

### Confidence Levels

- **Exact** (100% match): Direct text match, high confidence
- **Fuzzy** (≥95% match): Very close match, should review
- **Manual** (&lt;95% match): Needs human verification

### Similarity Algorithm

Uses Levenshtein distance normalized by text length:
```
similarity = 1.0 - (levenshtein_distance / max_length)
```

Thresholds:
- Title matching: ≥90%
- Description matching: ≥85%

## Workflow

### Initial Integration

1. **Extract game data** (if not already done):
   ```bash
   # Game files must be extracted to .copilot_workspace/battlesector-data/
   # See docs/game-mechanics.md for extraction process
   ```

2. **Run dry run to preview**:
   ```bash
   pnpm run i18n:integrate-abilities:dry
   ```

3. **Review output** and check stats:
   - How many exact vs fuzzy matches?
   - Are critical abilities matched?

4. **Run actual integration**:
   ```bash
   pnpm run i18n:integrate-abilities
   ```

5. **Review fuzzy matches** (if any):
   ```bash
   cat .copilot_workspace/ability-i18n-review.json
   ```

### Manual Review Process

For abilities flagged for review:

1. Check the top candidate matches
2. Verify the description text matches the ability
3. If correct: Note the textId for future reference
4. If incorrect: Add manual translation to `ability-overrides.source.json` or mark for follow-up

### Integrating into Application

After generating `ability-i18n.json`:

1. **Update i18n data loader**:
   ```typescript
   // src/data/i18n.json or similar
   import abilityI18n from './ability-i18n.json';
   ```

2. **Create ability localization accessor**:
   ```typescript
   export function abilityText(
     id: number,
     field: 'title' | 'description',
     locale: string = 'en'
   ): string {
     const ability = abilityI18n.abilities.find(a => a.abilityId === id);
     return ability?.locales[locale]?.[field] ?? fallback;
   }
   ```

3. **Update components**:
   ```astro
   <!-- AbilityCard.astro -->
   <p data-i18n-ability-desc={ability.id}>
     {abilityText(ability.id, 'description', locale)}
   </p>
   ```

4. **Update client-side i18n**:
   ```typescript
   // src/scripts/i18n.ts
   export function applyAbilityI18n(locale: string): void {
     for (const el of document.querySelectorAll('[data-i18n-ability-desc]')) {
       const id = Number(el.dataset.i18nAbilityDesc);
       el.textContent = abilityText(id, 'description', locale);
     }
   }
   ```

## Limitations & Known Issues

1. **Requires extracted game data**: Script cannot run without text_repository files
2. **Title matching not yet implemented**: Only descriptions are matched currently
3. **Complex text formatting**: Some abilities have dynamic tokens (`{0}`, `{1}`) that need special handling
4. **Version dependencies**: Game updates may change text IDs

## Maintenance

### When to Re-run

- After game updates (text IDs may change)
- When adding new curated abilities
- When updating tc-localization mod
- After manual text corrections

### Validating Output

Check for:
- All curated abilities have matches (or are flagged for review)
- Confidence levels are appropriate (mostly exact/fuzzy, few manual)
- All expected locales are present
- Text quality (no placeholder tokens like `{0}` in final output)

## Future Enhancements

- [ ] Add title matching (separate from description)
- [ ] Interactive mode for manual review
- [ ] Token resolution for dynamic text
- [ ] Diff mode to compare with previous output
- [ ] Integration with ability-editor page
- [ ] Auto-update ability-overrides.source.json with textIds

## Related Files

- `scripts/generate-ability-ui.ts` - Generates ability UI data
- `src/data/ability-overrides.source.json` - Source of truth for curated abilities
- `src/lib/unit-abilities.ts` - Generated ability database
- `src/pages/command-abilities.astro` - Reference implementation for command ability i18n
- `docs/game-mechanics.md` - Game data extraction documentation
