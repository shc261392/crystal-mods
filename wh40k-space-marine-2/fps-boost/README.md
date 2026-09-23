# fps-boost — Space Marine 2 potato-mode config

Non-mod performance configuration for a **CPU-bound** rig (verified target:
**Ryzen 7 5800X + RTX 3090**, 40–50 FPS in heavy Tyranid swarms → **stable 120
displayed FPS**), that **keeps public matchmaking** — no pak, no private
lobbies, no watermark.

## Why not the aggressive pak?

We reverse-engineered the engine's config surfaces (see
[`docs/engine-analysis.md`](docs/engine-analysis.md)). The below-"Low" CPU-cost
values (swarm spawn coeff, ragdoll/gib limits) live **only** in `.sso` data
inside the base paks, and every route to override them (mod folder, `local/`
folder, editing base paks) either forces **private lobbies** or crashes/EAC-flags
the game. The in-game menu's lowest tier (swarm coeff 0.7) is the hard ceiling
without a mod. So this config stacks every aggressive lever that *does* survive
public matchmaking.

## What it does

| Layer | Lever | Effect |
| --- | --- | --- |
| In-game | **FSR 3 Frame Generation ON** | displays 120 when the CPU render loop is pinned at ~50 |
| In-game | **Dynamic Resolution, target 120** | auto-lowers internal res to hold the cap |
| In-game | DLSS Quality upscaling + all quality rows Low | cheapest valid GPU/CPU budget |
| OS (Windows) | `apply-affinity.ps1` | pins the game to **physical cores / SMT-off** + High priority |
| OS (Proton) | `launch-sm2.sh` | `taskset` physical cores + `performance` governor |
| OS (both) | `deploy.ps1`/`deploy.sh` | Windows power plan → Ultimate Performance |
| Optional | **Lossless Scaling** (you own it) | LSFG 3.0 frame-gen/scale on top, EAC-safe |

No game files are modified. Public matchmaking, progression and the account
stay untouched.

## Quick start

1. **In-game** (Options → Graphics): Upscaling = DLSS Quality, **Frame
   Generation = FSR 3 ON**, FPS cap = **120**, Dynamic Resolution = ON target
   120, Details/Effects/Fog Volume/Swarm/Physics/Cloth = Low, Reflex = On.
2. **Windows**: `.\deploy.ps1` (admin, sets power plan) → start the game → while
   it runs, `.\scripts\apply-affinity.ps1` (admin).
3. **Proton**: `bash deploy.sh` → `bash scripts/launch-sm2.sh`.
4. (Optional) Lossless Scaling LSFG 3.0 instead of the game's FSR3 FG — not both.

Full details: [`docs/settings-preset.md`](docs/settings-preset.md).

## Files

- `deploy.ps1` / `deploy.sh` — detect install, set Ultimate Performance power
  plan, print the guide.
- `uninstall.ps1` / `uninstall.sh` — restore the Balanced power plan.
- `scripts/apply-affinity.ps1` — pin running game to physical cores + High priority.
- `scripts/launch-sm2.sh` — Proton `taskset` affinity + governor.
- `docs/settings-preset.md` — the exact in-game + OS config.
- `docs/engine-analysis.md` — the engine config-surface research (SSF1
  container decoded, quality-tier data layout, why below-Low is pak-locked).

## Expected result (5800X + 3090)

| Scene | Rendered FPS | Displayed FPS |
| --- | --- | --- |
| Calm / corridor | ~100–120 | 120 (capped) |
| Medium combat | ~70–90 | ~120 |
| Full Tyranid swarm | ~50–70 | ~90–120 |

Frame generation smooths the output; the ~50–70 rendered rate in full hordes is
the 5800X CPU wall. For genuinely higher *rendered* FPS in swarms, the only
real lever left is a crowd-reduction pak (private lobbies) or a faster CPU.

## Links

- Performance research: [`../docs/performance.md`](../docs/performance.md)
- Engine analysis: [`docs/engine-analysis.md`](docs/engine-analysis.md)