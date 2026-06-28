# Changelog

All notable user-facing changes to the DoW DE Traditional Chinese patch are documented here.

## 2026-06-27 — Upstream game-update sync (Engine.ucs rebase)

### Changed
- Rebased TC `Engine.ucs` onto the latest upstream game file after the June 2026 update.
- Preserved existing TC localization edits while integrating upstream changes.

### Merge conflict context
- 3-way merge inputs:
  - old upstream: `.copilot_workspace/update-20260627/raw/old/Engine.ucs`
  - new upstream: `.copilot_workspace/update-20260627/raw/new/Engine.ucs`
  - current mod UCS: `dist/wh40k-dow-de-tc-mod-v1.0.4/Engine/Locale/Chinese/Engine.ucs`
- Conflict count: 2 keys (`11270884`, `11270885`), both in credits rows.
- Resolution policy: keep upstream factual credits updates when mod delta is formatting-only.

### Verified
- Upstream `EnginLoc.sga` remained byte-identical vs prior baseline (no archive payload delta).
- `scripts/apply_tc_corrections.py --ucs Engine.ucs --dry-run` returns no-op after rebase.

### Rebuild (2026-06-28)
- Rebuilt `v1.0.5` release artifact after investigating oversized menu/UI text.
- Root cause: packaged `.fnt` files had flattened `size640..size1600 = 32` (all-size profile), which over-scales many low-resolution UI bindings.
- Fix in rebuilt `v1.0.5`: restored vanilla `size640..size1600` per font and kept only `sizeDefault = 34` (fallback-only profile).
- Verification: only 13 `sizeDefault` deltas remain vs vanilla; no `size640..size1600` inflation deltas remain.

### Font profile update
- Increased the default recommended profile slightly: `sizeDefault` is now `36` for the standard mod package.
- Added a Vortex FOMOD profile bundle with three install-time choices:
  - **Vanilla size**
  - **Recommended for 1920×1080 or above** (`sizeDefault = 36`)
  - **Recommended for 4K or above** (`sizeDefault = 38`)

### Release
- Version bumped to `1.0.5`.
- Package artifact target: `dist/wh40k-dow-de-tc-mod-v1.0.5.zip`.

## 2026-06-09 — Campaign readability + tofu stability update

### Fixed
- Dark Crusade / Soulstorm campaign text tofu regressions were eliminated in the validated release composition.
- Packaging flow no longer relies on internal milestone terminology for normal release commands.

### Improved
- Restored larger, readable Traditional Chinese font sizing (original mod goal) while preserving tofu-safe campaign rendering.
- Standard release packaging command is now user-facing and explicit:
  - `make package-release`

### Build/Release flow
- `make package-release` now performs the full standard release packaging flow:
  1. Sync validated release SGA into `EnginLocMod.sga`
  2. Build distributable mod zip in `dist/`

### Notes
- `make package-rc20` is kept only as a backward-compatible alias and is considered deprecated.
