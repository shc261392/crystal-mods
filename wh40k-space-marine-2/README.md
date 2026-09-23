# Warhammer 40,000: Space Marine 2 — modding workspace

Home for mods and configuration for *Warhammer 40,000: Space Marine 2*
(Saber Interactive / Focus Entertainment, Swarm Engine).

## Game facts (researched)

| Field | Value |
| --- | --- |
| Steam App ID | `2183900` |
| Engine | Swarm Engine (SWAR — same lineage as World War Z) |
| Graphics API | Direct3D 12 |
| Anti-cheat | Easy Anti-Cheat (EAC) |
| Online | Co-op (3) + Versus (12), crossplay PS5/Xbox, Epic Online Services |
| Release | 2024-09-09 |
| PCGW | https://www.pcgamingwiki.com/wiki/Warhammer_40,000:_Space_Marine_2 |

## Installation (this machine)

- Steam: `/mnt/d/SteamLibrary/steamapps/common/Space Marine 2/`
  (`D:\SteamLibrary\steamapps\common\Space Marine 2\` on Windows)
- Windows launcher: `Warhammer 40000 Space Marine 2.exe` →
  `start_protected_game.exe` → `client_pc/root/bin/pc/Warhammer 40000 Space Marine 2 - Retail.exe`
- Language (Steam manifest): `tchinese` (UserConfig.language)

### Game directory layout

```
Space Marine 2/
├── client_pc/root/
│   ├── bin/pc/                        Executables + DX12/dlls
│   ├── loadconfig/*.loadcfg           Engine startup scripts (text)
│   ├── local/                         Dev/test loose-file overrides
│   ├── mods/                          ** Official mod folder (.pak) **
│   ├── paks/client/default/           Base game .pak archives (+ .cache)
│   ├── prebuild/svg/                  Prebuilt shader/UI data
│   └── sandbox/                       Server-side data
├── EasyAntiCheat/                     EAC runtime
└── server_pc/                         Dedicated server data
```

### User settings & save data (SSF1 format)

User config lives under `%LOCALAPPDATA%\Saber\Space Marine 2\`:

| Path | Contents |
| --- | --- |
| `storage/platform/config/*.cfg` | `video.cfg`, `video_quality.cfg`, `shared_user_settings.cfg`, `sound.cfg`, `config.cfg` |
| `storage/steam/user/<steamid>/Main/config/` | per-user settings + save data |
| `client/UserConfigs/` | SSO user config |

> **Important:** these `.cfg` files carry an `SSF1` header — Saber's proprietary
> compressed/encrypted format. There is **no public tool** to read or write
> them. Settings must be changed from the **in-game Options menu**. Deleting a
> `.cfg` forces the game to regenerate safe defaults.

## Mod system (official, post-v7.0)

- Mods are plain **ZIP archives** renamed `.pak`, placed in
  `client_pc/root/mods/`. 7-Zip/`zip` can create and open them; use **Store**
  (no compression) and the internal `tpl/`, `pct/`, `ssl/` layout.
- Mod paks shadow base paks (`paks/client/default/*.pak`) by internal path and
  load alphabetically; `pak_config.yaml` in the mods folder controls order.
- **Any mod = private lobbies only.** Public matchmaking is disabled, an
  on-screen "MODS DETECTED" watermark appears, and progression is tracked
  separately. This applies to every mod, official or community.
- Official docs & toolset: https://spacemarine2-modding.prismray.io/
  (Mod Editor = `IntegrationStudio`, plus PakManager / PakCacher / texmipper).

## Mods & configs in this folder

| Mod | What it does |
| --- | --- |
| [`potato-marines/`](potato-marines/README.md) | **Aggressive FPS mod for poor PCs** (private lobbies accepted). Data-only pak forcing CPU-heavy systems below the in-game Low tier: swarm spawns 0.7→0.2, gibs 23/43→6/12, ragdolls 5/15→0/2, corpses 40→8. Local-install only (not published to Steam Workshop). |
| [`fps-boost/`](fps-boost/README.md) | **Potato-mode config that keeps public matchmaking** (no mod). In-game FSR 3 frame generation + Dynamic Resolution (target 120) + DLSS Quality, OS-level CPU-core pinning (SMT-off) + high-power plan, Lossless Scaling setup. Includes the engine config-surface research proving below-Low values are pak-locked. |
| [`docs/performance.md`](docs/performance.md) | Full performance research: Swarm Engine config surface, CPU bottleneck, frame-gen guidance. |
| [`docs/modding-tools.md`](docs/modding-tools.md) | Official Saber modding toolset usage guide (ModEditor / IntegrationStudio, ModelConverter, ResourceTools, Map Converter, SteamWSModUploader). |