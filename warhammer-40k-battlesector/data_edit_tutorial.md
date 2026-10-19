# Battlesector Data-Edit Tutorial — Unit & Weapon Stats

A standalone guide to changing **any** unit or weapon stat in
*Warhammer 40,000: Battlesector* and shipping it as a Vortex-installable zip,
built entirely from the game files you already own.

This guide was originally written as the companion to the **Superhuman Cadian**
demo mod (retired; its screenshots and numbers are kept here as worked examples).
The mechanics below were verified against **Battlesector 1.7.7 / Unity 6000.0.62f1
(IL2CPP)** on a real installation.

> **Single-player only.** Data edits replace core game files. Do not use mods in
> multiplayer — it can be treated as cheating and may result in bans.

---

## 0. TL;DR recipe

```bash
# 1. (once) get a toolchain that has UnityPy
uv run --no-project --with UnityPy python build.py dump   # inspect current values

# 2. edit the constants at the top of build.py
#    (UNIT_ID / UNIT_SCALE_FIELDS / WEAPON_PATCHES ...)

# 3. build a Vortex-installable zip
make build            # -> dist/<mod>-v<version>.zip
```

The zip contains the patched bundle at its game-root-relative path, which the
repo's Vortex extension deploys for you.

A runnable reference implementation of this recipe is preserved at
[`tools/data-edit/build.py`](tools/data-edit/build.py) (from the retired
Superhuman Cadian demo).

---

## 1. Two kinds of Battlesector mods — pick the right one first

| | **Data edit** (this guide) | **Runtime plugin** |
|---|---|---|
| Changes | numbers/values stored in game assets | behaviour, logic, rendering |
| Tool | **UnityPy** (edit the asset bundle) | **BepInEx 6 (IL2CPP)** + C#/Harmony |
| Ships | a patched `*.bundle` | a `BepInEx/plugins/*.dll` |
| Examples | The Great Crusade, TC Localization | Red Laser Lasgun, TC font fix |

**Unit and weapon stats are a data edit.** You do **not** need BepInEx for them.
Reach for BepInEx only when you must run code (e.g. a per-shot beam, a config UI,
a font fix). The rest of this tutorial is the data-edit path; §9 covers the
BepInEx path.

---

## 2. Where the stats live

The game's balance tables are inside one asset bundle:

```
<GameDir>/Warhammer 40K Battlesector_Data/StreamingAssets/startup_assets_all.bundle
```

Inside it are two `MonoBehaviour` tables (found by their `m_Name`):

| Table | Holds | e.g. |
|---|---|---|
| `UnitDataTable` | one stat sheet per **unit** | Cadian Shock Troops = id `7003` |
| `WeaponDataTable` | one stat sheet per **weapon** | Lasgun = id `7010` |

Both are the same shape — **parallel arrays**:

```
keys   = ["7003", ...]        # entry ids (as strings)
values = [ {stat sheet}, ... ] # the actual MonoBehaviour data
```

So `values[i]` is the stat sheet for id `keys[i]`. Editing a stat = writing one
key in that dict.

> **Both tables share the same bundle**, which is why *every* unit/weapon mod here
> replaces the same `startup_assets_all.bundle` file and they all conflict with
> each other.

---

## 3. Toolchain

