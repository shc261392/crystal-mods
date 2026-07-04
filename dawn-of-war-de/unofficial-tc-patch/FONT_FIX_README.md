# Dawn of War DE Chinese Locale Font-Fix Scripts (Development Only)

> **⚠️ IMPORTANT: These scripts are for DEVELOPMENT use only.**  
> **End users should install the pre-built SGA package from Releases.**  
> **Loose data deployment is obsolete (removed in v1.0.4).**

These scripts help developers modify font sizes during SGA archive development:

1. Unpack `EnginLoc.sga` (or `EngineLoc.sga`) for editing
2. Patch `.fnt` font-size keys with different profiles
3. Repack to a new `.sga` for testing

## Usage Context

This workflow is **ONLY** for developers building the mod from source.  
The final package ships pre-built `EnginLocMod.sga` with tested font sizes.

If you're an end user installing the mod, use the releases from:
- GitHub Releases: pre-packaged `.zip` files
- Vortex Mod Manager: automated installation

## Files

- `setup_relic_tool.ps1` — Creates a local venv and installs `relic-tool-sga` + `relic-tool-sga-v2`
- `unpack_chinese_locale.ps1` — Backs up and unpacks the locale `.sga`
- `apply_font_fix.py` — Patches `.fnt` fields in extracted font files
- `repack_chinese_locale.ps1` — Packs manifest back into a new `.sga`

## Development Workflow

Run in PowerShell from `Engine\Locale\Chinese`:

1) Setup tooling:
   ```powershell
   ./setup_relic_tool.ps1
   ```

2) Unpack archive:
   ```powershell
   ./unpack_chinese_locale.ps1
   ```

3) Preview font edits:
   ```powershell
   ./.venv-relic/Scripts/python.exe ./apply_font_fix.py --dry-run --restore-from-bak --mode fallback-only --size 36
   ```

4) Apply font edits:
   ```powershell
   ./.venv-relic/Scripts/python.exe ./apply_font_fix.py --restore-from-bak --mode fallback-only --size 36
   ```

5) Repack into SGA:
   ```powershell
   ./repack_chinese_locale.ps1
   ```

## Font Size Modes

- `fallback-only` — changes only `sizeDefault` (recommended, less clipping)
- `all` — changes all `size*` keys (stronger scaling, may cause UI clipping)

## Notes

- Every changed `.fnt` gets a `.bak` backup next to it.
- Unpack script also writes `.sga` backup into `backup\`.
- If a `.fnt` file has an unknown syntax, it is skipped and reported.
- `fallback-only` mode is safer for mixed-resolution UI.
- If text clips, try smaller values like `--size 32` or `--size 30`.
