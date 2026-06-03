# Digimon Survive: cloth-editing survey for 2D character art

## TL;DR

If the goal is to change clothing on 2D character art without a dedicated artist, the viable path is **image-editing / inpainting**, not upscaling.

Best current approach for a developer-only team:

1. Extract the character texture from the game bundle.
2. Mask only the clothing region.
3. Use a local image editor in ComfyUI to redraw the outfit.
4. Preserve identity with reference-image guidance.
5. Replace the texture in the original bundle and test in-game.

This is realistic for a small modding team **only if the workflow is mostly mechanical**. If it needs a lot of hand painting, seam cleanup, or repeated art-direction iterations, it is probably too expensive for us and should be postponed.

---

## What I found in the game files

Digimon Survive is a Unity game, but the 2D character art is **not** a simple editable layer stack.

### Relevant bundle layout

- `StreamingAssets/StandaloneWindows64/slgchara/bu###` appears to be the main character-art area.
- `advroombg/prefabs/...` is for room/background art.
- `bm##_scene` is for battle-map scenes.

### Important observation

A quick UnityPy scan of representative `slgchara/bu###` bundles showed:

- only a few raw `Texture2D` entries
- no obvious `Sprite` slicing layer structure
- no named, friendly “cloth” or “outfit” objects

That means the clothing is most likely baked into one or more textures, not separated into a clean Unity clothing component.

### Practical interpretation

For this game, “change the cloth” likely means:

> edit pixels inside the character texture, then repack the texture into the same bundle slot

Not:

> toggle a Unity outfit field or swap a modular costume part

---

## What that means for modding

### Easy case

If the character art is a clean portrait or sprite with a clear clothing area, we can:

- extract the PNG
- mask the clothes
- inpaint a new outfit
- repack the texture

This is a good fit for a developer-led pipeline.

### Hard case

If the character art has:

- complex folds
- overlapping hair / hands / accessories
- painted lighting that must be preserved
- a non-trivial silhouette change

then we are doing real image editing, not just a texture replacement. That usually requires iterative artistic judgment.

If that happens often, the mod should be held unless we get artist support.

---

## 2026 May tool survey: what actually exists

I checked current documentation for the main tools and workflows.

### 1) ComfyUI is the best dev-friendly local hub

ComfyUI now explicitly supports:

- **Inpainting**
- **ControlNet and T2I-Adapter**
- **Flux Kontext** image editing
- **Qwen Image Edit**
- **Flux Fill** for inpainting
- **IP-Adapter**-style reference workflows via custom nodes / ecosystem support

It is also still the most practical node-graph UI for building repeatable workflows.

Why this matters for us:

- it can be operated like a pipeline, not like an art tool
- it has a local GPU workflow
- it can be automated and versioned
- it can reuse the same reference images / masks / prompts every time

### 2) ControlNet is still the structural-preservation workhorse

ControlNet remains a solid way to preserve structure while editing.
For clothing edits, useful controls are:

- pose / line art
- edge / boundary maps
- segmentation maps
- depth / normal guidance when shape matters

This is especially helpful when the outfit must follow the original body silhouette.

### 3) IP-Adapter is the strongest “keep this character looking like this” tool

IP-Adapter is designed to condition generation on an image prompt.
That makes it useful when you want:

- the same face / identity
- similar style and palette
- fewer accidental character drift issues

For character cloth edits, IP-Adapter is best as a **style/identity lock**, not as the only editing tool.

### 4) Flux Kontext and Qwen Image Edit are real 2026-era image editors

ComfyUI’s current docs list:

- **Flux Kontext** as an image-editing model
- **Qwen Image Edit** as another image-editing option
- **Flux Fill** for inpainting

These are the modern “sophisticated” tools we were asking about.

What they are good at:

- semantic image edits
- preserving much of the original subject
- making bigger changes than classic inpaint models
- reducing the amount of manual Photoshop-style work

What they are **not**:

- magic no-mask wardrobe editors
- guaranteed perfect clothing swaps without review
- a replacement for good masks and reference images

### 5) Closed/API models also exist, but they are less ideal for a modding team

ComfyUI also exposes API nodes for third-party/closed models.
That means there are more powerful hosted options in the ecosystem.

However, for this project they are a weaker fit because they tend to be:

- less reproducible
- less controllable offline
- potentially dependent on a service
- harder to pin to a stable, repeatable mod workflow

For a modding team with no artist, I would prefer local, deterministic tooling first.

---

## Recommended workflow for this project

### Best practical flow

1. **Extract the source texture** from `slgchara/bu###`.
2. **Auto-segment the clothing region**.
3. **Inpaint the outfit** with ComfyUI.
4. **Use a reference image** to keep style and identity stable.
5. **Keep the change local** to the clothing area.
6. **Repack the texture** into the same bundle.
7. **Test in-game**.

### Suggested ComfyUI stack

- **Base editor:** Flux Kontext or Flux Fill / inpaint
- **Structure preservation:** ControlNet
- **Identity/style preservation:** IP-Adapter
- **Masking:** manual mask editor first, auto-segmentation later
- **Quality gate:** human visual review before repacking

### Developer-friendly rule of thumb

Proceed only if the outfit change can be done with:

- one good mask
- one or two prompts
- one or two reference images
- at most a couple of reruns

