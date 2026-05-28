# Mod plan: Digimon Survive

> Status: **draft** (post-discovery, pre-implementation).
> Discovery report: [`DISCOVERY.md`](DISCOVERY.md).

## Game profile

- **Engine:** Unity `2019.4.29f1`, scripting backend **Mono**.
- **Install size:** 6.6 GB / 6230 files.
- **Steam AppID:** `1295860`.
- **Asset layout:** content lives as bare-name asset bundles under
  `DigimonSurvive_Data/StreamingAssets/StandaloneWindows64/` (e.g.
  `bm12_scene`, `advroombg/prefabs/<id>/<variant>`,
  `movie/movie001_<locale>`).
- **Localisation:** zh_TW already a first-class locale (see opening movies
  `movie001_zh_tw`). No translation work needed; localisation likely
  ScriptableObject- or CSV-driven inside `resources.assets`.
- **Mono managed DLLs:** 98 — straightforward to attach BepInEx 5.

## Goals (in priority order)

User intent: *"upscale first, plan future swap character model (research
how)."*

1. **Phase 1 — Texture upscale pack.** 2x/4x upscale of the visible-art
   asset bundles — primarily `advroombg/` (Adventure Room backgrounds) and
   battle map scenes (`bm**_scene`). Optional: UI atlases inside
   `resources.assets`.
2. **Phase 2 — Character model swap framework.** Research-and-prototype.
   Allow swapping the in-battle / adventure-mode digimon models for either
   alternate canon models or community remodels.

## Phase 1 — Texture upscale

### Pipeline

1. **Extract** target bundles with [AssetRipper](https://github.com/AssetRipper/AssetRipper)
   (CLI) or [UnityPy](https://github.com/K0lb3/UnityPy) (scripted) into PNG.
2. **Upscale** with Real-ESRGAN (default model `realesrgan-x4plus`) or
   `4xUltrasharp`. Per-asset selection: photographic backgrounds vs.
   pixel-art UI use different models.
3. **Repack** modified textures back into the original bundle via UnityPy
   (preserves bundle compression + name hash). Keep the original asset
   path/CRC so the game loads the patched bundle by name.
4. **Stage** patched bundles into `payload/StreamingAssets/StandaloneWindows64/…`
   and deploy via `deploy.sh` / `deploy.ps1` that copies on top, with a
   backup of originals.

### Bundle priority list (from discovery)

Largest art bundles to target first:

- `advroombg/prefabs/<NN>/<a|b|c>` — 22–39 MB each (visible adventure-mode rooms)
- `bm05_scene` … `bm32_scene` — 24–34 MB each (battle maps)
- UI atlases hidden inside `resources.assets` (needs separate extract pass)

### Output mod shape

```
digimon-survive/upscale-pack/
├── modinfo.json
├── README.md
├── deploy.sh / deploy.ps1
├── uninstall.sh / uninstall.ps1
├── payload/
│   └── DigimonSurvive_Data/StreamingAssets/StandaloneWindows64/
│       ├── advroombg/prefabs/…
│       └── bm**_scene
└── scripts/
    ├── extract_bundles.py
    ├── upscale_textures.py   # Real-ESRGAN runner
    └── repack_bundles.py
```

### Risks

- Repacked bundle size grows; install footprint may bloat by several GB.
- Texture format mismatch can crash the game — must preserve original
  `TextureFormat` (e.g. `BC7`, `DXT5`). UnityPy handles this if the
  destination format is set correctly.
- Movies (`movie001_*`) are video, not images — out of scope for upscale
  (would need a separate ffmpeg+upscaler workflow, not planned).

## Phase 2 — Character model swap (research)

### Research questions

1. Where do digimon models live? Probably under
   `StreamingAssets/StandaloneWindows64/` with names like `chr_<id>` or
   `digi_<id>` (need extract pass to confirm — discovery skipped non-locale
   bundles).
2. Are battle and adventure-mode meshes shared or split?
3. Is there a central data table that maps `digimon_id → bundle_path`?
   That's the swap point — easier than runtime patching.
4. Does the game use Addressables or raw `AssetBundle.LoadFromFile`? (The
   bare-name files under `StandaloneWindows64/` suggest the latter, which
   makes swap-by-replacement viable.)

### Proposed approach (subject to research)

- **Static swap:** replace the bundle file with one containing an alternate
  mesh at the same internal path. No code mod required. Quickest win.
- **Runtime swap (BepInEx 5):** a Mono BepInEx plugin that hooks the
  digimon load function and redirects the request to a user-selectable
  alternate bundle. Allows multiple skins to coexist.

### Decision deferred

We commit to Phase 1 first. Phase 2 starts only after a research spike
that produces a `RESEARCH.md` documenting the actual model-loading path.

## Files we will produce now (Phase 1)

See "Output mod shape" above. Author order: extract script → upscale script
→ repack script → end-to-end run on one bundle → deploy scripts → README.

## Open questions (need user input before implementation)

1. Upscale factor: 2x or 4x? (4x triples disk footprint vs 2x.)
2. Real-ESRGAN model: stick with `realesrgan-x4plus` (default), or use a
   pixel-art model for UI? (Likely both, with per-bundle config.)
3. Distribution: Nexus only? Or also ship a partial pack (UI only / rooms
   only) for users with less disk space?
4. Is GPU available for upscaling on the dev machine? (Otherwise CPU-only
   `realesrgan-ncnn-vulkan` would take a long time on 6.6 GB.)
