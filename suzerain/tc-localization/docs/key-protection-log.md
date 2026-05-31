# Suzerain TC localization — key protection log

Date: 2026-05-31
Branch: `suzerain-checkpoint-2efaf1c`

## Critical rule

Do **not** translate string fields that behave as runtime keys / linkage identifiers.

## Protected fields and components

### Entity text bundle (`defaultlocalgroup_assets_assets_database_entitytextassets...bundle`)

- Protected DataJson fields (NOT translated):
  - `StoryPackDataJson`
  - `AppBundleDataJson`
- Rationale:
  - These fields participate in story-pack / app-bundle identity linkage.
  - Translating values here can make `CurrentStoryPackData` null during load.

### Scene bundles (`scenes_scenes_assets_scenes_{mainmenu,rizia,sordland}...bundle`)

- Protected component field (NOT translated):
  - `StaticUIText.locaId`
- Rationale:
  - `locaId` is a lookup key, not display text.
  - Mutating keys can break localization resolution and scene/game load flow.

### Allowed scene field

- `TextMeshProUGUI.m_text` (translated)
- Rationale:
  - Visible render text field; safe to localize directly.

## Crash-safety scene policy (discovered by binary isolation)

- `mainmenu` scene patch: safe
- `rizia` scene patch: safe
- `sordland` scene patch: **unsafe in current build line** (causes load-game crash)

Default policy now:
- Patch only `mainmenu` + `rizia` scene bundles.
- Keep `sordland` scene bundle original until a stricter whitelist strategy is added.

## Policy for future translation changes

1. Translate only presentation fields (`Title`, `Description`, `Text`, `Subtitle`, TMP `m_text`).
2. Never translate IDs/keys/table names/reference strings.
3. If uncertain, add field/component to this log first, then ship after test.
