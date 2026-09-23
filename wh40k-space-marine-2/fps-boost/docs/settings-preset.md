# fps-boost — potato-mode config (keeps public matchmaking)

The engine analysis (`engine-analysis.md`) shows the below-"Low" CPU-cost values
are pak-locked, and any pak = private lobbies. So this config works **without a
mod**: it stacks every aggressive lever that *does* survive public matchmaking.

Verified target: **Ryzen 7 5800X + RTX 3090**, 40–50 FPS in heavy Tyranid
swarms → **stable 120 displayed FPS**.

## 1. In-game (Options → Graphics) — the frame-rate engine

These are the actual 120-enablers. Do **not** rely on the Quality Preset alone.

| Setting | Value | Why |
| --- | --- | --- |
| Quality Preset | Low | baseline |
| Details / Effects / Fog Volume | Low | lowest non-mod CPU/GPU budget |
| Swarm Quality | **Low** | 0.7 spawn coeff — the lowest non-mod value |
| Physics Quality | Low | gibs 23/43, ragdolls 5/15 |
| SSAO / SSR | Default | keep cheap |
| Textures / Shadows | Low–Medium | GPU side (VRAM), not the bottleneck |
| **Upscaling** | **DLSS Quality** | ~66% internal res, frees GPU headroom |
| **Frame Generation** | **FSR 3 ON** | the key 120 lever on a CPU-pinned rig (3090 can't DLSS-MFG) |
| **FPS cap** | **120** | 30/60/90/120/Unlimited options |
| **Dynamic Resolution** | **ON, target 120** | game auto-lowers internal res to hold the cap |
| NVIDIA Reflex | On | offsets frame-gen input latency |

> The menu's config files are `SSF1` (see `engine-analysis.md` §3) — these
> settings are stored there, not in any editable plaintext. Change them in-game.

## 2. OS-level CPU aggression — the "potato mode"

The OC3D finding (disabling Intel E-cores raised CPU performance) applies to
your 5800X as **disabling SMT for the game** and pinning it to physical cores:

```powershell
# after the game is running (admin): pin to physical cores 0,2,4,...,14 (0x5555)
.\scripts\apply-affinity.ps1 -Name "Warhammer 40000 Space Marine 2 - Retail"
```

```bash
# Proton / Linux: launch with taskset on physical cores 0-7 + performance governor
./scripts/launch-sm2.sh
```

Plus:
- **Power plan → Ultimate Performance** (`deploy.ps1` sets it; `powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61`).
- On WSL2 → Windows, run `powershell.exe -Command "powercfg /setactive SCHEME_MIN"` from `deploy.sh`.

## 3. Optional: Lossless Scaling (you own it)

Driver-level frame generation / upscaling, invisible to the game — **no mod
detection, keeps public matchmaking**. Use it *instead of* the game's FSR3 FG
(not both — double frame-gen causes artifacts):

- Launch game → add `Lossless Scaling` → set Scale Type **LSFG 3.0**, Frame Gen **ON** (2×/3× from the ~50-60 base → 100–180).
- Keep the game's own Frame Generation **OFF** when using LSFG.

## 4. Verify

- Load a swarm-heavy operation. Expect **~90–120 displayed FPS** in the worst
  hordes (rendered rate ~50–70 — the CPU wall is real; frame-gen smooths it).
- If LSFG/FSR3 artifacts bother you, drop to FPS cap 90.

## 5. Reverting

`./uninstall.sh` (or `uninstall.ps1`) restores the default Windows power plan.
In-game rows revert by changing them back in the menu. No game files are
touched, so nothing else needs undoing.