# Suzerain — Traditional Chinese (zh-TW) Localisation

> **Status:** draft / pre-release. Pipeline scaffolding only.

Community Traditional Chinese localisation for [Suzerain](https://store.steampowered.com/app/1207650/).

## Pipeline

```
EntityTextAssets bundle
        │  scripts/extract_entitytext.py   (UnityPy)
        ▼
extracted/<object>.json  +  raw_strings.jsonl
        │  tools/python/translation-tool  (tl init/translate/review/export)
        ▼
translated/zh-TW.jsonl
        │  scripts/repack_entitytext.py   (UnityPy, future)
        ▼
payload/Suzerain_Data/StreamingAssets/aa/StandaloneWindows64/<patched>.bundle
        │  deploy.sh / deploy.ps1
        ▼
Game install (with backup of original bundle)
```

See [../PLAN.md](../PLAN.md) for the higher-level design and trade-offs.

## Scripts

- `scripts/extract_entitytext.py` — dump every object in the
  `entitytextassets*.bundle` to JSON for schema inspection. Self-bootstraps
  via PEP 723 (`uv run --script`).
- `scripts/repack_entitytext.py` — *(planned)* apply translated strings
  back into a copy of the bundle.

## Run extraction

```sh
uv run --script suzerain/tc-localization/scripts/extract_entitytext.py \
    "<steam>/Suzerain_Data/StreamingAssets/aa/StandaloneWindows64/defaultlocalgroup_assets_assets_database_entitytextassets.asset_7658ed792f0c4924d06b11829a6c36d1.bundle" \
    --out suzerain/tc-localization/extracted
```
