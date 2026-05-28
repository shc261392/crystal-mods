# Graphic Improvement Mod Survey — DoW: Definitive Edition

> **Status**: Research / feasibility survey  
> **Scope**: What visual quality improvements are possible beyond the DE baseline, and how hard is each one.

---

## 1. Baseline: What the DE Already Improved

Relic's Definitive Edition remaster (2022) layered new, higher-priority archives on top of the original data. Understanding this layering is essential before planning any further improvements.

### Module load order (`W40k.module`, first wins)

| Priority | Archive / Folder | Contents |
|----------|-----------------|----------|
| 1 (highest) | `W40kData-SharedTextures-Definitive.sga` | Remaster-quality shared textures |
| 2 | `W40kData-SharedTextures-Full.sga` | Full-res original shared textures |
| 3 | `W40kData-Whm-Definitive.sga` | Remaster-quality unit/building models |
| 4 | `W40kData-Whm-High.sga` | High-quality original models |
| 5 (lowest) | `W40kData.sga` | Base game data (2004) |

The same `Definitive` / `Full` / `High` pattern repeats for `DoWDE`, `DXP2`, `DXP3`, and `WXP` campaign modules.

**Key insight**: A mod only needs to place its files at a higher priority than `*-Definitive.sga` to override DE assets — no patching required. This is done by deploying loose files to the `Data_Shared_Textures\Remaster` or `Data_Whm\Remaster` folder paths, or by registering a mod archive that loads before the DE ones.

### What DE improved vs original (2004):
- Texture resolution: 2–4× upscale on most unit textures and terrain
- Unit models: higher poly counts and additional detail meshes in `*-Definitive.sga`
- Shadow support: added entirely (absent from original)
- Widescreen: proper aspect ratio handling
- Anti-aliasing: MSAA options exposed in settings
- Cutscene FMV: pre-rendered movies at higher resolution

### What DE did NOT improve:
- No ray tracing, no DLSS/FSR (DX9 engine)
- Particle/VFX density and resolution largely unchanged
- Terrain textures partially updated, inconsistent quality
- Shadow map resolution and draw distance capped
- No ambient occlusion
- No screen-space reflections
- Shader pipeline unchanged from 2004 HLSL

---

## 2. Graphics Pipeline Overview

DoW DE runs on the **Relic Essence Engine** (v1/v2), a custom DirectX 9 engine.

| Layer | Technology | Modifiable? |
|-------|-----------|-------------|
| Renderer | DirectX 9 | No (engine binary) |
| Shaders | HLSL `.fx` / compiled `.fxo` | Partial (see §4) |
| Textures | `.rsh` / `.rtx` (Relic Chunky wrapper over DXT) | Yes, with decode step |
| Models | `.whm` / `.whe` (Relic Chunky) | Yes (official tools) |
| Particles / VFX | `.bfx` / `.fx` | Yes (FxTool) |
| Terrain materials | `.terrainmaterial` + `.rtx` | Yes |
| UI | `.swf` / `.gfx` (Flash/Scaleform) | Yes |
| Post-processing | None (engine-native) | Via ReShade injection |

### Key File Formats (confirmed by inspection)

All graphical assets use the **Relic Chunky** container format (`magic: "Relic Chunky"`):

| Extension | Relic Chunky type | Contents |
|-----------|-------------------|----------|
| `.rsh` | `FOLDSHRF` → `FOLDTXTR` → `DATADATA` | Unit/building textures (diffuse, specular, normal) |
| `.rtx` | Relic Terrain Texture | Terrain tiles and decals |
| `.wtp` | Team colour palette | Per-race recolour masks |
| `.whm` | `FOLDMSGR` → mesh data | 3D model (geometry + UV + bone weights) |
| `.whe` | Animation data | Skeleton keyframe animation |
| `.rsh` (shader) | `FOLDSRSL` | HLSL shader source/bytecode |

**Important**: None of these are plain DDS files. Upscaling requires a `decode → edit → re-encode` pipeline.

