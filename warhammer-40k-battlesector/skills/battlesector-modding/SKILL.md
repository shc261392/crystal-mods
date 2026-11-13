---
name: battlesector-modding
description: "Extract, edit, and package mods for Warhammer 40,000: Battlesector (Unity 6 IL2CPP). Use to change unit or weapon stats (HP, movement, action points, damage, attacks, armour penetration, point cost), patch the startup_assets_all.bundle Unity asset bundle with UnityPy, build BepInEx 6 IL2CPP runtime plugins, or produce a Vortex-installable mod zip from scratch."
---

# Modding Warhammer 40,000: Battlesector

Everything needed to go from the installed game to a **Vortex-installable zip**.
Verified on **Battlesector 1.8.0 / Unity 6000.0.62f1 (IL2CPP)**. The 1.7.x
table layout is also supported by the readers described below.

## 0. Decide the mod type first

| Want to change | Type | Tool | Ships |
|---|---|---|---|
| Unit/weapon **stats** (HP, movement, AP, damage, attacks, AP-pen, cost) | **Data edit** | UnityPy | a patched `*.bundle` |
| Upgrade-card effects, XP curves, rewards | **Data edit** | UnityPy | a patched `*.bundle` |
| **Behaviour** (rendering, UI, fonts, logic hooks) | **BepInEx plugin** | BepInEx 6 IL2CPP + C# | `BepInEx/plugins/*.dll` |

**Unit/weapon stats are a data edit — no BepInEx needed.** Reach for BepInEx only
when you must run code.

## 1. Key paths & constants

```
<GameDir>/Warhammer 40K Battlesector_Data/StreamingAssets/startup_assets_all.bundle
    ├─ MonoBehaviour "UnitDataTable"    (1.7.x data; since 1.8.0 a composite with
    │                                    empty keys/values and `sources` -> per-faction)
    ├─ MonoBehaviour "UnitFactionDataTable_<Faction>"     (1.8.0 rows)
    ├─ MonoBehaviour "WeaponDataTable"  (1.7.x data; composite since 1.8.0)
    ├─ MonoBehaviour "WeaponFactionDataTable_<Faction>"   (1.8.0 rows)
    └─ MonoBehaviour "SharedWeaponDataTable"              (1.8.0 shared weapons)
```

**1.8.0 composite layout.** The parent tables keep `keys`/`values` empty and
store a `sources` array. Read the per-faction tables for data edits, or call the
parent's `Keys`/`Values` from a BepInEx plugin (they trigger the merge). New in
1.8.0: `ShotsPerSwitch` on weapons (firing grouping/VFX, not damage) and
`BallisticWeaponTargetType` value 3 (`SwitchingTargetPerMember`).

**1.8.0 content/font landmines.** 205 unit rows (10 Servants of Chaos units plus
5 variants), 446 weapon rows, 12 factions; new weapons Enraged Strikes, Plasma
Rifle, Cyclic Ion Raker. Fonts moved to `sharedassets2.assets` (pid 370
`NotoSansCJKjp-Regular SDF`, 369 `... - No Underlay`, 368
`FuturaBT-CondMedium SDF`, 371 Roboto, 372 futura). A TC bake grows the last
atlas to 2048×4096 and must retarget any runtime font swap to pid 370 / name
`NotoSansCJKjp-Regular SDF`.

- Game exe: `Warhammer 40K Battlesector.exe`; Steam app `1295500`, GOG `1248481392`.
- Typical `GameDir`: Windows `D:\SteamLibrary\steamapps\common\Warhammer 40000 Battlesector`;
  WSL `/mnt/d/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector`.
- **Never assume `.vortex_backup` is pristine or current.** Vortex may keep a
  backup from an older game build (during the 1.8.0 rollout the backup was still
  1.7.7, dated July 22). Use Steam → *Verify integrity of game files*, or
  snapshot the live file immediately after a game update, before deploying.
