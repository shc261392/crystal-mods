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
| **Necron production speed → ×2** (resource-cheat variant only, EXPERIMENTAL) | Human player only, while playing Necrons (build/research/reinforce time × ½) |
| **Ork waaagh economy — banner +4000 waaagh, cap 40001, waaagh growth ×2** (resource-cheat variant only) | Ork player only |
| **Ork waaagh pool cap → 40001** (`max_pop_cap`) | All ork games, both variants |

Covered campaigns: **Main campaign**, **Winter Assault**, **Dark Crusade (DXP2)**,
**Soulstorm (DXP3)**.

## Two variants (choose ONE)

The `dist/` folder ships two files that are identical except for the resource
cheat:

| ZIP | Resource cheat | Playstyle |
|---|---|---|
| `over-40000-v0.1.7.zip` | **On** — start with 40001 req/power, ×10 income | Full cheat: spam anything immediately |
| `over-40000-v0.1.7-normal-resources.zip` | **Off** — normal resources | Same 5x squads / caps / unlimited limits, but you earn resources normally |

Ork waaagh zip scoping: the waaagh pool cap (`max_pop_cap` → **40001**) ships in
**both** variants; the **+4000 waaagh per banner** value and the **×2 waaagh
growth** ship in the resource-cheat zip only. Ork waaagh reinforce costs are
floored at 1.0 in both.

## How it works (for maintainers)

- `W40k/Data/scar/setup.scar` — the cheat is **not** hooked via `Setup_Player`
  (that function only runs for scripted single-player missions). Instead the mod
  registers a one-shot rule for the human player (index 0) via `Scar_AddInit`,
  which runs for **every** battle (single-player missions *and* engine-driven
  multiplayer-map battles). ~1s after game init the rule applies per-player
  income modifiers (×10 requisition & power), sets requisition/power to 40001,
  and removes itself. The 2s `StartupTopup` rule re-sets the resources for the
  first ~60s so mission/meta-campaign resets don't clobber them. Because
  modifiers are applied with `Modifier_ApplyToPlayer`, **the computer never
  benefits**. Two battle types are excluded by the cheat guard:
  **skirmish Economic Victory** games and the **Dark Crusade "Gather Power"
  side mission** (`cl_vandea_coast`) — with the cheat their win conditions are
  trivially satisfied, so `Over40000_IsCheatSuppressed()` keeps the cheat off.
- **Necron production speed** (resource-cheat variant only) — when the human
  player's race is Necron, `Over40000_ApplyNecronProductionCheat` applies the
  three player time modifiers (`recruit_` / `research_` / `reinforce_time_player_modifier`)
  at ×0.5 (time × ½ ≈ 200% build speed). Tunable in the cheat template:
  1.0 = vanilla, 0.5 = 2×, 0.25 = 4×.
- **Ork waaagh economy** (resource-cheat variant only) — the ork waaagh
  banner's `population_cap_player_modifier` is raised from 10 to **4000** waaagh
  per banner, the race `max_pop_cap` is raised to **40001** (both variants), and
  the ork population-growth rate is **×2** so the waaagh pool fills fast enough
  to reach the raised cap.
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
make build            # -> dist/over-40000-v0.1.7.zip  (resource cheat on)
make build RESOURCE_CHEAT=0
                      # -> dist/over-40000-v0.1.7-normal-resources.zip
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
[`easy-reinforcement/`](../easy-reinforcement/README.md). Install it alongside
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
2. Drag `dist/over-40000-v0.1.7.zip` (or the `-normal-resources` variant) onto Vortex and **Install**.
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
- Play a **skirmish** game afterwards: the resource cheat applies there too
  (it runs via `Scar_AddInit`, for every battle type) — but start a skirmish
  game with the **Economic Victory** condition and confirm the cheat stays off,
  so an EC win can't be trivially satisfied.

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

- **Engine hard-caps squads at 30 models.** Any ×5-scaled squad whose scaled
  `unit_max` exceeds 30 is clamped to 30 by the engine in-game (observed:
  everything reads 30/30 even when the shipped data says 75 / 750). **74 squads**
  are affected; the full per-race enumeration is in
  [`docs/ENGINE_SQUAD_CAP_30.md`](docs/ENGINE_SQUAD_CAP_30.md).
