# Space Marine 2 — engine config-surface analysis

What the Swarm Engine actually exposes for configuration, and why aggressive
below-"Low" graphics values cannot be applied without a mod. Researched against
the local install (build `24668625`, `default_other.pak` / `default_ssl.pak`).

## 1. Quality tiers are data, not code

The in-game quality menus (Swarm / Physics / Cloth / Details / Effects / …)
read per-tier **`.sso` text files** inside `paks/client/default/default_other.pak`:

```
ssl/main/user/quality_settings/quality_settings_presets/quality_settings_presets_swarm.sso
    swarmPresets = { LOW = { SpawnExtensionModule = { flockSpawnCoefficent = 0.7 ... } }, HIGH = { } }
ssl/main/user/quality_settings/quality_settings_presets/quality_settings_presets_physics.sso
    physicsPresets = { LOW = { GoreModule = { goreGibSoftLimit = 23 ... } RagdollModule = { ... } }, HIGH = { } }
ssl/main/user/quality_settings/quality_settings_presets/quality_settings_presets_cloth.sso
    clothPresets = { LOW/NORMAL/HIGH = { ClothModule = { clothQuality = "LOW" } } }
```

- **Swarm Quality** menu: `LOW` = spawn coefficients **0.7**, `HIGH` = 1.0 (empty
  override → module defaults). There is **no way to select below 0.7 from the UI.**
- **Physics Quality** menu: `LOW` = gibs 23/43, ragdolls 5/15, freeze 5 s.
- The module defaults (`quality_settings_modules/*.sso`) are the HIGH-tier values
  (gibs 35/65, ragdolls 25/50).
- The UI setting model files (`ui/screens/settings/ui_setting_models/misc/*.sso`)
  confirm only these two/three tiers are offered.

The compiled SSL (`quality_settings_pc_release.sslbin`) contains only class
names — no quality values, no config-tree paths. Quality is fully data-driven.

## 2. Every route to override that data

| Route | Works? | Side effect |
| --- | --- | --- |
| Mod pak in `client_pc/root/mods/` | ✅ | **Private lobbies only** + separate progression + "MODS DETECTED" watermark (official Saber rule) |
| Loose files in `client_pc/root/local/` | ✅ | Same mod-mode restrictions (official docs: "Corrupt files" warning + MODS DETECTED) |
| Edit base `default*.pak` in place | ❌ | **Crashes the game on start** (official docs). EAC additionally hash-checks game files. |
| `%LOCALAPPDATA%\Saber\...\config\*.cfg` | ⚠️ | `SSF1` container — only **selects tiers**; cannot inject values below a tier. See §4. |
| `client_pc/root/config/pc/game.cfg` + `--set /Config/...` | ⚠️ | Exe reads `../../config/pc/game.cfg` and supports `--set`, but the exposed config tree is **network/debug** (`/Config/RedstoneGlobals/*`, `/Config/Epic/*`, `/Config/steam/*`) — no quality keys. |

**Conclusion:** below-"Low" values (e.g. swarm coeff 0.25, ragdolls 1/3) are
reachable **only** through pak data, and every pak route disables public
matchmaking. There is no engine-level, matchmaking-preserving override for
them. The aggressive-but-fair ceiling with public matchmaking is the in-game
LOW tier + the non-mod config in this folder.

## 3. `SSF1` user-config container (decoded structure)

`config.cfg`, `video.cfg`, `video_quality.cfg`, `shared_user_settings.cfg`,
`sound.cfg` under `storage/platform/config/` use a header we reverse-engineered:

```
SSF1                     magic
u32                      masked-stream length        (bytes from offset 53)
u32                      0
u32                      uncompressed length
u32                      0
32×ASCII-hex             MD5(masked stream)          (verified for all 5 files)
0x02                     scheme byte
masked zlib stream       deflate payload, XOR-masked with an unknown key
```

The 16-byte MD5 covers the **masked** stream, so an editor can recompute it.
The codec is confirmed as **XOR + zlib** (Swarm Engine Save Editor FAQ,
https://www.nexusmods.com/johncarpenterstoxiccommando/mods/12). The XOR key is
not a short repeating key (lengths 1–3 exhausted) nor a common string.

**Practical consequence:** even with full SSF1 support, editing `video_quality.cfg`
can only force the tier selection and other user-level settings (render
resolution, DLSS/FSR mode, frame-gen toggle, FPS cap, dynamic resolution).
It **cannot** reach the per-tier `.sso` values that live in the paks. Those are
the CPU-cost switches this mod targets.

## 4. What is aggressive and matchmaking-safe

- **In-game FSR 3 Frame Generation** (v5.0+, not a quality tier) — displays 120
  when the CPU render loop is pinned. Works with public matchmaking.
- **Dynamic Resolution → target 120** — auto-scales internal resolution.
- **CPU-core scheduling (OS-level)** — pin the game to physical cores / disable
  SMT for it (the AMD analogue of the OC3D E-core finding), high-performance
  power plan.
- **Lossless Scaling** (driver-level overlay) — LSFG frame-gen / scale stack;
  invisible to the game, EAC-safe, keeps public matchmaking.

## 5. If the private-lobby trade-off is ever accepted

The aggressive pak (swarm coeff 0.25, gibs 8/16, ragdolls 1/3, faster corpse
collection, 12 override files diffed against the base paks) is fully speced and
was validated against `default_other.pak`. Rebuild from the data in §1 by
overriding the four preset files + module defaults + corpse/gib collectors;
the format is `key   =   value` CRLF text and mod paks are ZIP/Store. Not
shipped here because it costs public matchmaking.