- A missing `startup_assets_all.bundle` surfaces as Addressables
  `RemoteProviderException: Invalid path in AssetBundleProvider` and the game
  freezes at Bootstrap. Check that the live file exists, not only the backup.
- Table `path_id`s (1.7.7, for reference only — **always find tables by `m_Name`**):
  `UnitDataTable = -4059264497134316581`, `WeaponDataTable = 297598000547913130`.
  In 1.8.0 find `UnitDataTable`/`WeaponDataTable` first, then walk their `sources`
  (or match `*FactionDataTable_*` / `SharedWeaponDataTable`).

## 2. Toolchain

```bash
uv run --no-project --with UnityPy python build.py     # zero-install
# or: pip install UnityPy
```
Python 3.11+. Optional GUI: UABEA; bulk dump: AssetRipper.

## 3. Read a stat table

```python
import UnityPy
env = UnityPy.load(BUNDLE)                       # BUNDLE = pristine startup_assets_all.bundle
for o in env.objects:
    if o.type.name != "MonoBehaviour":
        continue
    try:
        t = o.read_typetree()
    except Exception:
        continue                                 # non-script MonoBehaviours can't be parsed
    name = t.get("m_Name", "")
    if name == "UnitDataTable" or name.startswith("UnitFactionDataTable_"):
        keys = [str(k) for k in t["keys"]]       # ids are STRINGS
        if "7003" not in keys:                   # composite parent / other faction
            continue
        unit = t["values"][keys.index("7003")]   # Cadian Shock Troops
        print(name, unit["MaxHealth"], unit["PointCost"])
```

Tables are parallel arrays: `values[i]` is the stat sheet for `keys[i]`. **Compare
ids with `str(id)`** (older exports sometimes used ints).

### How to edit (the whole pattern)
```python
obj, tree = find_table(env, "UnitDataTable")     # find by m_Name
row = tree["values"][row_index(tree, 7003)]
row["MaxHealth"] = 60                            # poke the field
obj.save_typetree(tree)                          # write it back
data = env.file.save(packer="original")          # "original" keeps the bundle format
```

## 4. Field reference (`UnitDataTable`)

