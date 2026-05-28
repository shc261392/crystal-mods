# `pcgw-fetch` — PCGamingWiki metadata fetcher

Fetches game metadata from [PCGamingWiki](https://www.pcgamingwiki.com/) via the
MediaWiki + Cargo API and writes a normalized `metadata.jsonc` to a target
`<game>/` folder.

## Why

`<game>/metadata.jsonc` is the single source of truth for engine, graphics
API, store IDs, OS support, and modding metadata across this monorepo.
Fetching keeps it consistent and refreshable.

## Install (uv workspace)

From repo root:

```bash
uv sync                    # installs all workspace members
uv run pcgw-fetch --help   # entry point
```

## Usage

```bash
# Fetch by Steam App ID, write to dawn-of-war-de/metadata.jsonc
uv run pcgw-fetch --steam-appid 3556750 --out dawn-of-war-de/metadata.jsonc

# Fetch by exact PCGW page name
uv run pcgw-fetch --page "Warhammer 40,000: Dawn of War – Definitive Edition" \
                  --out dawn-of-war-de/metadata.jsonc

# Fuzzy search by name (uses opensearch first, then resolves)
uv run pcgw-fetch --search "Elden Ring" --out elden-ring/metadata.jsonc

# Refresh: re-fetch but preserve any field marked "_manual": true
uv run pcgw-fetch --refresh dawn-of-war-de/metadata.jsonc
```

## Rate-limit etiquette

PCGW limits to **30 req/min** and requires a descriptive User-Agent. This tool
sets:

```
crystal-mods/pcgw-fetch/<version> (+https://github.com/shc261392/crystal-mods)
```

A throttling client enforces ≤ 20 req/min by default to leave headroom.

## Output schema

See [`docs/conventions.md`](../../../docs/conventions.md#gamemetadatajsonc-schema).