- **Unit-limit overrides are data-wide.** The `required_squad_cap` change
  applies to AI players too (they can also field unlimited Terminators). This
  is inherent to how per-unit caps are stored.
- The unit-limit `.rgd` overrides are compiled data — they load exactly like
  vanilla `.rgd` files. Each is byte-identical to the base except the
  `max_squad_cap` values.
- The population/resource/income cheats are registered with `Scar_AddInit` in
  `W40k/Data/scar/setup.scar`, so they run for **every battle type** — campaign
  missions *and* skirmish / engine-driven multiplayer-map battles. **Exceptions:**
  skirmish **Economic Victory** games and the Dark Crusade **"Gather Power"
  side mission** (`cl_vandea_coast`) are excluded by the cheat guard, because
  their win conditions would be trivially satisfied by the cheat.

## Repository layout

```
over-40000/
├── Makefile                    # build / regenerate / lint / verify
├── pyproject.toml              # uv project (stdlib only)
├── modinfo.json                # mod metadata (not shipped in the zip)
├── README.md
├── docs/
│   ├── ENGINE_SQUAD_CAP_30.md   # 30-model engine cap — full per-race enumeration
│   └── SINGLE_MODEL_HONOR_GUARD.md
├── NEXUS_DESCRIPTION.md        # copy-paste text for the Nexus mod page
├── mod/                        # generated mod tree (the deliverable)
│   ├── W40k/Data/scar/setup.scar
│   ├── DXP2/Data/attrib/sbps/**/*.lua
│   └── DXP3/Data/attrib/sbps/**/*.lua
├── scripts/
│   ├── rgd_decode.py           # RGD (.rgd) binary decoder (Bob Jenkins hash)
│   ├── scan_squad_caps.py      # finds squad build-limit requirements
│   ├── generate_mod.py         # builds mod/ from an extraction tree
│   └── templates/              # setup.scar / setup.nocheat.scar cheat hooks, squads.blacklist.txt
└── dist/                       # build output (gitignored)
```

## Version history

- **0.1.7** — **skirmish/total-battle retrofit + ork waaagh economy**, plus the
  experimental **Necron production-speed cheat** (resource-cheat variant only).
  - **Cheat now applies to every battle type.** The resource cheat previously
    shipped a misleading "campaign-only" claim; it actually runs via
    `Scar_AddInit` and applies in skirmish and engine-driven multiplayer-map
    battles too. Two battle types are now explicitly **excluded** by the cheat
    guard (`Over40000_IsCheatSuppressed` via `scripts/templates/setup.scar`):
    **skirmish Economic Victory** games (win = reach resource goals, which the
    cheat would instantly satisfy) and the **Dark Crusade "Gather Power" side
    mission** (`cl_vandea_coast`, detected via its unique
    `Rule_Power_Count_Objective_Variation` load-time marker). No single
    `_EconVict`-style check covers both, so two markers are needed.
  - **Ork waaagh economy fixed** (checks against the ×5 squad counter-scale
    that divided waaagh reinforce costs to 0.2/0.4): reinforce-cost
    **population rows are floored at 1.0** in both variants; the waaagh
    **`max_pop_cap` is raised to 40001** in both variants; and in the
    resource-cheat variant the **waaagh banner grants +4000 pop cap per banner**
    (was 10 via `population_cap_player_modifier`) with **waaagh growth ×2**
    so the pool fills to the new cap in a few banners.
  - **Necron production speed**: when the human player plays Necrons, build /
    research / reinforce time is multiplied by ½ (~200% production speed) via
    the three player time modifiers. Applies to the human Necron player only —
    AI players and other races are unaffected. Tunable in
    `scripts/templates/setup.scar` (`Over40000_ApplyNecronProductionCheat`;
    1.0 = vanilla, 0.5 = 2×, 0.25 = 4×). **Note:** the ×2 (0.5) value replaced
    the original ×4 (0.25) in 0.1.7; the release zips in `dist/` are rebuilt
    from the retuned template.

