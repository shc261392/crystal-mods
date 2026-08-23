# Over 40000 — Dawn of War Definitive Edition Fun / Power Cheat

A **Vortex-installable** fun mod for *Warhammer 40,000: Dawn of War —
Definitive Edition*.

> **This is a FUN mod, not a balance mod.** Game balance gets weird on purpose:
> e.g. an Imperial Guard **Sentinel is a 5-model squad** and can shred targets
> in seconds, Scouts field 10 models immediately, and you can build unlimited
> Terminators. Some factions become hilariously overpowered. That is the point.

## What it does

| Feature | Scope |
|---|---|
| **Unit (population) & vehicle (support) caps → 40001** | All modes & races (data-wide) |
| **Squad model count → ×5** (initial & max reinforce), per-model cost counter-scaled | All races & campaigns |
| **Starting requisition & power → 40001** (resource-cheat variant only) | Each campaign mission start |
| **Resource income → ×10 requisition & power** (resource-cheat variant only) | Player only |
| **Requisition bank cap → +400000** (resource-cheat variant only) | Player only |
| **Unlimited unit build limits** (Terminators, Dreadnoughts, warbosses, etc.) | Dark Crusade & Soulstorm |

Covered campaigns: **Main campaign**, **Winter Assault**, **Dark Crusade (DXP2)**,
**Soulstorm (DXP3)**.

## Two variants (choose ONE)

The `dist/` folder ships two files that are identical except for the resource
cheat:

| ZIP | Resource cheat | Playstyle |
|---|---|---|
| `over-40000-v0.1.3.zip` | **On** — start with 40001 req/power, ×10 income | Full cheat: spam anything immediately |
| `over-40000-v0.1.3-normal-resources.zip` | **Off** — normal resources | Same 5x squads / caps / unlimited limits, but you earn resources normally |

## How it works (for maintainers)

- `W40k/Data/scar/setup.scar` — every campaign mission calls `Setup_Player()`
  from this SCAR library. The mod registers a one-shot rule for the human
  player (index 0) that, ~1s after game init, applies per-player income
  modifiers (×10 requisition & power) and sets 40000 requisition + power. It
  is deliberately applied *after* `OnGameSetup` (the game itself only touches
  player data from delayed rules). Because modifiers are applied with
  `Modifier_ApplyToPlayer`, **the computer never benefits**.
- `*/Data/attrib/racebps/*_race.rgd` — the **population/vehicle caps** come
  from here. Each race file is byte-identical to vanilla except the 4-byte
  `race_squad_cap_table` floats (`base/max squad cap`, `base/max support cap`)
  are set to **40001**. This is reliable data (the same source the game uses
  for caps), unlike per-player cap modifiers which produced odd values.
- `DXP2/Data/attrib/sbps/**/*.rgd` and `DXP3/Data/attrib/sbps/**/*.rgd` —
  compiled-data overrides for the **unlimited unit limits**. Each file is
  byte-identical to vanilla except the 4-byte `max_squad_cap` float inside its
  `required_squad_cap` requirement (1/2/3/4 → 40000). These are valid `.rgd`
  files, so they load exactly like the base data. These are data-wide (apply
  to AI as well — inherent to the cap system).

## Build (Linux / WSL2)

```bash
cd dawn-of-war-de/over-40000
make build            # -> dist/over-40000-v0.1.3.zip  (resource cheat on)
make build RESOURCE_CHEAT=0
                      # -> dist/over-40000-v0.1.3-normal-resources.zip
```

- `SQUAD_SCALE=N` — multiply every squad's **initial** (`unit_min`) and **max
  reinforce** (`unit_max`) model count by N (default **5**). Example: Space
  Marine Scouts go from 2 → 10 initial / 4 → 20 max with N=5. To keep the total
  build cost and build time at vanilla levels, each unit's **per-model**
  `cost_ext` (requisition/power/time) is also divided by N (so 20 models
  cost/build like 4 used to). Fixed-model "team" units (heavy-weapons teams,
  entrenched teams) are **excluded** — scaling their model count breaks their
  state machine and crashes the game.
- `RESOURCE_CHEAT=1` (default) — start with **40001** requisition/power and ×10
  income; `RESOURCE_CHEAT=0` ships vanilla `setup.scar` for normal resources.
