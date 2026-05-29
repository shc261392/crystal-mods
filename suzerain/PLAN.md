# Mod plan: Suzerain

> Status: **draft** (post-discovery, pre-implementation).
> Discovery report: [`DISCOVERY.md`](DISCOVERY.md).

## Game profile

- **Engine:** Unity `6000.0.58f2` (Unity 6), scripting backend **IL2CPP**.
- **Install size:** 1.3 GB / 161 files.
- **Steam AppID:** `1207650`.
- **Asset system:** Unity Addressables, bundled in
  `Suzerain_Data/StreamingAssets/aa/StandaloneWindows64/<hashed-name>.bundle`.

## Key findings from discovery

- IL2CPP — there is **no `Managed/*.dll`** to patch in C#. Code mods require
  BepInEx-IL2CPP (uses Il2CppInterop), which is a heavier lift.
- **All translatable text lives in a single bundle:**
  `defaultlocalgroup_assets_assets_database_entitytextassets.asset_…bundle`
  (4.5 MB). Extracted via `scripts/extract_entitytext.py`:
  - 79 `TextAsset` objects, each wrapping a JSON `items[]` array.
  - **18,373 translatable strings, ~667K words.**
  - Storypack bundles (`storypack_sordland`, `storypack_rizia`) contain
    only 3D map assets (meshes/materials/textures) — no text.
  - The `…_storypacks_*` bundle holds only sprite icons.
- Total addressable scene + content payload is on the order of ~700 MB; the
  rest is audio (`.bundle` per OGG track).

## Goal

User intent: *"create a translation tool as utility of the project mod
tools, extract text and use the translation tool to generate TC and create
TC localization mod."* The translation tool itself is its own project
(glossary + manual edit + Google Translate + Gemini Flash backends).

Concrete Suzerain deliverable: a Traditional Chinese (zh-TW) localisation
mod that replaces the English entity-text database with translated entries.

## Implementation phases

### Phase 0 — translation tool (separate workstream, prerequisite)

Outlined in `tools/python/translation-tool/` (not yet created). Required
features:

- Glossary load/save (TSV or JSON), term-aware substitution.
- Manual edit UI (CLI first, optional TUI later).
- Backends: Google Translate (free unofficial endpoint or official API), Gemini Flash via REST.
- Resumable: source unit → glossary apply → backend → review → final state.

### Phase 1 — text extraction ✅ DONE

1. ✅ `scripts/extract_entitytext.py` (UnityPy, PEP 723) dumps every
   object's typetree and, for `TextAsset`, JSON-parses `m_Script` and
   harvests user-facing string fields into `raw_strings.jsonl`.
2. ✅ Schema confirmed: 79 TextAssets, each with `items[].{Title,
   Description, Notes, ...}`. ID format: `<object_index:05d>::<path>`.
3. ✅ Storypack bundles checked — no text content; nothing to extract.
4. ✅ `scripts/build_tl_source.py` converts `raw_strings.jsonl` into the
   `tl` project `source.jsonl` format.

### Phase 2 — translation 🟡 IN PROGRESS

1. ✅ Pilot project initialised at `tc-localization/translation/` (18,373
   units, glossary seeded with country/party/office names).
2. ✅ End-to-end pipeline validated with Google backend (20 sample units;
   free endpoint rate-limits hard at ~50/run).
3. ⏳ Production translation pass with Gemini Flash Lite
   (`GEMINI_API_KEY` required). Cost estimate: ~$2–5 USD for the full corpus.
4. ⏳ Review pass via `tl review` (or external editor on `state.jsonl`).
5. ⏳ Expand glossary as recurring terms emerge from review.

### Phase 3 — repack

Two options:

- **A: Bundle replacement.** Repack the modified `EntityTextAssets`
  ScriptableObject back into the bundle file via UnityPy. Ship the modified
  bundle; deploy script swaps it into the Addressables folder. Risk:
  Addressables uses a content-hashed catalogue; a hash mismatch could fail
  to load. Need to either rebuild the `.json`/`.hash` catalogue or use a
  catalogue override.
- **B: Runtime BepInEx-IL2CPP mod.** A small mod that intercepts the
  language resolution call and substitutes our translated strings from a
  separate `Translations/zh-TW.json` resource. Higher engineering, but
  decouples us from the addressables hash dance and from Steam updates.

Recommendation: prototype Option A first because it has zero runtime
dependency; fall back to B if hash regeneration proves intractable.

## Files we will produce (eventually)

```
suzerain/
├── modinfo.json
├── README.md
├── deploy.sh / deploy.ps1
├── uninstall.sh / uninstall.ps1
├── payload/
│   └── Suzerain_Data/StreamingAssets/aa/StandaloneWindows64/<patched>.bundle
└── scripts/
    ├── extract_strings.py           # bundle -> CSV/JSON via UnityPy
    ├── build_translated_bundle.py   # apply zh-TW dict -> repack bundle
    └── translations/zh-TW/          # checked-in TC source of truth
```

## Open questions (need user input before implementation)

1. Should we ship the BepInEx-IL2CPP runtime mod (option B) as the primary
   delivery, or only as fallback?
2. Glossary scope: does the user want me to start one from political/
   Eastern-European-fiction terms, or wait for the translation tool design?
3. Are we OK requiring the user to install BepInEx-IL2CPP separately, or
   bundle?

## Blockers

- For production TL: `GEMINI_API_KEY` must be set in the environment.
- For Phase 3: need to research how Suzerain's Addressables catalogue
  validates bundle hashes before committing to bundle-replacement vs
  runtime-redirect.