| Field | Meaning |
|---|---|
| `PointCost` | requisition cost |
| `Members` | models in squad (don't blindly scale) |
| `MaxHealth` | **per-model** HP (total = `MaxHealth` × `Members`) |
| `MaxActionPoints` | AP per activation |
| `MaxMovementPoints`, `MinMovementRange` | movement |
| `Evasion` | accuracy penalty on attackers |
| `SingularArmor` / `ArmorFront…Rear` / `ArmorProfile` | armour (0 = singular, 1 = directional) |
| `MeleeAccuracy` | % |
| `RangedAccuracyModifier`, `RangedFalloffModifier` | ranged tweaks |
| `ActivationRange`, `AwarenessRange`, `AwarenessConeRange`, `AwarenessConeAngle` | senses/overwatch |
| `MomentumPerModelDeath`, `CPPPerModelDeath`, `GainCPPOnModelDeath` | momentum / command points |
| `UnitHeight`, `Size`, `IsLarge`, `MemberSeparation` | footprint (visual/LOS — risky) |
| `WeaponSlots`, `LoadoutSlots`, `AbilityList`, `DefaultModel`, `IconRef`, `Faction`, `RoleGroup`, `Keywords` | **references/enums — never scale** |

## 5. Field reference (`WeaponDataTable`)

| Field | Meaning |
|---|---|
| `Damage` | **max** damage (min = 75 % of it) |
| `ArmourPenetration` | flat armour ignored; drives crit/graze |
| `Attacks` | shots per attack (the in-game "attacks") |
| `ShotsPerSwitch` | **1.8.0:** shots per target before switching (targeting/VFX; total shots still `Attacks`) |
| `APCost` | AP to fire |
| `Accuracy`, `AccuracyFalloff` | hit chance |
| `MinimumRange`, `MaximumRange`, `OptimalRange` | range band |
| `ImpactType`, `SplashDamageSettings` | single / splash / tile |
| `Ammunition`, `UnlimitedAmmunition`, `Reloadable`, `ReloadTime` | ammo |
| `Pistol` | melee-usable ranged |
| `NameID`, `CustomIcon`, `Keywords`, `Abilities`, `ProjectileEffect` | **references — never scale** |

There is **no `ShotsPerAttack`** field in the asset — `Attacks` is the total.
1.8.0 adds `ShotsPerSwitch` and `BallisticWeaponTargetType` 3
(`SwitchingTargetPerMember`).

## 6. Editing rules (don't corrupt the unit)

- **Scale only numeric stat fields**, never ids / enums / asset refs / arrays.
  Doubling `DefaultModel 7003 → 14006` or a flag `0/1 → 0/2` breaks the unit.
- **Preserve type**: `int` stays `int`, `float` stays `float` (the serialiser is
  picky). `int(round(old * mult))` for int fields; `old * mult` for floats.
- **Cap percentages at 100** (`MeleeAccuracy`, `RangedAccuracyModifier`, …).
- Scaling harmless zeroes (`ArmorFront 0 → 0`) is fine.

## 7. Look up ids

Use the stats site data (`warhammer-40k-battlesector/battlesector-tools/src/data/units.json`
and `weapons.json`) or grep a dump. Known: Cadian Shock Troops `7003`, Cadian
Sergeant `7000`, Cadian Castellan `7004`, Lasgun `7010`.

## 8. Package a Vortex-installable zip

The repo's Vortex extension (`vortex-ext/game-warhammer40kbattlesector`) accepts a
zip whose files sit at **game-root-relative paths** (or are wrapped in one folder):

```
mod-v1.0.0.zip
└── Warhammer 40K Battlesector_Data/StreamingAssets/startup_assets_all.bundle
```

- **Game files only.** Do **not** put `modinfo.json`, `README.md`, docs, or
  sources in the archive: the Vortex extension deploys *every* archive path, so
  they would land in the game root. `modinfo.json` is repo metadata
  (id/name/version/changes/deployFiles/conflicts) — keep it in the repo, not the zip.
- Write the zip **deterministically** (fixed timestamps) — repo rule 15:

```python
import zipfile
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for arc, data in sorted(entries.items()):
        zi = zipfile.ZipInfo(arc, date_time=(1980, 1, 1, 0, 0, 0))
        zi.external_attr = 0o644 << 16
        z.writestr(zi, data)
```

- Output to the mod's `dist/` folder (never `/tmp`). Zips and `*.bundle` are
  gitignored — commit the **source** (`build.py`, docs, scripts), not the zip.
- **Ignored binaries.** `*.bundle`, `*.ttf` and `*.otf` are gitignored. If a mod
  must embed a small licensed asset (e.g. the Warpstorm configurator's SIL-OFL
  Barlow fonts), add a narrow `!` exception, commit the files, and make the
  build fail when they are missing. A clean worktree does not inherit ignored
  files; a silent empty glob produced a configurator EXE that crashed at
  startup.
- Provide a `Makefile` with one canonical `make build` and both `deploy.sh` +
  `deploy.ps1` (and matching `uninstall`) — repo rule 8.

Reference implementation: `warhammer-40k-battlesector/data_edit_tutorial.md`
(the Superhuman Cadian demo that produced it is retired).

### Verify before shipping
Re-open the produced bundle and assert the new values, **and** confirm a second
`make build` is byte-identical (sha256). Never claim "done" without both.

### Troubleshooting a broken install

- **Game freezes at Bootstrap / `Invalid path in AssetBundleProvider`:** the
  live `startup_assets_all.bundle` is missing or the Vortex deployment is
  incomplete. Purge mods, verify the game files, then redeploy. Do not restore a
  stale `.vortex_backup` from an older build.
- **Plugin not loading:** check `BepInEx/LogOutput.log` for the
  `[Info : YourMod]` line; no line means the DLL was not deployed or BepInEx did
  not run.
- **Configurator/desktop tool exits immediately:** read its own log next to the
  EXE; Avalonia font/asset failures point at a missing embedded resource.

## 9. BepInEx plugin path (behaviour mods)

1. Ship/[require] the repo's **BepInEx Framework** mod (BepInEx 6 IL2CPP
   Bleeding-Edge build **#785**, SHA-256
   `2a7cbf74d26abe4765c3e662db1721b923bac39849ebfef2ca5dc7de7e2d9b7f`). It adds
   `winhttp.dll`, `doorstop_config.ini`, `.doorstop_version`, `BepInEx/`, `dotnet/`
   at the game root and modifies no assets. Launch once so BepInEx generates
   `BepInEx/interop/`.