- `--descale-campaign-single` (on in release builds) — **single-model campaign
  variants in Dark Crusade/Soulstorm** (`_advance_sp`, `_sp`, `_veteran_sp`,
  `_hg` name markers) are **not** model-count scaled. They are spawned at
  mission start with min loadout (honor guards); scaling them froze the SIM
  (e.g. Wraithlord HG in Tau Stronghold). Skirmish single-model units
  (Predator, Rhino, Sentinel, …) still scale ×5.

> **v0.4.0 crash fix (in 0.1.0):** the experimental weapon-upgrade cap boost
> (`Over40000_BoostWeaponCaps` in `setup.scar`) was **removed**. It crashed the
> game on its 5 s tick for any squad without a `squad_reinforce_ext` upgrade
> max (432 of 866 squads — e.g. the Haemonculus Honor Guard): it evaluated
> `Squad_GetUpgradeMax(...) * 4`, which is `nil * 4` → Lua error. Diagnostic
> testing proved the block was both necessary and sufficient for the crash and
> that a nil/0 guard did not fix it, so the block is dropped entirely. Squad
> scaling itself is unaffected.

**Auto-reinforce** is a separate standalone mod:
[`auto-reinforcement/`](../auto-reinforcement/README.md). Install it alongside
this mod to auto-reinforce your squads.

**To revert to the pre-0.1.0 build:** rebuild without squad scaling
(`make build SQUAD_SCALE=0`) — that produces the old 0.3.0-style behaviour
(caps + resource cheat only, no model-count scaling). A copy of the 0.3.0 zip
is kept in `../.copilot_workspace/saved/`.

Regenerating `mod/` from a fresh game-data extraction:

```bash
# 1) extract the SGAs once (scratch space, ~9 GB)
cd .copilot_workspace
python3 -m venv sga-venv && sga-venv/bin/pip install relic-game-tool
sga-venv/bin/relic sga unpack -q "<game>/DXP2/DXP2Data.sga" -o extract/DXP2
sga-venv/bin/relic sga unpack -q "<game>/DXP3/DXP3Data.sga" -o extract/DXP3

# 2) regenerate the mod tree
make regenerate        # EXTRACT_ROOT=../.copilot_workspace/extract
make build
```

## Install (Windows / Vortex)

1. Install the **DoW DE game extension** for Vortex (`vortex-ext-game-warhammer40kdawnofwar-*.zip`) if you haven't — drag it onto Vortex's **Extensions** tab and enable it.
2. Drag `dist/over-40000-v0.1.3.zip` (or the `-normal-resources` variant) onto Vortex and **Install**.
3. Click **Deploy Mods**.
4. Launch **Dawn of War Definitive Edition** from Vortex (or Steam — the loose files are already deployed to the game folder).

**Uninstall:** disable/purge the mod in Vortex. No game files are modified by the
mod itself.

> Note: the mod deploys loose files into `W40k/Data/`, `DXP2/Data/`,
> `DXP3/Data/` of the game installation (the same mechanism the camera mod
> uses). It does not touch any `.sga` or locale files.

---

## In-game testing checklist

Test in this order — if a later step fails, the earlier ones are still valid.

### 1. Soulstorm — the caps + resources + income (most important)

- Start a **Soulstorm campaign** (any race, any difficulty) and load into the
  first battle / stronghold.
- **At mission start** your requisition and power should both be **40000**.
- Look at the **population / support counters** in the top bar — they should
  cap at **40001**.
- Build a lot of units — you should be able to exceed the normal 20-pop / 6-vehicle cap easily.
- Watch income for ~1 minute — it should come in far faster than vanilla (×10).
- Play a **skirmish** game afterwards: caps and starting resources should be **vanilla** (this mod is campaign-only).

### 2. Soulstorm — unlimited Terminators

- As **Space Marines** in the Soulstorm campaign (or skirmish), research and
  build **more than one Terminator squad**. Vanilla allows only 1.
- If Terminators are still capped at 1, the `.lua` data override format needs
  adjustment — see "Known limitations" below.

### 3. The other three campaigns

- **Dark Crusade**: start a battle — 40000 caps + resources + income, AI
  untouched.
- **Main campaign** (DoW:DE): first mission `ms01` — caps/resources/income.
- **Winter Assault**: any mission — caps/resources/income.

