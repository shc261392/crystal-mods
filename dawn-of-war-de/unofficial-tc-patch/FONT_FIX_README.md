# Dawn of War DE Chinese Locale Font-Fix Scripts

These scripts automate the workflow in this folder:

1. Unpack `EnginLoc.sga` (or `EngineLoc.sga`) into `data/`
2. Patch `.fnt` font-size keys with either:
	- anti-clipping fallback profile (`fallback-only`), or
	- stronger visible scaling (`all`)
3. Optionally repack to a new `.sga`

> You are already in the target folder:
> `...\Engine\Locale\Chinese`

## Files

- `setup_relic_tool.ps1` — Creates a local venv and installs `relic-tool-sga` + `relic-tool-sga-v2`
- `unpack_chinese_locale.ps1` — Backs up and unpacks the locale `.sga`
- `apply_font_fix.py` — Patches `.fnt` fields in `data/font/*.fnt` (or `font/*.fnt`)
- `repack_chinese_locale.ps1` — Packs manifest back into a new `.sga`

## Typical workflow

Run in PowerShell from this folder:

1) Setup tooling:
- `./setup_relic_tool.ps1`

2) Unpack archive:
- `./unpack_chinese_locale.ps1`

3) Preview font edits:
- `./.venv-relic/Scripts/python.exe ./apply_font_fix.py --dry-run --restore-from-bak --mode fallback-only --size 34`

4) Apply font edits:
- `./.venv-relic/Scripts/python.exe ./apply_font_fix.py --restore-from-bak --mode fallback-only --size 34`

### Stronger visible size profile (if fallback-only still looks too small)

- `./.venv-relic/Scripts/python.exe ./apply_font_fix.py --restore-from-bak --mode all --size 32`

### Replace Chinese font with Microsoft YaHei

1) Copy YaHei fonts into locale font folder:
- `Copy-Item 'C:\Windows\Fonts\msyh.ttc' '.\data\font\msyh.ttc' -Force`
- `Copy-Item 'C:\Windows\Fonts\msyhbd.ttc' '.\data\font\msyhbd.ttc' -Force`

2) Apply size + font replacement (keeps English file mapping unless matched):
- `./.venv-relic/Scripts/python.exe ./apply_font_fix.py --restore-from-bak --mode all --size 32 --replace-font-file msyh.ttc --replace-font-match 'NotoSansTC|Gulim'`

5) (Optional) Repack into a new archive:
- `./repack_chinese_locale.ps1`

## No-repack method (recommended for quick test)

Like your reference mod says, the game can load unpacked folder content directly:

- Keep backup of original `.sga`
- Remove or rename original `.sga`
- Ensure `data\font\*.fnt` exists in this language folder

## Notes

- Every changed `.fnt` gets a `.bak` backup next to it.
- Unpack script also writes `.sga` backup into `backup\`.
- If a `.fnt` file has an unknown syntax, it is skipped and reported.
- `fallback-only` mode changes only `sizeDefault` (best for 4K fallback and less clipping).
- `all` mode changes all `size*` keys and can cause clipping if size is too high.
- If text still clips, try: `--size 30` or `--size 32`.
- `--replace-font-file` lets you swap the `file = "..."` entries in `.fnt` files (for example `msyh.ttc`).