2. Write a C# plugin: `[BepInPlugin(GUID, name, ver)]` + HarmonyX patches; build
   against the game's `BepInEx/interop/` assemblies.
3. Ship `BepInEx/plugins/YourMod.dll` — the Vortex extension treats `BepInEx/` as
   a game-root dir and deploys it (Layout A). Reference: `red-laser-lasgun/`.

### Applying data edits at runtime (no bundle replacement)

The same stats can be edited from a plugin; Warpstorm is the reference. Known
managed hooks in 1.8.0 (`BepInEx/interop/Assembly-CSharp.dll`):

| Data | Hook |
|---|---|
| Units / weapons | `RuntimeDataTables.Instance.UnitDataTable` / `.WeaponDataTable`; use `.Keys` / `.Values` / `.Count` — they merge the composite source tables |
| Upgrade cards | `.WarzoneUpgradesDataTable.AllUpgrades` / `.AllClusterModifiers`; each `WarzoneUpgradeCard.statsModifiers` |
| XP / card drops | `.WarzoneConfig.RewardConfig` (`expNeededToLevelUp`, `CardDropProbabilities`, `rewardModifiers`) |
| Localised text | `TextRepositoryManager.Instance.GetRepository(type)`, then its `strings` list or a `GetItem` Harmony hook |
| Fonts | swap `TMP_FontAsset` references at runtime; TCFix is the reference |

Trade-offs: a runtime plugin adds no file conflicts and survives asset
re-serialisation, but requires BepInEx, must run after the tables load, and can
break when IL2CPP type/field names change. A bundle edit needs no BepInEx and
applies before any code, but wins the whole file and must be rebuilt on every
game update.

Plugin mods add files → **no conflicts**. Data edits overwrite files → they
conflict with any other mod touching the same bundle.

## 10. Compatibility facts

- All unit/weapon/upgrade data lives in **one** file
  (`startup_assets_all.bundle`) → **only one data-edit mod can win it**. The Great
  Crusade and TC Localization both target it.
- To keep TC fonts **and** your stats, build on the TC bundle:
  `BS_VANILLA_BUNDLE=.../tc-localization/translation/zh-TW/dist/startup_assets_all.bundle python build.py`.
- Stats mods are **single-player only**; disable for multiplayer.

## 11. Repository conventions (this repo)

**The authoritative rules are in [`AGENTS.md`](../../../AGENTS.md) at the repo
root. Read it before changing anything here; this section is only a reminder.**

- Mods at `<game>/<mod>/`; scratch in `./.agent_workspace/` (never `/tmp`);
  distribution zips in the mod's `dist/`.
- One deterministic build recipe: `make build`; required variants live in the
  committed files, not ad-hoc flags.
- Don't modify the user's game files without approval; build the zip, let the user
  deploy (or use the repo's Vortex extension).

## 12. Worked example (retired Superhuman Cadian demo)

Unit `7003` every core stat ×2 (`MaxHealth 30→60`, `MaxActionPoints 1→2`,
`MaxMovementPoints 4→8`, `Evasion 5→10`, `SingularArmor 2→4`, `MeleeAccuracy
85→100`…) + `PointCost 40→1`; weapon `7010` `Attacks 4→50`, `Damage 4→8`,
`ArmourPenetration 1→2`. See `warhammer-40k-battlesector/data_edit_tutorial.md`.