### SGA archive inventory (confirmed)

| Archive | Size | File count | Notable contents |
|---------|------|------------|-----------------|
| `W40kData-SharedTextures-Definitive.sga` | 1.2 GB | 2,805 `.rtx` + 256 `.terrainmaterial` + 171 `.wtp` + 89 `.rsh` | **DE-quality** race textures, terrain, UI icons, decals |
| `W40kData-SharedTextures-Full.sga` | 27 MB | 324 `.rsh` | Original full-res unit texture sheets |
| `W40kData-Whm-Definitive.sga` | 203 MB | 455 `.whm` + 162 `.whe` | **DE-quality** unit/building models |
| `W40kData-Whm-High.sga` | 16 MB | (original high-poly models) | Original high-poly fallback |
| `W40kData.sga` | 1.5 GB | 1,942 `.tga` + 639 `.dds` + 2,395 `.lua` + 1,574 `.rgd` + 533 `.rtx` | Base game data, scripts, AI, data tables |

**Key insight**: The base `W40kData.sga` still has 1,942 `.tga` and 639 `.dds` textures that the DE remaster did **not** replace — these are the lowest-hanging fruit for improvement.

---

## 3. Opportunity Areas

### 3.1 ReShade Post-Processing  ⭐ Highest feasibility / impact

**What it is**: ReShade is a generic DX9/DX10/DX11 shader injector. It applies full-screen effects after the renderer outputs its frame. No game files are modified.

**Compatible**: Yes — DoW DE uses DirectX 9; ReShade 5.x supports DX9. Install by copying `dxgi.dll` / `d3d9.dll` and `ReShade.ini` to the game root.

**Effects possible**:
- **SMAA** — better anti-aliasing than the engine's MSAA, especially on foliage and model edges
- **HBAO / SSAO** — ambient occlusion gives depth to units and terrain that the engine completely lacks
- **Bloom / HDR tonemapping** — the engine's bloom is flat; ReShade can give it cinematic quality
- **Sharpening (CAS / LUT)** — compensates for any softness introduced by MSAA or upscaling
- **Color grading** — bring the palette more in line with Warhammer 40k's grimdark aesthetic
- **Depth of field** (subtle) — ground-level or cutscene use

**Effort**: Low — configure a preset, ship as an optional extra  
**Risk**: None (no game files changed; player can toggle on/off)  
**Deliverable**: A `.ini` ReShade preset file, installation instructions

---

### 3.2 Texture Upscaling Pack  ⭐ High impact, medium-high effort

**What it is**: Extract textures from SGA archives, run through an AI upscaler, repack and deploy at higher priority than the DE archives.

**Critical discovery**: All textures are stored in **Relic Chunky** format (`.rsh` and `.rtx`), not plain DDS. The pipeline has an extra decode/re-encode step.

**Pipeline**:
1. **Unpack SGA** → `relic-tool-sga` (`uv run relic sga unpack`) extracts loose `.rsh`/`.rtx` files
2. **Decode Relic Chunky** → extract the `DATADATA` blob from `FOLDTXTR`/`FOLDIMAG` and interpret as DXT1/DXT3/DXT5
   - Community tool: Corsix's Mod Studio (Windows) can export `.rsh` → DDS
   - Alternative: write a Python parser for the Relic Chunky binary format
3. **Upscale** → Real-ESRGAN 4× (general-purpose model); DDS → PNG → upscale → PNG → DDS
4. **Re-encode** → pack the upscaled DDS back into a `.rsh`/`.rtx` Relic Chunky file with updated `DATAATTR` dimensions
5. **Repack SGA** → `relic-tool-sga` pack into a new SGA deployed before `W40kData-SharedTextures-Definitive`

**Lowest-hanging fruit — base game assets DE did NOT replace**:  
`W40kData.sga` still contains **1,942 `.tga` and 639 `.dds` files** that are plain image files (no Relic Chunky decode needed). Upscaling these only requires steps 3–5.