- **0.1.6** — separate the cost counter-scale + attachable-leader fixes from the
  talos fix. **Cost counter-scale invariant fixed for 63 squads** across
  DXP2 (26) and DXP3 (37): their EBP build cost/time was previously **not**
  counter-scaled (a shared-EBP `_sp` variant zeroed the divisor via `min()`), so
  they built at 5× cost/time. Now `max()` is used and a unit test
  (`scripts/test_cost_counter_scale.py`, `make test`) enforces that every
  model-scaled squad's EBP divisor equals its scale. Fixed squads:

  **DXP2 (Dark Crusade) — 26:**
  chaos_squad_defiler, chaos_squad_khorne_berserker_stronghold_sp,
  chaos_squad_obliterator_stronghold_sp, chaos_squad_possessed_marine_stronghold_sp,
  eldar_squad_falcon_grav_tank, eldar_squad_grav_platform_brightlance,
  eldar_squad_wraithlord, guard_squad_chimera, guard_squad_enginseer,
  guard_squad_hellhound, guard_squad_sentinel, necron_destroyer_squad,
  necron_tomb_spyder_squad, ork_squad_killa_kan, ork_squad_trukk,
  ork_squad_wartrak, space_marine_squad_assault_veteran_stronghold_sp,
  space_marine_squad_dreadnought, space_marine_squad_dreadnought_hellfire,
  space_marine_squad_land_speeder,
  space_marine_squad_terminator_assault_veteran_stronghold_sp,
  space_marine_squad_terminator_veteran_stronghold_sp,
  space_marine_squad_veteran_stronghold_sp, tau_crisis_suit_squad,
  tau_drone_harbinger_squad, tau_skyray_squad.

  **DXP3 (Soulstorm) — 37:**
  chaos_squad_bloodthirster, chaos_squad_defiler,
  chaos_squad_khorne_berserker_stronghold_sp, chaos_squad_obliterator_stronghold_sp,
  chaos_squad_possessed_marine_stronghold_sp, chaos_squad_sorcerer,
  dark_eldar_squad_raider, eldar_harlequin_squad, eldar_squad_bonesinger,
  eldar_squad_falcon_grav_tank, eldar_squad_fire_prism,
  eldar_squad_grav_platform_brightlance, eldar_squad_vypers,
  eldar_squad_wraithlord, guard_squad_chimera, guard_squad_enginseer,
  guard_squad_hellhound, guard_squad_sentinel, necron_destroyer_squad,
  necron_tomb_spyder_squad, ork_squad_fighta_bomba, ork_squad_killa_kan,
  ork_squad_trukk, ork_squad_wartrak, sisters_squad_immolator_tank,
  space_marine_squad_assault_veteran_stronghold_sp, space_marine_squad_dreadnought,
  space_marine_squad_dreadnought_dxp3_nis, space_marine_squad_dreadnought_hellfire,
  space_marine_squad_dreadnought_hellfire_dxp3_nis,
  space_marine_squad_land_speeder,
  space_marine_squad_terminator_assault_veteran_stronghold_sp,
  space_marine_squad_terminator_veteran_stronghold_sp,
  space_marine_squad_veteran_stronghold_sp, tau_crisis_suit_squad,
  tau_drone_harbinger_squad, tau_skyray_squad.

  Also in 0.1.6: attachable leaders **Priest / Commissar / Psyker** are
  blacklisted from scaling so they stay 1-model and can attach.
- **0.1.5** — fix DE mission crash: the **Dark Eldar Talos** is permanently
  blacklisted from model-count scaling via a git-controlled blacklist file
  (`scripts/templates/squads.blacklist.txt`). Scaling it ×5 crashed the game
  with "Invalid command receiver detected for command type 24, receiver type 2"
  when the AI fielded it (e.g. Eldar vs Dark Eldar stronghold). The blacklist is
  applied by default in every build; pass `--blacklist-file PATH` to override
  with a different list. `make build` is deterministic.
- **0.1.4** — fix resource-cheat timing during opening cinematics. The cheat
  now waits for `Event_IsAnyRunning()` to be false (opening NIS finished) before
  applying the income/cap boost, instead of a fixed 1s one-shot that fired while
  the cinematic was still playing and got reset when the mission initialized.
  Works whether the cinematic is skipped at 1s or watched fully.
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
