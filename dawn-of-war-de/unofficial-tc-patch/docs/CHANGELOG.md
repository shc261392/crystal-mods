# Changelog

All notable user-facing changes to the DoW DE Traditional Chinese patch are documented here.

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
