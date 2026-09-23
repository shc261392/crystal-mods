# potato-marines — override values

Reference of every override shipped in `potato-marines.pak`, with the pristine
base value for comparison. Source: `paks/client/default/default_other.pak`
(build `24668625`). Values-only changes; `.sso` format (`key   =   value`,
CRLF) is byte-identical in structure.

## Quality settings presets

### `ssl/main/user/quality_settings/quality_settings_presets/quality_settings_presets_swarm.sso`

| Key | Vanilla LOW | potato |
| --- | --- | --- |
| `flockSpawnCoefficent` | 0.7 | **0.2** |
| `crawlingSpawnCoefficent` | 0.7 | **0.2** |
| `battlegroundSpawnCoefficent` | 0.7 | **0.2** |

Both `LOW` and `HIGH` tiers are set to 0.2 so the value holds regardless of the
in-game Swarm Quality selection.

### `ssl/main/user/quality_settings/quality_settings_presets/quality_settings_presets_physics.sso`

| Key | Vanilla LOW | potato |
| --- | --- | --- |
| `goreGibSoftLimit` | 23 | **6** |
| `goreGibHardLimit` | 43 | **12** |
| `ragdollSoftLimit` | 5 | **0** |
| `ragdollHardLimit` | 15 | **2** |
| `timerRagdollFreezeAfterLastCdt` | 5 | **0** |
| `qualityMorpheme/PhysObjecs/GoreGib` | "Debris" | "Debris" (unchanged) |

### `ssl/main/user/quality_settings/quality_settings_presets/quality_settings_presets_cloth.sso`

All tiers (`LOW`/`NORMAL`/`HIGH`) → `clothQuality = "LOW"`.

## Quality settings module defaults

Overridden so the aggressive values also apply on code paths that use module
defaults (e.g. when a tier has no explicit override):

- `.../quality_settings_modules/gore_module.sso` — 35/65 → **6/12**
- `.../quality_settings_modules/ragdoll_module.sso` — 25/50, freeze -1 → **0/2, freeze 0**
- `.../quality_settings_modules/physics_module.sso` — "DebrisSimpleToi" → **"Debris"**
- `.../quality_settings_modules/spawn_extension_module.sso` — (empty) → **coeff 0.2**
- `.../quality_settings_modules/cloth_module.sso` — "NORMAL" → **"LOW"**

## Corpse / gore collectors

- `ssl/spawn_system/despawn/corpse_collector.sso` — `min/maxCorpsesOnScene` 20/40 → **3/8**
- `ssl/spawn_system/despawn/npc_corpse_collector.sso` — 20/40 → **3/8** (`allowMaxValueOverflow` stays True)
- `ssl/spawn_system/despawn/swarm_actorless_corpse_collector.sso` — `minCorpses` 20 → **3**
- `ssl/spawn_system/actorless_gore_collector.sso` — `min/maxGibs` 35/65 → **6/12**

## Tuning

Edit the constants in `scripts/build_pak.py` and rebuild:

| Constant | Default | Notes |
| --- | --- | --- |
| `SWARM_COEFF` | 0.2 | lower = fewer boids (0.1 extreme, 0.4 mild) |
| `GIB_SOFT` / `GIB_HARD` | 6 / 12 | keep soft < hard |
| `RAG_SOFT` / `RAG_HARD` | 0 / 2 | 0/1 = single ragdoll at a time |
| `CORPSES_MIN` / `CORPSES_MAX` | 3 / 8 | lower = faster cleanup |
| `GORE_MIN` / `GORE_MAX` | 6 / 12 | lower = fewer gibs |

Safe ranges: soft < hard, all ≥ 0, `SWARM_COEFF` in (0, 1].