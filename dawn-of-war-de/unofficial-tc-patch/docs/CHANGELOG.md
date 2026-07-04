# Changelog

All notable user-facing changes to the DoW DE Traditional Chinese patch are documented here.

## 2026-07-04 — Architecture cleanup (loose data deployment removed)

### BREAKING CHANGES
- **Removed all loose data deployment code** (obsolete since v1.0.4)
- Deploy scripts now only support SGA-only deployment
- Removed `--mode` flags and `DEPLOY_MODE` variable from deploy.sh/deploy.ps1
- Simplified uninstall scripts to remove only SGA files (no more data/ directory handling)

### Documentation Updates
- Updated README.md manual install instructions (no longer requires EnginLoc.sga renaming)
- Clarified FONT_FIX_README.md is for development use only
- Updated Makefile to remove loose-mode deployment targets

### Rationale
- v1.0.4 established SGA-only deployment as the canonical method
- Loose data deployment was a legacy workflow from early development
- Removing obsolete code paths prevents future confusion and maintenance burden

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

### Font size adjustment (2026-07-04)
- Increased `sizeDefault` from 34 to 36 for improved readability.
- All `.fnt` files confirmed using NotoSansTC font family (notosanstc-*.ttf).
- **Font size variants:**
  - `wh40k-dow-de-tc-mod-v1.0.5.zip` — standard variant (sizeDefault=36)
  - `wh40k-dow-de-tc-mod-v1.0.5-font48.zip` — large font variant (sizeDefault=48) for users who need extra-large text

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
