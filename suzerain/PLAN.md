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
- The biggest candidate for in-game text data is:
  - `defaultlocalgroup_assets_assets_database_entitytextassets.asset_7658ed792f0c4924d06b11829a6c36d1.bundle` — 4.5 MB
  - Plus story-pack bundles: `storypack_sordland_…`, `storypack_rizia_…`.
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

### Phase 1 — text extraction

1. Use [AssetRipper](https://github.com/AssetRipper/AssetRipper) or
   [UnityPy](https://github.com/K0lb3/UnityPy) on
   `entitytextassets.asset…bundle` to dump the `EntityTextAssets` ScriptableObject as JSON / CSV.
2. Identify the schema (key, language, text). Suzerain ships multi-language
   text in-game; locate the existing language enum to know what slot to fill.
3. Repeat for the `storypack_*` bundles to grab story-specific strings.

### Phase 2 — translation

1. Feed extracted strings through `translation-tool` with a curated political /
   parliamentary / Cold-War-Eastern-European-pastiche glossary.
2. Review and tag finalised entries.

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

- Translation tool does not exist yet. Cannot start Phase 2 until it does.
- Need a working sample of an extracted `EntityTextAssets` to confirm schema before committing to extraction approach.
