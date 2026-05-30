# Suzerain — Traditional Chinese (zh-TW) Localisation

> **Status:** machine-translation complete; repack pipeline ready for in-game testing.

Community Traditional Chinese localisation for [Suzerain](https://store.steampowered.com/app/1207650/).

## Pipeline

```
EntityTextAssets bundle + scene UI bundles  (Unity 6 Addressables, IL2CPP)
  │  scripts/extract_entitytext.py / extract_scene_ui.py   (UnityPy)   →  make extract
        ▼
extracted/raw_strings.jsonl  →  translation/source.jsonl   (18,373 units)
scene UI strings            →  scene-ui-translation/source.jsonl   (620 units)
        │  tl glossary build  (corpus-driven term discovery) →  make glossary
  │  tl translate       (batched Gemini)               →  make translate
        ▼
translation/state.jsonl + scene-ui-translation/state.jsonl
  │  scripts/repack_entitytext.py + repack_scene_ui.py   (UnityPy)   →  make build
        ▼
build/<patched>.bundle + build/scenes_scenes_assets_scenes_*.bundle
  │  deploy.sh / deploy.ps1   (backs up originals first)
        ▼
Game install  (uninstall.sh / uninstall.ps1 restores the backup)
```

See [../PLAN.md](../PLAN.md) for the higher-level design and trade-offs.

## Quick start (dev, from this directory)

```sh
make help          # list targets
make extract       # bundle → source.jsonl  (re-run only if the game updates)
make glossary      # discover + translate recurring terms (needs GEMINI_API_KEY)
make translate     # full Gemini zh-TW pass for entity text + scene UI (needs GEMINI_API_KEY)
make status        # show counts
make build         # repack database + scene UI translations → build/*.bundle
make deploy        # build + install into the game (Linux/WSL2)
make uninstall     # restore the latest backup
```

`GEMINI_API_KEY` is read from the repo-root `.env` (gitignored).

## Scripts

- `scripts/extract_entitytext.py` — dump every object in the
  `entitytextassets*.bundle` to JSON and harvest user-facing strings into
  `raw_strings.jsonl`. Self-bootstraps via PEP 723 (`uv run --script`).
- `scripts/build_tl_source.py` — convert `raw_strings.jsonl` into the
  `tl` project `source.jsonl` (ID = `<object_index:05d>::<path>`).
- `scripts/repack_entitytext.py` — apply translated narrative/database strings
  back into a copy of the runtime `Entity Text Assets` bundle.
- `scripts/extract_scene_ui.py` — harvest unique scene UI strings from
  `StaticUIText.locaId` and `TextMeshProUGUI.m_text` across the shipped scenes.
- `scripts/repack_scene_ui.py` — rewrite translated scene UI strings back into
  the main menu / Sordland / Rizia scene bundles.

## Glossary

`translation/glossary.tsv` has two sections:

- **Manual** entries at the top take precedence and are never overwritten.
- An auto-generated block (delimited by markers) produced by
  `tl glossary build`, which detects recurring proper nouns / named entities
  from the corpus and translates them once with consistency anchoring (so
  *Sordland → 蘇德蘭*, *Sordish → 蘇德蘭人*, *Rizian → 里齊亞人* stay aligned).

Re-run `make glossary` after the game adds content; use
`tl glossary build … --rebuild` to re-translate the whole auto block.

## Deploy / uninstall

Both deploy scripts:

1. Auto-detect the Steam install (or accept `--game-dir` / `-GameDir`).
2. Back up the original bundle to `backup/<stamp>/` (with an `origin.txt`).
3. Copy the patched bundle into the Addressables folder.

`uninstall` restores the most recent backup (or `--backup <stamp>`).

> **Note on Addressables CRC:** Suzerain (Unity 6) uses a binary catalogue
> (`catalog.bin`). Local bundles generally load without CRC verification, but
> if patched text reverts to English or renders blank in-game, the catalogue
> may be enforcing a hash — run `uninstall` and report it so we can switch to
> the BepInEx-IL2CPP runtime-redirect approach (Option B in the PLAN).

## Run extraction manually

```sh
uv run --script suzerain/tc-localization/scripts/extract_entitytext.py \
    "<steam>/Suzerain_Data/StreamingAssets/aa/StandaloneWindows64/defaultlocalgroup_assets_assets_database_entitytextassets.asset_7658ed792f0c4924d06b11829a6c36d1.bundle" \
    --out suzerain/tc-localization/extracted
```
