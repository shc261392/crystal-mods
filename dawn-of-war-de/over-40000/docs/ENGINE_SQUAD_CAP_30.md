# Engine 30-model squad-size cap — every ×5 squad that is clamped

## What this documents

When squads are model-count scaled, the shipped `.rgd` data contains the **scaled**
values (the generator writes them correctly and byte-identically to the base file
except the `unit_min` / `unit_max` floats). In-game, however, no squad can exceed
**30 models per squad**: every unit whose scaled value would go past 30 is clamped
to 30 by the engine. In-game testing observed **30/30 everywhere** — even for a
necro test build whose data had `unit_min`/`unit_max` = 250/750.

**Verified facts**

- The experiment zip `over-40000-exp-spyder-x1-scarab-x50.zip` provably contains
  `unit_min`/`unit_max` = **250/750** in `necron_scarab_squad.rgd` (DXP2 + DXP3)
  and `necron_scarab_no_flyer_squad.rgd` — yet the in-game assault scarab displays
  **30/30**. The clamp is therefore not in the mod's data.
- No **vanilla** squad in any module has `unit_max` > 15 (surveyed W40k: 91, WXP:
  89, DXP2: 263, DXP3: 423 squad files). So a limit of 30 was unreachable by
  vanilla content and is undocumented in the community knowledge base.
- The formation hardpoint table (45 slots under `7c408388`) and the
  `squad_loadout_ext` table structure are byte-structurally identical between the
  assault scarab and the necron warrior, so the clamp source is not in the shipped
  squad data.

