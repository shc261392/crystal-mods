# Space Marine 2 — official modding toolset (usage guide)

The official Saber modding tools are installed locally at
`D:\tools\wh40k-space-marine-2-modding-tools\` (mirrored into this workspace
only as documentation — the binaries stay on disk). Source of truth for the
workflow: `ModEditor\SpaceMarine2_Modding_HowTo.pdf` (28 pp.) and
`ModEditor\Map_Converter_Guide.pdf` (10 pp.), plus the toolset folders.

## Toolset contents

```
wh40k-space-marine-2-modding-tools/
├── ModEditor/                 Game mod editor + build pipeline
│   ├── SpaceMarine2_Modding_HowTo.pdf    (read this first)
│   ├── Map_Converter_Guide.pdf
│   ├── mods_source/           Link files + extracted source (project assets)
│   ├── paks/                  Project pak list (client + server references)
│   ├── preload/               Preload export options
│   ├── prjenv/                Editor / exporter / furnace / resource-converter envs
│   └── tools/
│       ├── bin/ModEditor/     IntegrationStudio.exe (the editor GUI)
│       ├── bin/ResourceManager/  Convert.exe, GfxBundle.exe, LightProbe, ObbHier…
│       ├── bin/ResourceTools/    create_empty_resource, create_tpl_resource,
│       │                          create_scene_resource, pct_resource_gen, furnace
│       ├── bin/ModelConverter/   USF ↔ GLTF converter (drag-and-drop)
│       ├── bin/UsfExport/        USF → TPL + TGA → PCT, generates resources
│       ├── meta_descs/           SSO/CLS/PROP property descriptors
│       └── py/                   UsfExporter, furnace python helpers
├── ModelConverter/           Standalone model pipeline + tutorials
└── SteamWSModUploader/       Steam Workshop uploader (steam_appid.txt = 3856330)
```

## 1. Install the Mod Editor into the game

> ⚠️ **Backward compatibility is not guaranteed** — use the toolset that matches
> the installed game version (check the `.exe` file version). Mod files must
> match the base-game version or the game crashes.

1. Copy the **contents of `ModEditor/`** to
   `<game>\client_pc\root\` (i.e. `…\Space Marine 2\client_pc\root\`).
2. Extract source files from the base paks into `mods_source/`:
   - Client: `…\client_pc\root\paks\client\default\default_other.pak`
   - Server: `…\server_pc\root\paks\server\default\default_other.pak`
   - Replace/skip duplicates when prompted. **Do not deviate** — it can break
     resource generation.
3. Launch the editor: `…\client_pc\root\tools\ModEditor\IntegrationStudio.exe`.
   Wait for the progress bar (bottom-left) to finish loading sources.

## 2. Editor workflow (IntegrationStudio)

- **Interface**: Top menu (File / Edit / Window), Content Browser (all project
  files, searchable), File editor (Property Control panel), Problems (log).
- **Open files**: `Alt+Shift+O` to browse; `Ctrl+O` for a file via Explorer.
  Only open files inside `mods_source/` — opening external files breaks saving.
- **Edit**: CLS/PROP/SSO open in **Property Control**. Changes are shown in
  bold; the `⟳` button reverts to the parent value. `Ctrl+S` saves.
- **`.resource` files**: auto-generated on save for CLS/PROP/SSO edits. They are
  **essential** when a mod changes game assets (textures, models, sounds).
  For pure data `.sso` value changes they are not required.
- **Test in `local/`**: copy the edited file *plus its `.resource`* (if any) to
  `<game>\client_pc\root\local\<relative-path>`, keeping the hierarchy after
  `mods_source\default_other\`. Launching the game shows "MODS DETECTED" — that
  is expected.
- **Hotkeys**: `Ctrl+O` open, `Alt+Shift+O` browse, `Ctrl+N` new file, `F2`
  rename; custom keys under `Edit > Hot Keys`.

### File types

| Type | Purpose |
| --- | --- |
| `.cls` | Actor classes (an actor = game object with logic). `pc_marine_base_authority.cls` is the parent marine class. |
| `.prop` | Actor properties (geometry, sound, damage, jetpack…). |
| `.sso` | Arbitrary classes: checkpoint systems, **enemy spawn logic**, accessibility (colorblind), weapon clip settings, quality presets. |
| `.resource` | Resource descriptor + asset links; auto-generated, required for asset-touching mods. |

## 3. Pack & install a mod

1. Keep only your mod's files in `local\`, select them **retaining the folder
   hierarchy** (e.g. `ssl\characters\player\marine\outfits\story_titus\…`).
2. Pack with **7-Zip / zip**: format `zip`, extension **`.pak`**, compression
   **Store (0)**.
3. Move the `.pak` into `<game>\client_pc\root\mods\`. Delete the files from
   `local\`. **No `.cache` files are needed for mod paks.**
4. Multiple paks are allowed; on path collisions the **first alphabetically**
   wins. Load order can be controlled with `pak_config.yaml` in `mods\`
   (list `- pak: name.pak` entries; unlisted paks load first alphabetically).
5. Verify in-game (MODS DETECTED label, private lobbies, separate progression).

> Data-only mods (e.g. `potato-marines`) can be built **without the editor** by
> packing the modified `.sso` files directly (ZIP/Store) — no `.resource` needed.

## 4. Version control (GitHub Desktop, from the HowTo)

- Init a repo at `<game>\client_pc\root` named `mods_source`.
- `main<version>` branch = vanilla extracted files; `mod<version>` branch =
  your changes on top.
- Upgrading: new `main8.0` from vanilla files, rebase `mod8.0` on it, resolve
  `<<<<<<< / ======= / >>>>>>>` conflicts manually, then trigger resource
  regeneration (change a value → save → revert → save) and commit resources.
- **Crashes almost always mean mod files don't match the base-game version.**

## 5. Model / asset pipeline (ModelConverter)

- `ModelConverter.exe` — drag-and-drop **USF ↔ GLTF**. Name matters: input file
  must have its final name (`cc_titus`, not `my_cool_model`) since it is baked
  into the model. Flags: `--no-skin` (rigid geometry only), `--experimental`.
- `UsfExport` — converts **USF → TPL** and **TGA → PCT**, generating resources.
- `CrashReporter` — opens `SSLDMP` files to view callstacks / SSL frame memory.
- `SampleUsfFiles`, `PremadeTemplates`, `Tutorials/` — starting points.

## 6. Custom maps (Map Converter + Furnace)

Per `Map_Converter_Guide.pdf`: Map Converter turns a **GLTF** scene into an
**SCN** description; **Furnace** compiles SCN + TPL for level geometry. This is
for new/custom maps, not needed for gameplay/data mods.

## 7. Publishing — Steam Workshop (GATED)

`SteamWSModUploader\SteamWSModUploader.exe` uploads a mod to the Steam Workshop
(app id `3856330`). **Per project policy, this repo never uploads to the Steam
Workshop — publishing requires explicit user permission per mod.** The
`potato-marines` mod is built **local-install only** (`dist/`), and `SteamWSModUploader`
is documented here solely so the user can run it manually if they ever choose.

## 8. Local toolset paths used by this workspace

- Toolset root: `D:\tools\wh40k-space-marine-2-modding-tools\`
- Editor exe: `…\ModEditor\tools\ModEditor\IntegrationStudio.exe`
- SteamWS uploader: `…\SteamWSModUploader\SteamWSModUploader.exe`
- Game install: `D:\SteamLibrary\steamapps\common\Space Marine 2\`
- Game mods folder: `…\client_pc\root\mods\` (put `.pak` files here)

See [`../potato-marines/README.md`](../potato-marines/README.md) for the
data-only build that this workspace ships without needing the GUI editor.