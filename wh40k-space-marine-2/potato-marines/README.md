# potato-marines — Space Marine 2 aggressive FPS mod for poor PCs

Forces Space Marine 2's engine **below** the lowest in-game quality tier to
maximize FPS on a weak CPU. A data-only mod pak that overrides the engine's
quality-settings and corpse/gib collector `.sso` files — no editor, no
`.resource` files, no `.cache` needed.

> ⚠️ **Private lobbies only.** Any pak mod disables public matchmaking:
> separate progression and a "MODS DETECTED" watermark (official Saber rule).
> Accepted for this mod. **Not published to the Steam Workshop** — local install
> only.

## What it forces (base "Low" → potato)

| System | Vanilla Low | potato-marines | Effect |
| --- | --- | --- | --- |
| Swarm spawn (`flock/crawling/battlegroundSpawnCoefficent`) | 0.7 | **0.2** | ~5× fewer Tyranid swarm boids — the big CPU win |
| Gibs (`goreGibSoft/HardLimit`) | 23 / 43 | **6 / 12** | far fewer gib entities |
| Ragdolls (`ragdollSoft/HardLimit`) | 5 / 15 | **0 / 2** | near-zero persistent ragdolls |
| Ragdoll freeze timer | 5 s | **0 s** | bodies freeze instantly |
| Corpses on scene (`corpse_collector`) | 20 / 40 | **3 / 8** | battlefield cleaned quickly |
| Gore gibs on scene (`actorless_gore_collector`) | 35 / 65 | **6 / 12** | gibs collected fast |
| Cloth quality (all tiers) | LOW (min) | LOW (min) | keep at the minimum |

All 12 override files are diffed against the pristine `default_other.pak`
originals: **values only**, exact `.sso` CRLF structure preserved. See
`docs/values.md` for the full table and tuning.

### Engine config (`game.cfg`) — the aggressive part

`deploy` also writes the engine config tree
`<game>\client_pc\root\config\pc\game.cfg` (the file `sandbox.json` points the
engine at). It drives the `Video.*` / `VideoQuality.*` / `CONFIG.*` apCfg tree
that the in-game menu cannot reach:

- **Disables** SSAO, SSR, RTAO, DOF, water simulation, terrain covering,
  capsule shadows, screen-space shadows, SSS blur, FP-model shadow split,
  dissolve pattern, distortion mask, bloom low-pass.
- **Floors** FogVolumes, Lightshafts, Shadows, Effects, Decals, Details,
  Textures, TerrainTessellation quality.
- **CPU job tuning**: `EngineWorkersCount`/`MaxJobThreads` = 8 (physical cores
  on the 5800X — the E-core-finding analogue), animation + Morpheme batching on,
  low-res particles, texture streaming off.

> ⚠️ **Verification required**: the `game.cfg` line format is the one remaining
> unknown (the engine reads `config/pc/game.cfg` and exposes the `Video.*`
> tree, but the exact parser syntax isn't documented). After launching, if the
> scene looks flat (no AO), has no depth-of-field and harsher shadows, the
> config parsed. If the game looks identical, delete `game.cfg` and report back
> — the pak part still works regardless. Everything is backed up and reverted
> by `uninstall`.

## Install (local only)

```bash
# Linux / WSL2
./deploy.sh [--game-path "D:\\SteamLibrary\\steamapps\\common\\Space Marine 2"]
# Windows
.\deploy.ps1 [-GamePath "D:\SteamLibrary\steamapps\common\Space Marine 2"]
```

`deploy` auto-detects the Steam install, builds `dist/potato-marines.pak` if
missing, installs it into `client_pc/root/mods/`, writes `pak_config.yaml`,
installs `data/game.cfg` into `client_pc/root/config/pc/`, and backs up any
prior `potato-marines.pak` / `pak_config.yaml` / `game.cfg` to `backup/`.

Also set in-game (Graphics) — the menu lets you go **OFF** for these, the user
must apply them:
- **SSAO = OFF**, **SSR = OFF**, **Motion Blur = OFF** (menu allows OFF).
- Details / Effects / Fog Volume / Swarm / Physics / Cloth = Low.
- **Dynamic Resolution = ON, target 120** · **Frame Generation = FSR 3 ON** ·
  **NVIDIA Reflex = On**.

## Uninstall

```bash
./uninstall.sh   # or uninstall.ps1
```

Removes the pak, restores the previous `pak_config.yaml` and `game.cfg`.
Restart the game to return to public matchmaking.

## Build

```bash
python3 scripts/build_pak.py        # -> dist/potato-marines.pak (ZIP, Store)
```

Tune the pak by editing the constants at the top of `scripts/build_pak.py`
(e.g. raise `SWARM_COEFF` to `0.4` for a milder effect, or drop to `0.1` for
maximum FPS), then rebuild + redeploy. Tune the engine config by editing
`data/game.cfg`, then re-run `deploy`.

## How it works

Quality tiers are data, not code: the Swarm Engine reads per-tier `.sso` files
in `paks/client/default/default_other.pak`. The in-game Swarm Quality menu only
offers coeff 0.7 (Low) / 1.0 (High); the mod pak shadows those files with values
the UI can never reach. See `../docs/modding-tools.md` §3 and
`../fps-boost/docs/engine-analysis.md` for the full engine analysis.

## Publishing

**Deliberately not on the Steam Workshop.** The toolset ships
`SteamWSModUploader` (workshop app id `3856330`); uploading requires explicit
user permission per project policy. This workspace only builds the
local-installable `dist/` pak.