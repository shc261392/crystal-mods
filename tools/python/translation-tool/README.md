# translation-tool

Glossary-aware translation pipeline for the Crystal Mods localisation work
(Suzerain TC, Black Book TC, future). Backends: Gemini, Google Translate
(unofficial endpoint), manual passthrough.

## Install

It's part of the repo's uv workspace. From the repo root:

```sh
uv sync --all-packages
```

The `tl` command is installed into the workspace venv.

## Quick start

```sh
# 1. Create a project from a source file (jsonl/json/csv/tsv).
#    Source units look like {"id": "...", "text": "..."} per line.
uv run tl init my-project --source extracted-strings.jsonl \
    --src-lang en --tgt-lang zh-TW --backend gemini

# 2. (Optional) Edit my-project/glossary.tsv. Format: src<TAB>tgt per line.

# 3. Translate pending units.
export GEMINI_API_KEY=...
uv run tl translate my-project --limit 50

# 4. Review interactively (a=accept, e=edit, s=skip, q=quit).
uv run tl review my-project --status translated

# 5. Export.
uv run tl export my-project --out ../mod/payload/zh-TW.json --format json
```

## Project layout

```
my-project/
├── project.json     # config: src/tgt lang, backend, model
├── source.jsonl     # input units (immutable after init)
├── glossary.tsv     # hand-curated rules, longest-match protected as ⟦G\d+⟧
└── state.jsonl      # per-unit: machine TL, manual edit, status
```

State machine: `pending → translated → reviewed → final`. `tl translate`
moves `pending → translated`; `tl review` moves `translated → reviewed`
(on edit) or `→ final` (on accept).

## Backends

- `manual` — passthrough; user fills in via `tl review`.
- `google` — unofficial `translate.googleapis.com` endpoint, no key. May
  be blocked or rate-limited.
- `gemini` — REST, reads `GEMINI_API_KEY`. Default model
  `gemini-3.1-flash-lite`, override with `--model`.

## Export formats

- `jsonl` — `{"id", "source", "target"}` per line.
- `json` — single object, `{id: target}`.
- `autotranslator` — XUnity AutoTranslator `source=target` lines, with
  `\r` / `\n` / `=` escaping.
