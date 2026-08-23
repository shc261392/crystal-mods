# Single-model campaign variants not scaled in DC/SS

## What this documents

In DXP2/DXP3, **single-model squads whose name carries a campaign-only marker
are NOT model-count scaled** by `--descale-campaign-single`. These are the
campaign army / honor-guard variants spawned at mission start with min loadout;
scaling them freezes the SIM (e.g. Wraithlord HG in the Tau Stronghold mission).

**Name markers** (token-boundary match; `_sp`/`_advance_sp`/`_veteran_sp` at end
of name or as a component, `_hg` / `_hg_<module>` variants):

- `_advance_sp`  (e.g. `eldar_squad_wraithlord_advance_sp`)
- `_sp`          (e.g. `space_marine_squad_veteran_sp`, `dark_eldar_squad_raider_sp_dxp3`)
- `_veteran_sp`  (e.g. `space_marine_squad_terminator_veteran_sp`)
- `_hg`          (e.g. `sisters_squad_immolator_hg_dxp3`, `tau_broadside_battlesuit_squad_hg_dxp3`)

Skirmish single-model units are NOT matched (mid-word `_sp` like `land_speeder`,
`tomb_spyder` is excluded) and still scale ×5. Multi-model campaign variants
(e.g. `sisters_squad_battle_sister_hg_dxp3` unit_max 6) still scale ×5.

The honor-guard pool itself is predefined in `scenarios/sp/races/<race>_race.race`
under **`BonusSquadCosts`** (the engine's `MetaMap_GetRaceStartingSquadsList`
reads it). NOTE: `ReinforcementSquads` in the same files is a different list
(purchasable reinforcements spawned on-map), NOT honor guards.

## Dark Crusade (DXP2) — single-model campaign variants (33 in BonusSquadCosts)

- chaos_squad_defiler_advance_sp
- chaos_squad_aspiring_champion_advance_sp
- chaos_squad_raptor_champion_advance_sp
- chaos_squad_khorne_berserker_advance_sp
- chaos_squad_possessed_marine_advance_sp
- chaos_squad_obliterator_advance_sp
- chaos_squad_sorcerer_advance_sp
- eldar_squad_vypers_advance_sp
- eldar_squad_wraithlord_advance_sp
- guard_squad_sentinel_advance_sp
- guard_squad_assassin_advance_sp
- guard_squad_hellhound_advance_sp
- guard_squad_commissar_advance_sp
- guard_squad_psyker_advance_sp
- necron_destroyer_squad_advance_sp
- necron_tomb_spyder_squad_advance_sp
- necron_wraith_squad_advance_sp
- ork_squad_killa_kan_advance_sp
- ork_squad_wartrak_advance_sp
- ork_squad_bad_dok_advance_sp
- ork_squad_armored_nob_advance_sp
- space_marine_squad_dreadnought_advance_sp
- space_marine_squad_assault_veteran_sp
- space_marine_squad_chaplain_advance_sp
- space_marine_squad_dreadnought_hellfire_advance_sp
- space_marine_squad_land_speeder_advance_sp
- space_marine_squad_librarian_advance_sp
- space_marine_squad_terminator_veteran_sp
- space_marine_squad_terminator_assault_veteran_sp
- space_marine_squad_veteran_sp
- tau_skyray_squad_advance_sp
- tau_honor_guard_crisis_suit_squad_advance_sp
- tau_kroot_shaper_squad_advance_sp

(33 single-model honor guard squads in DXP2)

## Soulstorm (DXP3)

Single-model honor guards from `BonusSquadCosts`, resolved to their squad .rgd
(vanilla unit_max == 1.0):

- chaos_squad_aspiring_champion_advance_sp
- chaos_squad_raptor_champion_advance_sp
- chaos_squad_khorne_berserker_advance_sp
- chaos_squad_obliterator_advance_sp
- chaos_squad_possessed_marine_advance_sp
- chaos_squad_sorcerer_advance_sp
- chaos_squad_defiler_advance_sp
- dark_eldar_squad_warp_beast_hg_dxp3
- dark_eldar_squad_haemonculus_hg_dxp3
- dark_eldar_squad_reaver_hg_dxp3
- dark_eldar_squad_raider_hg_dxp3
- sp_eldar_banshee_exarch_squad
- eldar_harlequin_squad_hg_dxp3
- eldar_squad_vypers_advance_sp
- eldar_squad_wraithlord_advance_sp
- guard_squad_enginseer_advance_sp
- guard_heavy_weapons_team_squad_hg_dxp3
- guard_squad_assassin_advance_sp
- guard_squad_psyker_advance_sp
- guard_squad_commissar_advance_sp
- guard_squad_sentinel_advance_sp
- guard_squad_hellhound_advance_sp
- necron_wraith_squad_advance_sp
- necron_destroyer_squad_advance_sp
- necron_tomb_spyder_squad_advance_sp
- ork_squad_bad_dok_advance_sp
- ork_squad_armored_nob_advance_sp
- ork_squad_mek_boy_advance_sp
- ork_squad_wartrak_advance_sp
- ork_squad_killa_kan_advance_sp
- sisters_squad_servitor_hg_dxp3
- sisters_squad_missionary_hg_dxp3
- sisters_squad_veteran_superior_hg_dxp3
- sisters_squad_assassin_hg_dxp3
- sisters_squad_confessor_hg_dxp3
- sisters_squad_immolator_hg_dxp3
- space_marine_squad_veteran_sp
- space_marine_squad_assault_veteran_sp
- space_marine_squad_terminator_assault_veteran_sp
- space_marine_squad_apothecary_veteran_stronghold_sp
- space_marine_squad_librarian_advance_sp
- space_marine_squad_land_speeder_advance_sp
- space_marine_squad_dreadnought_advance_sp
- space_marine_squad_dreadnought_hellfire_advance_sp
- tau_honor_guard_crisis_suit_squad_advance_sp
- tau_kroot_shaper_squad_advance_sp
- tau_skyray_squad_advance_sp
- tau_broadside_battlesuit_squad_hg_dxp3

(48 single-model honor guard squads in DXP3)

## Notes / resolution details

- Honor Guard entries in `BonusSquadCosts` are blueprint names without a `.rgd`
  suffix; they resolve to `attrib/sbps/races/<race>/<blueprint>.rgd` in the same
  module.
- Two BonusSquadCosts entries have no matching squad file in the module data
  (`dark_eldar_squad_warrior_hg_dxp3`, `dark_eldar_squad_hellion_hg_dxp3`) and
  are ignored (not single-model issues).
- `space_marine_squad_assault_sp` (DXP2 BonusSquadCosts) resolves to the W40k
  module file; it is single-model there but is a base-game squad covered by the
  W40k/WXP single-model exclusion.
- These are the ONLY single-model honor guard units. Any squad not in a race's
  BonusSquadCosts table cannot be selected as Honor Guard.