### 4. AI sanity check (optional)

- In any campaign battle, tab over to an AI player or check the enemy base —
  their caps should still be the vanilla values and they should NOT start with
  40000.

---

## Known limitations

- **Unit-limit overrides are data-wide.** The `required_squad_cap` change
  applies to AI players too (they can also field unlimited Terminators). This
  is inherent to how per-unit caps are stored.
- The unit-limit `.rgd` overrides are compiled data — they load exactly like
  vanilla `.rgd` files. Each is byte-identical to the base except the
  `max_squad_cap` values.
- The population/resource/income cheats run through the SCAR `Setup_Player`
  hook, which only fires in **single-player campaign missions** — by design.
- Skirmish/multiplayer intentionally keeps vanilla caps & resources.

## Repository layout

```
over-40000/
├── Makefile                    # build / regenerate / lint / verify
├── pyproject.toml              # uv project (stdlib only)
├── modinfo.json                # mod metadata (not shipped in the zip)
├── README.md
├── NEXUS_DESCRIPTION.md        # copy-paste text for the Nexus mod page
├── mod/                        # generated mod tree (the deliverable)
│   ├── W40k/Data/scar/setup.scar
│   ├── DXP2/Data/attrib/sbps/**/*.lua
│   └── DXP3/Data/attrib/sbps/**/*.lua
├── scripts/
│   ├── rgd_decode.py           # RGD (.rgd) binary decoder (Bob Jenkins hash)
│   ├── scan_squad_caps.py      # finds squad build-limit requirements
│   ├── generate_mod.py         # builds mod/ from an extraction tree
│   └── templates/              # setup.scar / setup.nocheat.scar cheat hooks
└── dist/                       # build output (gitignored)
```

## Version history

- **0.1.3** — fix DC/SS mission-start freeze: **single-model campaign variants**
  in Dark Crusade/Soulstorm (`_advance_sp`, `_sp`, `_veteran_sp`, `_hg` name
  markers) are no longer model-count scaled. They are spawned at mission start
  with min loadout (honor guards); scaling them froze the SIM (Wraithlord HG in
  Tau Stronghold). Skirmish single-model units (Predator, Rhino, Sentinel, …)
  still scale ×5. Released in two variants (`over-40000-v0.1.3.zip` /
  `-normal-resources.zip`).
- **0.1.2** — module-scoped single-model exclusion: base-game W40k/WXP
  single-model squads are not scaled (the base-game validator rejects them with
  "Squads with complex upgrades have a maximum unit count of one!"); DXP2/DXP3
  single-model squads still scale ×5. (Superseded by 0.1.3.)
- **0.1.1** — (unrevisioned fix under the public 0.1.1 label; superseded by
  0.1.2) initial single-model exclusion was applied globally, which wrongly
  stopped DC/SS single-model scaling.
- **0.1.0** — first public release. Squad model-count scaling ×5 (initial &
  max reinforce, per-model cost counter-scaled) + caps 40001 + unlimited unit
  limits, in **two variants**: resource cheat on (`over-40000-v0.1.0.zip`) or
  normal resources (`over-40000-v0.1.0-normal-resources.zip`). The
  weapon-upgrade cap boost that crashed v0.4.0-experimental was removed.
- **0.4.0-experimental** — (unreleased) cheat now hooked via `Scar_AddInit` (runs for every
  battle, including multiplayer-map campaign battles like Soulstorm's "Cerulea"
  that have no mission scar); all edits applied to all 4 modules (W40k/WXP/
  DXP2/DXP3) and all races; vehicles scale to 5x models; weapon-upgrade
  (`max_upgrades`) limit scales with the squad.
- **0.3.0** — caps now set to exactly 40001 via patched `racebps` data (v0.2.0's
  per-player cap modifiers produced ~9008/9003 values); resource + income cheat
  kept in the scar.
- **0.2.0** — fix campaign start: cheat applied via delayed rule (no
  `OnGameSetup` touches) and unit limits shipped as patched `.rgd` files
  (v0.1.0 used `.lua` overrides + applied the cheat inside `OnGameSetup`, which
  could prevent the intro event).
- **0.1.0** — first build: campaign caps/resources/income cheat + unlimited
  unit limits for Dark Crusade & Soulstorm.