You need Python 3.11+ and [UnityPy](https://github.com/K0lb3/UnityPy):

```bash
pip install UnityPy
# or, zero-install:
uv run --no-project --with UnityPy python build.py
```

Useful extras: [UABEA](https://github.com/nesrak1/UABEA) for a GUI inspector, and
[AssetRipper](https://github.com/AssetRipper/AssetRipper) if you prefer to dump
the whole game to readable YAML.

> **Windows/WSL note:** the game lives on the Windows drive. Under WSL that is
> `/mnt/d/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector`. Point
> `BS_GAME_DIR` at it.

---

## 4. Read the tables

`build.py dump` prints the values a mod targets. To explore freely, load a
bundle and find a table:

```python
import UnityPy

env = UnityPy.load("…/startup_assets_all.bundle")
for o in env.objects:
    if o.type.name != "MonoBehaviour":
        continue
    t = o.read_typetree()                      # may raise on non-script MBs
    if t.get("m_Name") == "UnitDataTable":
        keys, values = t["keys"], t["values"]
        i = [str(k) for k in keys].index("7003")   # Cadian Shock Troops
        print(values[i]["MaxHealth"], values[i]["PointCost"])
```

`keys` are **strings** on 1.7.7 (older dumps sometimes showed ints) — compare with
`str(id)` and you are safe either way (a `row_index()` helper does exactly that).

To find an id, use the stats site (`battlesector-tools/`) or grep the dump:
Cadian Shock Troops `7003`, Cadian Sergeant `7000`, Cadian Castellan `7004`.

---

## 5. The field reference (verified)

### `UnitDataTable` — the stats you'll care about

| Field | Meaning |
|---|---|
| `PointCost` | requisition cost to field the unit |
| `Members` | models in the squad (do **not** blindly double) |
| `MaxHealth` | **per-model** HP (total = `MaxHealth` × `Members`) |
| `MaxActionPoints` | AP per activation |
| `MaxMovementPoints` | movement points per turn |
| `MinMovementRange` | minimum move distance |
| `Evasion` | raises the attacker's accuracy penalty |
| `SingularArmor` | all-round armour (used when `ArmorProfile == 0`) |
| `ArmorFront/Left/Right/Rear` | directional armour (when `ArmorProfile == 1`) |
| `ArmorProfile` | 0 = singular, 1 = directional |
| `MeleeAccuracy` | melee hit chance (percentage) |
| `RangedAccuracyModifier`, `RangedFalloffModifier` | ranged tweaks |
| `ActivationRange`, `AwarenessRange`, `AwarenessConeRange`, `AwarenessConeAngle` | senses / overwatch |
| `MomentumPerModelDeath`, `CPPPerModelDeath`, `GainCPPOnModelDeath` | momentum & command points |
| `UnitHeight`, `Size`, `IsLarge`, `MemberSeparation` | model/space footprint |
| `CanMeleeReact`, `CanFallback`, `DefaultMovementMode` | behaviour flags |
| `WeaponSlots`, `LoadoutSlots`, `AbilityList` | what it carries (references) |
| `Faction`, `RoleGroup`, `Keywords`, `ShortNameID`, `LongNameID` | identity/enums — **don't touch** |

*(The full list is every key of the entry; a dump prints all of them.)*

### `WeaponDataTable` — the stats you'll care about

| Field | Meaning |
|---|---|
| `Damage` | **maximum** damage (min = 75 % of it) |
| `ArmourPenetration` | flat armour ignored; also drives crit/graze |
| `Attacks` | shots per attack (= "attacks" column in-game) |
| `APCost` | action points to fire |
| `Accuracy`, `AccuracyFalloff` | hit chance |
| `MinimumRange`, `MaximumRange`, `OptimalRange` | range band |
| `ImpactType`, `SplashDamageSettings` | single / splash / tile |
| `Ammunition`, `UnlimitedAmmunition`, `Reloadable`, `ReloadTime` | ammo |
| `Pistol` | usable in melee |
| `Keywords`, `Abilities`, `ProjectileEffect`, `CustomIcon` | references — **don't touch** |

> There is **no** `ShotsPerAttack` field in the asset — the in-game "shots" line
> is `Attacks`. (The stats site normalises some names; trust the raw asset.)

---

## 6. Edit the values

The pattern is always the same three steps: **find the table → find the entry →
write the field.**

```python
unit_obj, unit_tree = find_table(env, "UnitDataTable")
unit = unit_tree["values"][row_index(unit_tree, 7003)]
unit["MaxHealth"] = 60
unit_obj.save_typetree(unit_tree)            # <- write the edit back
```

### Scaling vs. absolute

- **Scale** a field when the change is relative: `new = old * 2`.
- **Set** a field when the change is absolute: `PointCost = 1`.

### Why *not* "multiply every field"?

A unit entry contains more than numbers: **id fields, enum codes, asset
references** (`IconRef`, `DefaultModel`), **arrays** (`WeaponSlots`,
`AbilityList`) and **flags** (`IsLarge`, `CanMeleeReact`). Doubling *those*
corrupts the unit (e.g. `DefaultModel 7003 -> 14006` = no such model; a flag
`0/1 -> 0/2`).

So "double every stat" really means **double every field in the stat sheet's
numeric list** — keep an explicit allow-list (`UNIT_SCALE_FIELDS`) and add or
remove names there to control exactly what scales.

### Type & range care

- Preserve the **type** (`int` stays `int`, `float` stays `float`) — the
  serialiser is picky. A `scaled()` helper should do this.
- **Percentages cap at 100.** `MeleeAccuracy 85 -> 170` is meaningless; cap it at
  100 (`PERCENT_FIELDS` / `PERCENT_CAP`).
- Some doubles are harmless zeroes (`ArmorFront 0 -> 0`); that's fine.

---

## 7. Build the bundle

```python
data = env.file.save(packer="original")       # <- "original" keeps the bundle format
```

Write it back at the **game-root-relative path** (the Vortex extension keys off
this path):

```
Warhammer 40K Battlesector_Data/StreamingAssets/startup_assets_all.bundle
```

Stage that path (game files only) and zip it with **fixed timestamps** so the
same inputs produce a byte-identical zip (a repo rule).

---

## 8. Package & install

### Zip layout
The archive holds files at their game-root-relative paths:

```
<mod>-v<version>.zip
└── Warhammer 40K Battlesector_Data/StreamingAssets/startup_assets_all.bundle
```

The repo's Vortex extension (`vortex-ext/game-warhammer40kbattlesector`) detects
the `Warhammer 40K Battlesector_Data/` prefix and deploys every file to its path
("Layout A"), backing up overwritten originals as `.vortex_backup`.

### Install
- **Vortex:** drag the zip in → **Deploy Mods**.
- **Manual:** `./deploy.sh <zip>` backs up the original once; `./uninstall.sh`
  restores it.

---

## 9. When you *do* need BepInEx

If your idea changes **behaviour**, not numbers (a per-shot beam, a runtime UI, a
font fix), ship a **BepInEx 6 (IL2CPP)** plugin instead:

- Install the repo's **BepInEx Framework** mod first (it is the runtime; it adds
  `winhttp.dll`, `BepInEx/`, `dotnet/` at the game root and modifies no assets).
- Write a C# plugin (`[BepInPlugin]` + HarmonyX patches), build against the
  game's `BepInEx/interop/` assemblies, and ship
  `BepInEx/plugins/YourMod.dll` — the Vortex extension treats `BepInEx/` as a
  game-root dir and deploys it for you.
- Plugin mods add files, so they **don't conflict** with data edits.

Reference implementation: [`red-laser-lasgun/`](red-laser-lasgun/).

> Rule of thumb: **stats → UnityPy data edit; behaviour → BepInEx plugin.**

---

## 10. Multiple mods: compatibility & conflicts

Battlesector mods collide at the **file** level, not the feature level. Two rules
decide everything:

1. **Does it replace a game file?**
   - *Data edits* (The Great Crusade, TC Localization) **overwrite** the files
     they ship.
   - *BepInEx plugins* (Red Laser Lasgun, the TC font fix) **add** files under
     `BepInEx/`. They never collide.
2. **Same file → one winner.** If two mods replace the same file only one can win
   it; the other's change to that file is lost.

### The two big examples

**[The Great Crusade](https://www.nexusmods.com/warhammer40000battlesector/mods/3)**
— Crusade/Planetary-Supremacy tuning (XP curve, card rarity, upgrade-card
values). Repo: [`the-great-crusade/`](the-great-crusade/). It ships **one** file:
`Warhammer 40K Battlesector_Data/StreamingAssets/startup_assets_all.bundle`.

**[Traditional Chinese Localization](https://www.nexusmods.com/warhammer40000battlesector/mods/1)**
— swaps the game's Simplified Chinese for Traditional, plus a BepInEx font fix.
Repo: [`tc-localization/`](tc-localization/). It ships **eight** files:
`startup_assets_all.bundle`, `mapbuilder-tools_assets_all.bundle`,
`resources.assets`, `sharedassets0.assets`, `sharedassets1.assets`,
`sharedassets1.assets.resS`, `Launcher/Localization/stringsChinese.resx`, and
`BepInEx/plugins/TCFix.dll`.

### What collides with what

| Mod | Replaces | Collides with |
|---|---|---|
| The Great Crusade | `startup_assets_all.bundle` | TC Localization |
| The Great Crusade *(TC-compatible build)* | `startup_assets_all.bundle` (built on TC's) | any other edit of that file |
| TC Localization | `startup_assets_all.bundle` + 6 more + a plugin | any data edit of that file |
| Red Laser Lasgun / Army Painter | nothing (add DLLs) | — always compatible |

So all data mods above fight over the **same one file**. You can install all of
them, but only one wins that file; the others' *other* files still deploy.

### Resolving it in Vortex

The extension registers the game with `mergeMods: true`, so Vortex installs every
mod but raises a **file conflict** and asks which mod provides each contested
file. The winner's copy is deployed; the loser's copy is skipped for that file.
Since the game loads exactly one `startup_assets_all.bundle`, the winner's stats
/ cards / fonts are what you get. The original is stored as
`startup_assets_all.bundle.vortex_backup` and restored when you purge.

Don't rely on install order — decide **which single bundle you want**, then make
one mod produce it.

### Combining two data edits (the real fix)

"Winner takes the file" means you *cannot* stack two bundle edits by installing
both. Instead **merge them into one build**:

- **Build on the other mod's output.** To keep TC fonts *and* your stats, point
  the base at the TC bundle:
  ```bash
  BS_VANILLA_BUNDLE="../tc-localization/translation/zh-TW/dist/startup_assets_all.bundle" \
    python build.py
  ```
  This is exactly what The Great Crusade does for its **TC-compatible** variant —
  it rebuilds its edits on top of the TC bundle. Then install that build **plus**
  the other mod's non-bundle files (TC still needs its `sharedassets*`,
  `resources.assets`, `TCFix.dll`, …).
- **Or merge the edits in one script.** Load the base bundle, apply both mods'
  patches, save once.

### Rules of thumb

- **Stats / cards / localization → one bundle, one winner.**
- **BepInEx plugins add files → free to stack** (Red Laser Lasgun + TC's font fix
  coexist happily).
- To *combine* two data edits, merge them in a single `build.py`; never install
  both blindly and hope.
- Verify by inspecting the bundle that actually loaded (see §4).

---

## 11. Recipes

**Give one unit more HP.** Set `MaxHealth` on its id; remember it is *per model*
(total = `MaxHealth × Members`).

**Make a unit cost 1.** `UNIT_ABSOLUTE_FIELDS = {"PointCost": 1}`.

**Buff a whole faction's weapons.** Loop `WEAPON_PATCHES` over the ids you want,
or iterate every entry and scale `Damage`:

```python
for w in weapon_tree["values"]:
    w["Damage"] = round(w["Damage"] * 1.5, 3)
```

**Give a weapon 50 shots.** `WEAPON_PATCHES[7010]["Attacks"] = 50`.

---

## 12. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `X not found in bundle` | wrong bundle, or the table name changed after a game update |
| `id N not found in table` | wrong id, or you're on a different game version |
| Edit has no effect in game | base bundle wasn't the one the game loads (check `deployFiles`), or another mod won the conflict |
| Game crashes on load | a non-numeric field was edited (id / enum / reference), or an `int` field got a `float` |
| Vortex doesn't deploy | the zip doesn't start with a game-root dir (`Warhammer 40K Battlesector_Data/`) and isn't wrapped in a single folder |
| Values revert | game updated and repackaged the bundle — rebuild from fresh vanilla |

---

## 13. Checklist

- [ ] Picked **data edit** (this) vs **BepInEx plugin** (§9).
- [ ] Found the unit/weapon id and confirmed it with a dump.
- [ ] Edited **only** numeric stat fields (not ids/enums/references/arrays).
- [ ] `int` fields stay `int`; percentages capped.
- [ ] Rebuilt with `make build`; `verify` passed.
- [ ] Tested in-game; single-player only.
- [ ] Documented the changes and the `startup_assets_all.bundle` conflict.

---

## 14. Using coding agents (SKILL.md)

This entire guide — plus the exact field names, table layout, and packaging steps
— is also available as a machine-readable **agent skill**:
[`skills/battlesector-modding/SKILL.md`](skills/battlesector-modding/SKILL.md).

An AI coding agent (Claude, Copilot, Cursor, …) can use it to go from *"make the
Cadian squad superhuman"* to a built, verified Vortex zip with no other context.
Ask the agent to read the skill, then describe what you want to change. The skill
tells the agent:

- when a change is a **data edit** (UnityPy) vs a **BepInEx plugin**;
- the exact tables (`UnitDataTable` / `WeaponDataTable`) and field names;
- how to find an id and edit only the safe numeric fields;
- how to build a **byte-deterministic, Vortex-installable zip**;
- and the compatibility rules in §10.

> Agents: load the skill before editing this repo's Battlesector mods — it is the
> shortest path to a correct change.

Happy modding. Now go change something other than the Cadian.
