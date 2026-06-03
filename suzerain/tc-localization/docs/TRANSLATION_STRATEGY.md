# Suzerain TC Localization Strategy

## Summary
- **Menu**: locaId fully mapped + selected TMP ✓ stable
- **Campaign**: Loading stable with entity + mainmenu/rizia (no full Sordland TMP)
- **Remaining**: Entity names (mostly proper names left intentionally), Sordland TMP (selective)

## Deployed Bundles (Current Stable)
- Entity: zh-TW translation + name overrides
- MainMenu scene: full locaId + safe TMP subset
- Rizia scene: full locaId (no TMP applied yet, safe to add)
- Sordland scene: full locaId only (TMP is crash risk)

## Crash Pattern Observed
- **Full Sordland TMP deployment → campaign freeze/crash**
- Root cause: likely TMP text overrides affecting game logic strings

## Next Safe Steps
1. Add Sordland TMP only for **menu-facing UI labels** (not campaign logic)
2. Batch by risk: names/credits → UI prompts → dialogue
3. Test each batch (max 50-100 strings per batch)
4. Entity bundle: already safe, no further changes needed

## Audit Stats (Post-locaId deploy)
- Scene locaId English unique: 2 (safe to ignore, proper names)
- Scene TMP English unique: 54 (52 in Sordland)
- Entity English unique: 41,582 (mostly proper names, intentional)

## Files
- `docs/runtime-untranslated-scene.tsv` - detailed scene analysis
- `docs/runtime-untranslated-entity.tsv` - detailed entity analysis
- Scripts: `audit_untranslated_runtime.py`, `repack_scene_locaid_whitelist.py`, `repack_entitytext.py`
