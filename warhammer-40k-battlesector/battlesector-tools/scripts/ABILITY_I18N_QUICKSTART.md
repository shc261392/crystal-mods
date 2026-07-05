# Ability i18n Integration Quick Start

## Prerequisites

The integration script requires game localization data. You have two options:

### Option 1: Full Integration (All Locales)

Extract game data to access all supported languages:

1. **Extract game assets** using AssetRipper or similar:
   ```
   Game Installation → AssetRipper → Export to folder
   ```

2. **Locate text_repository files**:
   ```
   ExportedProject/Assets/Resources/text_repository-*.txt
   ```

3. **Copy to workspace**:
   ```bash
   mkdir -p .copilot_workspace/battlesector-data/extracted_text_assets
   cp <game-export>/Assets/Resources/text_repository-*.txt \
      .copilot_workspace/battlesector-data/extracted_text_assets/
   ```

4. **Run integration**:
   ```bash
   pnpm run i18n:integrate-abilities:dry  # Preview
   pnpm run i18n:integrate-abilities      # Generate
   ```

### Option 2: TC-Only Integration (Traditional Chinese)

If you only need Traditional Chinese support and have the tc-localization mod:

1. **Verify tc-localization mod is available**:
   ```bash
   ls ../tc-localization/translation/zh-TW/source/zh-TW/
   ```

2. **The script automatically uses TC data** if available

3. **Run integration** (will use English from source + TC translations):
   ```bash
   pnpm run i18n:integrate-abilities:dry
   ```

## Current Status

Based on your last run:
- ✅ Ability source loaded (62 abilities)
- ❌ Game extraction data not found
- ⚠️ Cannot perform full localization without extracted text

## Next Steps

Choose your path:

**A. Want all language support?**
→ Follow Option 1 above to extract game data

**B. Want Traditional Chinese only?**
→ Check if `../tc-localization/` has the data (run dry-run to verify)

**C. Don't need localization yet?**
→ Skip this script - abilities will use English fallback from source

## Understanding the Output

When the script succeeds, you'll see:

```
Step 3: Matching abilities to localization entries...
  [1] Jump Pack: ✅ textId=12345, score=1.000, 10 locales
  [2] Tactical Precision: ✅ textId=12346, score=1.000, 10 locales
  ...
```

Legend:
- ✅ = Exact match (100% confidence)
- ⚠️ = Fuzzy match (≥95%, review recommended)
- ❓ = Manual review needed (<95%)
- ❌ = No match found

## Troubleshooting

### "Extracted text assets not found"

**Cause**: Game data hasn't been extracted to `.copilot_workspace/battlesector-data/`

**Solutions**:
1. Extract game assets (see Option 1 above)
2. Or: Use TC-only mode if available
3. Or: Skip localization for now

### "No English text map available"

**Cause**: English text_repository files are missing or empty

**Solution**: Verify extraction included:
- `text_repository-units.txt`
- `text_repository-default.txt`
- etc. (8 base files, no suffix for English)

### "Warning: Failed to parse <file>"

**Cause**: Text repository file format is unexpected

**Solution**:
- Check file format (should be: `<id> <text>` per line)
- Verify UTF-8 encoding
- Check for corruption

## FAQ

**Q: Do I need to re-run after every game update?**
A: Only if text IDs change or new abilities are added to the game.

**Q: Can I add manual translations?**
A: Yes! Add them directly to `ability-overrides.source.json` or edit the generated `ability-i18n.json`.

**Q: What if the script doesn't find matches?**
A: Check `.copilot_workspace/ability-i18n-review.json` for suggestions, or add manual translations.

**Q: How do I integrate the output into the app?**
A: See the "Integrating into Application" section in `ABILITY_I18N_README.md`.

## Support

For more details, see:
- `scripts/ABILITY_I18N_README.md` - Full documentation
- `docs/game-mechanics.md` - Game data extraction process
- `src/pages/command-abilities.astro` - Reference i18n implementation
