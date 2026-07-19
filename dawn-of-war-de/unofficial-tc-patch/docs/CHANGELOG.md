# Changelog

All notable user-facing changes to the DoW DE Traditional Chinese patch are documented here.

## 2026-07-18 — v1.0.7 Subtitle gibberish fix

### Fixed
- **Dialogue subtitle gibberish eliminated** — automated font reference correction in build process prevents Unicode U+0000 glyph artifact
- `gillsans_11b.fnt` (dialogue subtitle font) now references `NotoSansTC-Medium.ttf` instead of Bold variant
- Build script now automatically fixes font references after vanilla SGA extraction

### Technical
- Added post-extraction font reference fix in `build_sga.sh`
- Prevents rendering of visible null terminator glyph (緝, U+7DC9) from Bold font
- Fix is automated and repeatable — no manual intervention needed

## 2026-07-18 — v1.0.6 Tofu fix + font adjustment system

### Fixed
- **Tofu box regression eliminated** — restored correct Chinese locale SGA source (`Engine/Locale/Chinese/EnginLoc.sga`) as the canonical base for all builds. Previous versions accidentally used English locale sources which caused campaign text rendering failures.

### Added
- **Font size adjustment system** — new `adjust_font_sizes.py` script allows configurable font sizing:
  - Adjusts all size fields (`sizeDefault`, `size640`-`size1600`) in `.fnt` files
  - Build command: `make build FONT_SIZE_INCREASE=6` (adjusts font sizes +6 points)
  - Default behavior: no adjustment (preserves vanilla Chinese locale font sizes)
- **Unified build system** — `make build` now runs the complete pipeline:
  1. Font size adjustment (optional via `FONT_SIZE_INCREASE` parameter)
  2. TC corrections application
  3. SGA rebuild via `build_sga.sh`
  4. Distribution package creation
- **Quality gates** — `make lint` runs Ruff linting on all Python scripts
- **Font structure documentation** — new `docs/FONT_STRUCTURE.md` documents font metrics and adjustment behavior

### Changed
- **Script consolidation** — `rebuild_sga_auto.sh` renamed to `build_sga.sh` for clarity
- **Project cleanup** — removed 18 outdated files (old bisection tools, deprecated scripts, stale documentation)

### Release
- Version: `1.0.6`
- Distribution: `dist/wh40k-dow-de-tc-mod-v1.0.6.zip` (184MB SGA → 122MB ZIP)
- Source SGA: `Engine/Locale/Chinese/EnginLoc.sga` (vanilla Chinese locale, 192MB)

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