**Hypothesis (NOT yet proven)** — the DoW DE engine hard-clamps per-squad model
count at 30 at runtime. The DE build is the same ancient single-core engine
recompiled to 64-bit (32-bit internals), and community reports say squads near
~30 models behave at the practical engine ceiling ("movement and placement of
certain squads will be broken at times"). No modding documentation of a hard
30-model cap was found. This enumeration therefore documents the **observed
behavior** (capped at 30) without claiming the mechanism.

## What this means for the mod

The canonical release build (`--squad-scale 5`) writes these **scaled** values into
the zips, but the engine will never display / run more than **30 models per squad**.
Any `scaled max > 30` effectively behaves as 30.

| Summary | Count |
|---|---|
| Squad files scaled ×5 (across all modules, deduped by basename) | 277 |
| Scaled max ≤ 30 (unaffected) | 203 |
| Scaled max > 30 → **engine-clamped to 30** | **74** |
| …of which scaled min also > 30 (spawns already at 30/30, marked ⚠) | 20 |

Effective in-game behavior for a clamped squad:

- `scaled max > 30` → shows **max 30**.
- `scaled min > 30` (⚠) → spawns at **30** immediately; the min/max display is
  30/30 from the start.
- Otherwise the squad spawns at its scaled min (≤ 30) and reinforces toward 30.

## Per-race enumeration (vanilla → ×5; module = highest-priority copy shipped)

`Module` is the highest-priority module the squad ships in (load order
DXP3 > DXP2 > WXP > W40k). `ships in` lists every module carrying the same squad
file. All values are the raw floats from the game data (`unit_min`, `unit_max`).

| Race | Squad (basename `.rgd`) | Module | vanilla min | scaled min | vanilla max | scaled max | ships in |
|---|---|---|---|---|---|---|---|
| chaos | `chaos_marine_squad` | DXP3 | 4 | 20 | 10 | 50 | W40k,WXP,DXP2,DXP3 |
| chaos | `chaos_marine_squad_sp_dxp3_prisoner` ⚠ | DXP3 | 10 | 50 | 10 | 50 | DXP3 |
| chaos | `chaos_marine_squad_stronghold_sp` | DXP3 | 4 | 20 | 10 | 50 | DXP2,DXP3 |
| chaos | `chaos_squad_cultist` | DXP3 | 4 | 20 | 10 | 50 | W40k,WXP,DXP2,DXP3 |
| chaos | `chaos_squad_cultist_sp_dxp3_prisoner` ⚠ | DXP3 | 10 | 50 | 10 | 50 | DXP3 |
| chaos | `chaos_squad_possessed_marine` | DXP3 | 4 | 20 | 10 | 50 | W40k,WXP,DXP2,DXP3 |
| chaos | `chaos_squad_possessed_marine_stronghold_sp` | DXP3 | 4 | 20 | 10 | 50 | DXP2,DXP3 |
| chaos | `chaos_squad_raptor` | DXP3 | 4 | 20 | 10 | 50 | W40k,WXP,DXP2,DXP3 |
| chaos | `chaos_squad_raptor_stronghold_sp` | DXP3 | 4 | 20 | 10 | 50 | DXP2,DXP3 |
| chaos | `chaos_squad_khorne_berserker` | DXP3 | 4 | 20 | 8 | 40 | WXP,DXP2,DXP3 |
| chaos | `chaos_squad_khorne_berserker_sp_dxp3_prisoner` ⚠ | DXP3 | 8 | 40 | 8 | 40 | DXP3 |
| chaos | `chaos_squad_khorne_berserker_stronghold_sp` | DXP3 | 4 | 20 | 8 | 40 | DXP2,DXP3 |
| chaos | `chaos_squad_cultist_advance_sp` ⚠ | DXP3 | 7 | 35 | 7 | 35 | DXP2,DXP3 |
| dark_eldar | `dark_eldar_squad_wych` | DXP3 | 4 | 20 | 7 | 35 | DXP3 |
| dark_eldar | `dark_eldar_squad_wych_sp_dxp3_prisoner` ⚠ | DXP3 | 7 | 35 | 7 | 35 | DXP3 |
| eldar | `eldar_guardian_squad` | DXP3 | 4 | 20 | 9 | 45 | W40k,WXP,DXP2,DXP3 |
| eldar | `eldar_guardian_squad_sp_dxp3_prisoner` ⚠ | DXP3 | 9 | 45 | 9 | 45 | DXP3 |
| eldar | `eldar_squad_banshees` | DXP3 | 4 | 20 | 9 | 45 | W40k,WXP,DXP2,DXP3 |
| eldar | `eldar_squad_banshees_sp_dxp3_prisoner` ⚠ | DXP3 | 9 | 45 | 9 | 45 | DXP3 |
| eldar | `eldar_squad_seer_council` | DXP3 | 3 | 15 | 9 | 45 | W40k,WXP,DXP2,DXP3 |
| eldar | `eldar_squad_seer_council_advance_sp` | DXP3 | 3 | 15 | 9 | 45 | DXP2,DXP3 |
| eldar | `eldar_squad_rangers` | DXP3 | 5 | 25 | 8 | 40 | W40k,WXP,DXP2,DXP3 |
| eldar | `eldar_squad_warp_spider` | DXP3 | 4 | 20 | 8 | 40 | W40k,WXP,DXP2,DXP3 |
| eldar | `eldar_squad_warp_spider_sp_dxp3` | DXP3 | 4 | 20 | 8 | 40 | DXP3 |
| eldar | `eldar_squad_warp_spider_stronghold_sp` | DXP3 | 4 | 20 | 8 | 40 | DXP2,DXP3 |
| guard | `guard_squad_guardsmen` | DXP3 | 5 | 25 | 9 | 45 | WXP,DXP2,DXP3 |
| guard | `guard_squad_guardsmen_advance_sp` ⚠ | DXP3 | 9 | 45 | 9 | 45 | DXP2,DXP3 |
| guard | `guard_squad_guardsmen_sp_dxp3_prisoner` ⚠ | DXP3 | 9 | 45 | 9 | 45 | DXP3 |
| guard | `guard_squad_kasrkin` | DXP3 | 5 | 25 | 9 | 45 | WXP,DXP2,DXP3 |
| guard | `guard_squad_kasrkin_sp_dxp3_prisoner` ⚠ | DXP3 | 9 | 45 | 9 | 45 | DXP3 |
| necrons | `necron_scarab_no_flyer_squad` | DXP3 | 5 | 25 | 15 | 75 | DXP3 |
| necrons | `necron_scarab_squad` | DXP3 | 5 | 25 | 15 | 75 | DXP2,DXP3 |
| necrons | `necron_basic_warrior_squad` | DXP3 | 3 | 15 | 8 | 40 | DXP2,DXP3 |
| necrons | `necron_basic_warrior_squad_dxp3_sp` | DXP3 | 3 | 15 | 8 | 40 | DXP3 |
| necrons | `necron_basic_warrior_squad_sp_dxp3_prisoner` ⚠ | DXP3 | 8 | 40 | 8 | 40 | DXP3 |
| necrons | `necron_flayed_one_squad` | DXP3 | 4 | 20 | 8 | 40 | DXP2,DXP3 |
| necrons | `necron_pariah_squad` | DXP3 | 4 | 20 | 8 | 40 | DXP2,DXP3 |
| necrons | `necron_pariah_squad_sp_dxp3_prisoner` ⚠ | DXP3 | 8 | 40 | 8 | 40 | DXP3 |
| npc | `guard_squad_soldier` | W40k | 5 | 25 | 15 | 75 | W40k |
| npc | `guard_squad_soldier_coward` | W40k | 5 | 25 | 15 | 75 | W40k |
| npc | `npc_necron_warrior` | DXP3 | 4 | 20 | 10 | 50 | WXP,DXP2,DXP3 |
| orks | `ork_squad_slugga` | DXP3 | 4 | 20 | 15 | 75 | W40k,WXP,DXP2,DXP3 |
| orks | `ork_squad_slugga_sp_dxp3_prisoner` ⚠ | DXP3 | 15 | 75 | 15 | 75 | DXP3 |
| orks | `ork_squad_stormboy` | DXP3 | 4 | 20 | 15 | 75 | W40k,WXP,DXP2,DXP3 |
| orks | `ork_squad_nob` | DXP3 | 5 | 25 | 10 | 50 | W40k,WXP,DXP2,DXP3 |
| orks | `ork_squad_nob_sp_dxp3_prisoner` ⚠ | DXP3 | 10 | 50 | 10 | 50 | DXP3 |
| orks | `ork_squad_shoota_boy` | DXP3 | 4 | 20 | 8 | 40 | W40k,WXP,DXP2,DXP3 |
| orks | `ork_squad_shoota_boy_sp_dxp3_prisoner` ⚠ | DXP3 | 8 | 40 | 8 | 40 | DXP3 |
| orks | `ork_flash_gitz_squad` | DXP3 | 3 | 15 | 7 | 35 | DXP2,DXP3 |
| sisters | `sisters_squad_battle_sister` | DXP3 | 4 | 20 | 10 | 50 | DXP3 |
| sisters | `sisters_squad_battle_sister_sp_dxp3_prisoner` ⚠ | DXP3 | 8 | 40 | 10 | 50 | DXP3 |
| sisters | `sisters_squad_seraphim` | DXP3 | 4 | 20 | 8 | 40 | DXP3 |
| sisters | `sisters_squad_seraphim_sp_dxp3` | DXP3 | 4 | 20 | 8 | 40 | DXP3 |
| sisters | `sisters_squad_repentia` | DXP3 | 4 | 20 | 7 | 35 | DXP3 |
| sisters | `sisters_squad_repentia_sp_dxp3_prisoner` | DXP3 | 6 | 30 | 7 | 35 | DXP3 |
| space_marines | `space_marine_squad_assault` | DXP3 | 4 | 20 | 8 | 40 | W40k,WXP,DXP2,DXP3 |
| space_marines | `space_marine_squad_assault_sp` | W40k | 4 | 20 | 8 | 40 | W40k |
| space_marines | `space_marine_squad_assault_sp_dxp3` | DXP3 | 4 | 20 | 8 | 40 | DXP3 |
| space_marines | `space_marine_squad_assault_veteran_stronghold_sp` | DXP3 | 4 | 20 | 8 | 40 | DXP2,DXP3 |
| space_marines | `space_marine_squad_sp_dxp3_prisoner` ⚠ | DXP3 | 8 | 40 | 8 | 40 | DXP3 |
| space_marines | `space_marine_squad_tactical` | DXP3 | 4 | 20 | 8 | 40 | W40k,WXP,DXP2,DXP3 |
| space_marines | `space_marine_squad_tactical_dxp3_nis` | DXP3 | 4 | 20 | 8 | 40 | DXP3 |
| space_marines | `space_marine_squad_terminator` | DXP3 | 4 | 20 | 8 | 40 | W40k,WXP,DXP2,DXP3 |
| space_marines | `space_marine_squad_terminator_assault` | DXP3 | 4 | 20 | 8 | 40 | W40k,WXP,DXP2,DXP3 |
| space_marines | `space_marine_squad_terminator_assault_veteran_stronghold_sp` | DXP3 | 4 | 20 | 8 | 40 | DXP2,DXP3 |
| space_marines | `space_marine_squad_terminator_veteran_sp_dxp3_prisoner` ⚠ | DXP3 | 8 | 40 | 8 | 40 | DXP3 |
| space_marines | `space_marine_squad_terminator_veteran_stronghold_sp` | DXP3 | 4 | 20 | 8 | 40 | DXP2,DXP3 |
| space_marines | `space_marine_squad_veteran_stronghold_sp` | DXP3 | 4 | 20 | 8 | 40 | DXP2,DXP3 |
| tau | `tau_kroot_alpha_squad_sp_dxp3_prisoner` ⚠ | DXP3 | 10 | 50 | 10 | 50 | DXP3 |
| tau | `tau_kroot_carnivore_squad` | DXP3 | 4 | 20 | 10 | 50 | DXP2,DXP3 |
| tau | `tau_kroot_carnivore_squad_clone_sp` | DXP3 | 4 | 20 | 10 | 50 | DXP2,DXP3 |
| tau | `tau_kroot_hound_squad` | DXP3 | 4 | 20 | 8 | 40 | DXP2,DXP3 |
| tau | `tau_kroot_hound_squad_clone_sp` | DXP3 | 4 | 20 | 8 | 40 | DXP2,DXP3 |
| tau | `tau_kroot_hound_squad_sp_dxp3_prisoner` ⚠ | DXP3 | 8 | 40 | 8 | 40 | DXP3 |

> `⚠` = scaled min > 30: the squad spawns already capped at 30/30 (never even
> starts below the cap).

Per-race breakdown of the **74** affected squads: chaos 13 · dark_eldar 2 ·
eldar 10 · guard 5 · necrons 8 · npc 3 · orks 8 · sisters 6 · space_marines 13 ·
tau 6. (20 are ⚠ min-capped, 54 reinforce to 30 from below.)

## Necron experiment decisions

- **Tomb Spyder** (`necron_tomb_spyder_squad`, `necron_tomb_spyder_no_flyer_squad`):
  keep at **×1** (1/1 vanilla, scale override `0`). Unaffected by the 30-cap
  (it is a single-model squad, never scaled).
- **Assault Scarab** (`necron_scarab_squad`, `necron_scarab_no_flyer_squad`): set
  to **just enough to reach the cap** → **×2**: vanilla 5→15 becomes **10/30**
  (`unit_min` 10, `unit_max` 30). Scale override factor `2`. This deliberately
  and exactly hits the 30-model engine ceiling instead of the ×5 value (25/75,
  which the engine clamps to 30 anyway) — no wasted data that can't run.

  Experiment invocation (experimental build only, never a formal release):

  ```
  python3 scripts/generate_mod.py ../.copilot_workspace/extract mod \
      --squad-scale 5 --resource-cheat on \
      --exclude-single-model on --descale-campaign-single on \
      --scale-overrides "necron_tomb_spyder_squad=0,necron_tomb_spyder_no_flyer_squad=0,necron_scarab_squad=2,necron_scarab_no_flyer_squad=2"
  ```

## How this table was produced

Read direct from the extracted game data (`DXP2/`, `DXP3/`, `WXP/`, `W40k/`)
using the same `collect_scale_maps(..., 5, "scale", exclude_single_model=True,
descale_campaign_single=True, exclude_squads=<default blacklist>)` logic the
canonical `make build` uses, then `unit_min`/`unit_max` floats are read from each
shipped squad file (raw-file view, `AEGD_OFF + field_offset`). Squads are deduped
by basename across modules and reported at their highest-priority module.
Reproducible for any extraction tree; re-run the scratch enumerator
(`.copilot_workspace/enumerate_engine30.py`) and re-verify the diffs before
updating this table.