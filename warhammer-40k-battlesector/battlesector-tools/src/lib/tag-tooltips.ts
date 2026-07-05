// Truth-grounded tooltip copy for gameplay tags.
// Sources:
// - docs/game-mechanics.md (melee/ranged classification, pistol, splash, AP)
// - src/lib/combat.ts (AP/armor crit+graze relationship)
// - extracted unit fields (isLarge, canMeleeReact, canFallback)

export const UNIT_TAG_TOOLTIPS = {
  hq: 'Role tag from unit data: HQ unit.',
  large:
    'Large units are vehicles/monsters with a bigger footprint. In-game they are easier to hit into melee and can block line/flamer attacks.',
  substance:
    'Unit substance/category extracted from the game data. This is shown verbatim so you can spot Vehicle, Infantry, Daemon/Other, and similar classifications.',
  vehicle:
    'Unit substance is Vehicle: this is a vehicle-type unit and uses the large-unit rules that come with that classification.',
  campaignOnly:
    'This unit is flagged as campaign-only and may not be available in skirmish/multiplayer lists.',
  meleeReaction:
    'Data flag `canMeleeReact` is enabled: this unit can perform melee reaction attacks.',
  fallback: 'Data flag `canFallback` is enabled: this unit can disengage/fall back.',
} as const;

export const WEAPON_TAG_TOOLTIPS = {
  melee:
    'Classified from weapon data: melee when MaximumRange ≤ 1.5 and weapon is not flagged as Pistol.',
  ranged: 'Classified from weapon data: ranged when MaximumRange ≥ 2, or when flagged as Pistol.',
  ballistic: 'Ranged weapon that fires solid projectiles (bolt, las, plasma, etc.).',
  flame: 'Ranged weapon that projects flame — hits models in a template rather than a single line.',
  artillery: 'Long-range indirect-fire weapon, typically with area-of-effect splash.',
  pistol: 'WeaponData.Pistol = true: this ranged weapon can be used in melee.',
  splash:
    'ImpactType = Splash: each hit affects a primary target plus additional models (secondary damage reduced by falloff).',
  tile: 'ImpactType = Tile: each hit damages all models in the target unit.',
  ap: 'Armor mitigation uses effective armor (armor − AP, min 0). AP also affects crit/graze: +5% crit per AP above armor, and +3% graze per armor above AP.',
} as const;
