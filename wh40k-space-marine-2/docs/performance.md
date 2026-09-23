# Space Marine 2 — performance configuration (CPU-bound rig)

Researched for a **Ryzen 7 5800X + RTX 3090** that holds **40–50 FPS** in heavy
Tyranid swarm scenes even at the lowest in-game settings, with a **stable 120
FPS** target — **without giving up public matchmaking**. The full engine
config-surface analysis is in
[`fps-boost/docs/engine-analysis.md`](../fps-boost/docs/engine-analysis.md).

> TL;DR — Space Marine 2 is **CPU-limited** in swarm scenes. The quality tiers
> are `.sso` data in the paks; the in-game menu only offers swarm spawn coeff
> 0.7 (Low) vs 1.0 (High), and **below-Low values are pak-locked** (any pak =
> private lobbies). The matchmaking-safe aggression is: **in-game FSR 3 frame
> generation + Dynamic Resolution target 120** (to *display* 120 while the CPU
> render loop is pinned) + **OS-level CPU-core pinning** (the E-core finding
> applied to your 5800X). Delivered as the [`fps-boost`](../fps-boost/) config.

---

## 1. The CPU wall

*Space Marine 2* (Swarm Engine, DX12) is CPU-bound in hordes:
- **Digital Foundry**: Ryzen 5 3600 ~55 FPS vs 7800X3D ~110 FPS in a swarm scene
  — a ~2× CPU spread; "settings tweaks don't tend to reduce the CPU burden as
  much as the GPU burden".
- **OC3D**: CPU-limited "especially in areas with large swarms"; disabling Intel
  E-cores gave a measurable boost (platform-level, not a game setting).
- Community: i7-11700K + RTX 3080 Ti stuck ~60–65 FPS "no matter what preset".

A 5800X is a solid 8-core Zen 3, but swarm scenes want 3D-V-Cache. The rendered
rate will stay ~50–70 in full hordes no matter the settings — frame generation
is what displays 120.

## 2. Engine config surface (what is and isn't reachable)

The quality tiers live as `.sso` data in `paks/client/default/default_other.pak`
(e.g. `quality_settings_presets_swarm.sso` → `flockSpawnCoefficent` 0.7 at LOW).

| Route to override | Works? | Side effect |
| --- | --- | --- |
| Mod pak (`mods/`) | ✅ | **private lobbies** + separate progression + watermark |
| `local/` loose files | ✅ | same mod-mode restrictions |
| Edit base `.pak` | ❌ | crashes on start (official docs); EAC hash-checks |
| `video_quality.cfg` (SSF1) | ⚠️ | only selects tiers; cannot inject below-Low |
| `game.cfg` / `--set /Config/...` | ⚠️ | exposed tree is network/debug only |

**Bottom line:** below-"Low" values are only reachable via a mod. This folder
therefore optimizes the matchmaking-safe configuration to the max.

## 3. The matchmaking-safe config (see `fps-boost`)

**In-game:** Upscaling DLSS Quality · **Frame Generation FSR 3 ON** ·
FPS cap 120 · **Dynamic Resolution ON target 120** · Details/Effects/Fog
Volume/Swarm/Physics/Cloth = Low · SSAO/SSR = Default · Reflex On.

**OS-level (the "potato mode"):**
- Pin the game to **physical cores / disable SMT for it** + High priority
  (`fps-boost/scripts/apply-affinity.ps1` on Windows, `launch-sm2.sh` on Proton).
- Windows power plan → **Ultimate Performance** (`deploy.ps1` / `deploy.sh`).
- **Lossless Scaling** (owned) LSFG 3.0 frame-gen instead of FSR3 FG (not both).

**Expected on 5800X + 3090:** ~90–120 displayed FPS in full swarms; rendered
~50–70 (CPU wall). Details in `fps-boost/docs/settings-preset.md`.

## 4. If you accept private lobbies

The aggressive pak is shipped as **`potato-marines`**: swarm coeff **0.2**,
gibs **6/12**, ragdolls **0/2** (instant freeze), corpse cap **8**, gore cap
**12** — forced below the in-game Low tier via a data-only pak (12 override
files, values-only, diffed against the base paks). Private lobbies + separate
progression + "MODS DETECTED" watermark apply. Fully reversible
(`potato-marines/uninstall.*`). For maximum FPS, combine it with the fps-boost
in-game/OS config.

## 5. Config-file facts (SSF1)

User settings (`video.cfg`, `video_quality.cfg`, …) under
`%LOCALAPPDATA%\Saber\Space Marine 2\storage\platform\config\` use the `SSF1`
container (`SSF1` + sizes + MD5(masked stream) + `0x02` + XOR-zlib). Decoded
structure is in `fps-boost/docs/engine-analysis.md` §3; the XOR key is unknown
and not a short pattern, and — decisively — even a full SSF1 editor can only
select existing quality tiers, not the below-Low `.sso` values.

## 6. Sources

- Digital Foundry — *Space Marine 2: Best PC Settings* (2024)
- OC3D — *Space Marine 2 PC performance review*
- Official SM2 modding portal — https://spacemarine2-modding.prismray.io/
- PCGamingWiki — *Warhammer 40,000: Space Marine 2*
- Base-pak / executable analysis (build `24668625`) — this repository