If the workflow turns into a long back-and-forth art session, it is not a good fit for a dev-only team.

### Step-by-step: one character cloth edit (developer runbook)

This is a practical pilot flow for **one** target character image from `slgchara/bu###`.

#### Prerequisites

- Source texture extracted from one `slgchara/bu###` bundle.
- One reference image for desired outfit style (optional but recommended).
- ComfyUI with:
	- Flux Kontext or Flux Fill (inpaint)
	- one ControlNet model (line/canny/depth)
	- IP-Adapter support

#### Phase 1 — pick and prep one texture

1. Pick one image with a clear torso/clothing region (avoid occluded hands/hair for first pilot).
2. Save as `input.png`.
3. Create `mask.png` where:
	 - white = clothing region to change
	 - black = keep unchanged
4. Keep face, hair, eyes, and exposed skin mostly outside mask for identity stability.

#### Phase 2 — build minimal ComfyUI graph

Recommended first graph (simple, stable):

1. `Load Image` (input)
2. `Load Image` (mask)
3. Inpaint-capable editor path:
	 - Flux Fill *or* Flux Kontext image-edit flow
4. `IP-Adapter` branch (reference image, low-to-medium strength)
5. Optional `ControlNet` branch (canny/line) for silhouette lock
6. `KSampler` / scheduler path
7. `Save Image`

Keep graph simple first. Add complexity only if drift occurs.

#### Phase 3 — first-pass generation settings

Use deterministic seeds first to compare changes cleanly.

- Denoise / edit strength: start around `0.35–0.55`
	- lower = preserves source more
	- higher = larger outfit redesign
- Steps: `20–35` for first pass
- CFG/guidance: keep moderate (model-dependent), avoid extreme values
- IP-Adapter weight: start low-to-mid (`~0.4–0.7` equivalent range depending on node pack)
- ControlNet weight (if used): start low (`~0.3–0.6`) then increase only if silhouette drifts

#### Phase 4 — quality gate before repack

Check these 6 items:

1. Face identity unchanged.
2. Hairline and neck seams clean.
3. Hands/fingers near clothing edges are not distorted.
4. Lighting direction still matches original scene.
5. No obvious texture artifacts in masked boundary.
6. Outfit reads clearly at in-game scale (not just zoomed view).

If any 2+ fail, do one controlled retry:

- tighten mask
- reduce denoise slightly
- increase identity/reference weight slightly

If still failing after 2 retries, mark as **artist-needed** and stop.

#### Phase 5 — repack and in-game verify

1. Replace the specific source texture in the same bundle slot.
2. Repack bundle with original path/name contract preserved.
3. Deploy and test the exact scene where that character art appears.
4. Capture before/after screenshots for review.

#### Pilot acceptance criteria (go/no-go)

For a dev-only team, proceed only if pilot metrics are met:

- Time per accepted image: `<= 30–45 min`
- Retry count: `<= 2`
- Manual paint-over required: `none` or minimal
- In-game artifact severity: `none` major

If these are not met, hold the project until we can either automate better masks/prompts or add artist support.

#### Common failure modes and fastest fixes

- **Character drift (face changes):** lower denoise, raise IP-Adapter weight, shrink mask away from face.
- **Cloth edges look melted:** use tighter mask boundary, add ControlNet edge guidance.
- **Style mismatch with game art:** use a style reference from the same game scene; reduce prompt creativity.
- **Looks good in PNG but bad in game:** check alpha edges and compression artifacts before repack.

---

## What I would not try first

I would **not** start with:

- training a custom diffusion model
- making a bespoke cloth-swap model from scratch
- trying to build a Unity runtime patch to “swap clothes” at the gameplay layer
- manually redrawing every frame of animation

Those are all much heavier than the mod needs.

---

## Decision guidance

### Green light

Use this approach if:

- the clothing region is clear and maskable
- the character can be preserved with one reference image
- the edit looks good at native resolution
- the bundle repack is stable
- the quality can be checked quickly by a developer

### Hold / red light

Pause if:

- the outfit edit needs frequent artistic touch-ups
- the face/hair integrity keeps breaking
- the output only looks good after manual painting
- the change requires many iterations per image
- the final asset needs animation-aware redraws across many frames

---

## Bottom line

Yes — **sophisticated cloth-edit tools do exist in 2026**.
The best current practical path is a local ComfyUI pipeline using:

- inpainting / image editing models
- ControlNet for structure
- IP-Adapter for identity/style retention
- manual masks or semi-auto segmentation

That said, the workflow is only worth adopting if we can keep it mostly mechanical.
If it becomes an art project, we should hold it.

---

## References consulted

- ComfyUI inpainting examples: https://comfyanonymous.github.io/ComfyUI_examples/inpaint/
- ComfyUI Flux examples: https://comfyanonymous.github.io/ComfyUI_examples/flux/
- ComfyUI Qwen Image examples: https://comfyanonymous.github.io/ComfyUI_examples/qwen_image/
- ComfyUI README / features: https://github.com/Comfy-Org/ComfyUI
- ControlNet README: https://github.com/lllyasviel/ControlNet
- IP-Adapter README: https://github.com/tencent-ailab/IP-Adapter
- Digimon Survive bundle findings: `slgchara/bu###` in `StreamingAssets/StandaloneWindows64/`
