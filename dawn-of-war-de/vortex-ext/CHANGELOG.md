# Changelog — Vortex Extension for Dawn of War: Definitive Edition

All notable changes to this extension will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.4] - 2026-06-18

### Fixed
- **Single-file archives** no longer treated as wrapper folders (added `hasNestedContent` guard)
- **Case-sensitive path matching** now handles lowercase mod paths correctly (`engine/locale/` matches `Engine`)
- **Directory permissions check** now validates entire game root instead of only `Engine/Locale`

### Changed
- Refactored `installModContent()` to use native `path.posix.relative()` instead of manual string manipulation
- Improved code readability with clearer variable names (`hasSingleWrapper`, `hasNestedContent`)
- Updated documentation to accurately describe generic installer behavior
- Removed outdated claims about locale-specific detection and file exclusions
- Source code link updated to GitHub repository

### Technical
- Uses template literals for string construction
- Case-insensitive helper function for directory detection
- Simpler `prepareForModding()` implementation

---

## [1.0.3] - 2026-06-09

### Fixed
- Layout detection for wrapper folders
- File deployment logic

---

## [1.0.0] - 2026-06-01

### Added
- Initial release
- Game detection via Steam App ID 3556750
- Generic mod installer with two layout modes:
  - Layout A: Game-root-relative paths
  - Layout B: Wrapper folder stripping
- Support for all DoW:DE directories (W40k, WXP, DXP2, DXP3, Engine, etc.)

---

## Notes

**Current Version:** 1.0.4  
**Vortex Compatibility:** 1.10+  
**Repository:** [https://github.com/shc261392/crystal-mods](https://github.com/shc261392/crystal-mods)