**High-value DE texture categories** (in `W40kData-SharedTextures-Definitive.sga`):
- `art/ebps/races/*/texture_share/` — all race unit/building texture sheets (chaos, eldar, orks, space_marines, necrons, imperial_guard, tau, sisters, dark_eldar)
- `art/ui/ingame/*_icons/` — unit/ability icons in the HUD (most visible during play)
- `art/scenarios/textures/detail/` — tiling terrain detail (covers the entire battlefield)
- `art/decals/death/` — blood/death splat decals (10 variants per terrain type)

**Effort**: Medium-High — Relic Chunky decode adds complexity, but automation is feasible  
**Risk**: Low — upscaled textures override cleanly via the data folder priority system  
**Tools needed**: `relic-tool-sga` (already installed), Corsix's Mod Studio OR custom Python decoder, Real-ESRGAN, texconv

---

### 3.3 Shader & Visual Effects Improvements  ⭐ Medium feasibility

**What it is**: The game ships `.fx` source files (HLSL) for particle systems and object shaders inside the SGA archives. These can be extracted, edited, recompiled with `FxTool.exe` (bundled), and redeployed as a loose-file mod.

**FxTool.exe** is bundled at the game root. It is the official Relic shader/particle editor used in development.

**Target improvements**:
- **Weapon/explosion particles**: increase emitter counts, add sub-emitters for sparks/debris
- **Blood / gore particles**: higher density, longer lifetime
- **Energy weapon glow**: more volumetric bloom on plasma / psychic effects
- **Shadow softening**: edit shadow filter kernel in terrain/model shaders
- **Water shader**: improve reflection, add ripple normal map
- **Fire effects**: more sub-layers, animated noise textures

**Effort**: Medium — shader knowledge required; FxTool has a GUI for particle work  
**Risk**: Low-Medium — incorrect shader compilation crashes the effect (not the game)  
**Blocked on**: Some shaders are pre-compiled `.fxo` in the archive; only `.fx` source files can be edited without a shader decompiler

---

### 3.4 Image-Based Lighting (IBL) Tweaks  ⭐ Low effort, subtle impact

**What it is**: `Tools/ModDocs/DefaultIBL.lua` defines the default environment / ambient light cube used when no map-specific IBL is present. Editing this changes the ambient tint, intensity, and directionality of light across all maps that use the default.

**Possible changes**:
- Shift ambient colour towards a more grimdark orange/red or cold grey tone
- Increase contrast between lit and shadowed faces on models
- Apply per-campaign IBL tweaks (e.g., colder tone for Winter Assault, dry for Dark Crusade)

**Effort**: Very Low — Lua text file, no compilation, immediate effect  
**Risk**: Low — only affects ambient fill; direct lighting is separate

---

### 3.5 Model Improvements  ⭐ Low feasibility (high effort)

**What it is**: Replace `.whm` / `.sgm` model files with higher-poly versions.

**Pipeline**:
1. Extract model from SGA with `Archive.exe`
2. Open in `ObjectEditor.exe` (bundled) and export to FBX or use a third-party importer
3. Edit in Blender / 3ds Max (add geometry, improve silhouette, re-UV)
4. Import back with `FBXtoSGM.exe` (bundled FBX → SGM converter)
5. Repack as an SGA at higher priority than `*-Whm-Definitive.sga`

**Reality check**: The DE already significantly improved model poly counts. Unit models are also shared by multiplayer, so any model change must not alter hitboxes or collision geometry — the engine uses separate collision meshes, but care is still needed.

**Effort**: Very High — each unit is a substantial 3D art task  
**Risk**: Medium — model import can break animations if skeleton/vertex weights change  
**Best candidates**: Hero units (Gabriel Angelos, Gorgutz, Taldeer), where a single high-detail model has significant screen presence

---

### 3.6 UI Visual Overhaul  ⭐ Medium feasibility

**What it is**: The HUD and menus use Scaleform GFX Flash (`.swf` / `.gfx`) files. These can be decompiled with tools like JPEXS Free Flash Decompiler, edited, and repackaged.

