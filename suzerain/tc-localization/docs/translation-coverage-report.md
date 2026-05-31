# Suzerain zh-TW coverage report (checkpoint line)

Date: 2026-05-31
Branch: `suzerain-checkpoint-2efaf1c`
Checkpoint commit: `8ec8b13`

## Scope summary

This report covers:

1. Core entity-text database translation project (`translation/`)
2. Safe scene UI text project (`scene-tmp-translation/`) that translates only `TextMeshProUGUI.m_text`
3. Explicitly excluded key-like fields (see `docs/key-protection-log.md`)

## What has been translated

### 1) Core game text (entity database)

Source: `translation/`

- Total units: **18,373**
- Pending: **0**
- Translated: **18,373**

Runtime patch notes:
- Database `*DataJson` text fields are translated
- Key-risk fields are excluded:
  - `StoryPackDataJson`
  - `AppBundleDataJson`

### 2) Scene UI visible text (safe subset)

Source: `scene-tmp-translation/`

- Extracted unique TMP strings: **602**
- Seeded from existing corpus: **41**
- Newly machine-translated this pass: **561**
- Final status: **602 / 602 translated**, pending **0**

Repack/deploy result:
- Scene bundles patched: **3**
  - `mainmenu`
  - `rizia`
  - `sordland`
- Runtime `TextMeshProUGUI.m_text` updates applied: **1812**

## What has NOT been translated (intentional)

### A) Scene localization key field

- Component: `StaticUIText`
- Field: `locaId`
- Unique key/value strings observed: **261**
- Status: **intentionally untranslated** (protected key field)

Reason:
- `locaId` is used as a lookup key; translating it can break runtime linkage and loading.

### B) Runtime identity/linkage DataJson fields

- `StoryPackDataJson`
- `AppBundleDataJson`

Status: **intentionally untranslated**.

Reason:
- These fields can affect story-pack/app-bundle identity resolution during load.

### C) Natural unchanged outputs in translated set

In `scene-tmp-translation`, **132** translated outputs remain equal to source text.

This is expected for values such as:
- proper names
- numbers/symbols/tokens
- markup-heavy strings
- short labels where target may intentionally match source

## Current deployment checkpoint

Deployed on this branch line:
- Patched entity-text bundle from checkpoint pipeline
- Patched scene bundles (TMP text only)

## Recommended next steps (reference plan)

1. **Validation loop (required):**
   - Launch game
   - Main menu
   - Load game
   - Open Codex / Journal / Reports
   - Verify no crash + text correctness

2. **If stable and you want wider UI localization:**
   - Build a curated whitelist for `locaId` values that are display-only and proven non-key
   - Translate in small batches (e.g., 20–50 keys)
   - Test load after each batch

3. **Quality pass:**
   - Review awkward machine translations in `scene-tmp-translation/state.jsonl`
   - Promote high-confidence manual edits via `manual` field

4. **Release hardening:**
   - Keep backups for all changed bundles
   - Tag a release commit once crash-free behavior is confirmed after load-game tests