**Possible changes**:
- Replace UI frame textures with higher-resolution versions
- Update icon art for units/abilities
- Adjust colour palette for better readability at 4K
- Modernise button layouts

**Effort**: Medium — Flash authoring skills needed; GFX format differs slightly from standard SWF  
**Risk**: Low — UI changes are cosmetic and don't affect gameplay  
**Tools**: JPEXS Free Flash Decompiler (free), Adobe Animate or Ruffle for testing, game-bundled `UIEditor.exe`

---

## 4. Feasibility Matrix

| Technique | Feasibility | Visual Impact | Effort | Risk |
|-----------|------------|---------------|--------|------|
| ReShade preset | ★★★★★ | High | Low | None |
| AI texture upscaling | ★★★★☆ | High | Medium-High | Low |
| IBL / atmosphere tweaks | ★★★★☆ | Low-Med | Very Low | Low |
| Particle / VFX (FxTool) | ★★★☆☆ | Medium | Medium | Low-Med |
| Shader source edits (`.fx`) | ★★★☆☆ | Medium-High | High | Medium |
| UI texture replacement | ★★★☆☆ | Low-Med | Medium | Low |
| Model replacements | ★★☆☆☆ | High | Very High | Medium |

---

## 5. Hard Limits (Cannot Be Modded)

| Feature | Reason |
|---------|--------|
| Ray tracing / path lighting | Requires DX12; engine is DX9 |
| DLSS / FSR upscaling | Requires DX12 / Vulkan integration |
| Deferred rendering / GBuffer | Forward renderer only; architecture is fixed in binary |
| Compiled shader override (`.fxo`) | No source → need decompiler (RenderDoc + SPIRV-Cross or similar) |
| Geometry / tessellation | No DX11 tessellation hardware stage available |

---

## 6. Recommended Starting Point

**Phase 1 — Plain texture upscaling** (2–3 days)
- Target: the 1,942 `.tga` and 639 `.dds` files in `W40kData.sga` that DE never replaced
- These are plain image files — no Relic Chunky decode required
- Pipeline: unpack SGA → upscale with Real-ESRGAN → repack as a new SGA or loose file override
- Zero tooling hurdle, immediate visual improvement on base assets

**Phase 2 — Unit portrait icons** (1 week)
- Portrait icons in `art/ui/ingame/*_icons/` are in `.rtx` Relic Chunky format
- Need the Corsix Mod Studio decode step (or a Python `.rtx` parser) added to the pipeline
- Very small files (64–256px typically), upscale to 4× is quick and has large HUD impact

**Phase 3 — Race texture sheets** (ongoing)
- The full `art/ebps/races/*/texture_share/` content covers all unit and building textures
- Same Relic Chunky pipeline as Phase 2
- Large number of assets; batch processing essential

**Phase 4 — Shader / VFX polish** (separate track)
- Use `FxTool.exe` (bundled in game root) to enhance particle effects
- Can be worked independently of texture upscaling

---

## 7. Community Resources

| Resource | URL |
|----------|-----|
| DoW Modding Wiki | https://dow.fandom.com/wiki/Modding |
| Corsix's Mod Studio (texture decode) | https://github.com/corsix/coh2-modstudio (historical; the DoW version circulates on modding forums) |
| relic-tool-sga (Python, SGA unpack/repack) | https://github.com/ModernMAK/Relic-Game-Tool |
| Real-ESRGAN upscaler | https://github.com/xinntao/Real-ESRGAN |
| texconv (DDS encode/decode, Microsoft) | https://github.com/Microsoft/DirectXTex |
| JPEXS Flash Decompiler (UI .swf/.gfx) | https://github.com/jindrapetrik/jpexs-decompiler |
| DoW modding Discord | Search "Dawn of War modding" on Discord directories |
| Bundled tools (in game root) | `Archive.exe`, `FxTool.exe`, `ObjectEditor.exe`, `FBXtoSGM.exe`, `UIEditor.exe`, `W40kME.exe` |
