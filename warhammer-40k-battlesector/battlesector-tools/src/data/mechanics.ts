// Seed content for the Game Mechanics reference page. Values are grounded in the
// shared combat formulas (src/lib/combat.ts) and the truth-notes in
// src/lib/tag-tooltips.ts. Copy is intentionally editable — refine over time.

export type MechanicCategory = 'combat' | 'defense' | 'movement' | 'resource';

export interface Mechanic {
  id: string;
  term: string;
  category: MechanicCategory;
  /** One-line summary shown in the card header. */
  summary: string;
  /** Detail bullet points. */
  details: string[];
  /** Extra keywords to match in search. */
  keywords?: string[];
}

export const MECHANIC_CATEGORY_LABEL: Record<MechanicCategory, string> = {
  combat: 'Combat',
  defense: 'Defense',
  movement: 'Movement',
  resource: 'Resource',
};

export const mechanics: Mechanic[] = [
  {
    id: 'critical',
    term: 'Critical',
    category: 'combat',
    summary: 'A boosted hit dealing 1.5× damage; chance scales with armour piercing over armour.',
    details: [
      'Critical chance = the weapon’s base critical chance + 5% for every point of Armour Piercing above the target’s effective armour.',
      'A critical hit deals 1.5× the rolled damage (a +50% bonus).',
      'Because AP-over-armour drives the bonus, high-AP weapons crit far more often against lightly-armoured targets.',
    ],
    keywords: ['crit', 'chance', 'multiplier', '1.5x', 'ap'],
  },
  {
    id: 'armor',
    term: 'Armor',
    category: 'defense',
    summary: 'Flat damage reduction subtracted from every hit.',
    details: [
      'Effective armour = max(0, unit armour − attacker Armour Piercing).',
      'The effective armour value is subtracted from each hit’s damage (both the minimum and maximum of the damage range).',
      'Vehicles/monsters can have directional armour (front/side/rear); the facing struck determines the value used.',
    ],
    keywords: ['armour', 'reduction', 'mitigation', 'directional'],
  },
  {
    id: 'armor-piercing',
    term: 'Armor Piercing',
    category: 'combat',
    summary: 'Reduces the target’s effective armour and fuels critical / suppresses graze.',
    details: [
      'Armour Piercing (AP) lowers effective armour to max(0, armour − AP), so more of each hit’s damage lands.',
      'AP above the target’s armour adds critical chance (+5% per point).',
      'AP also reduces graze chance (graze is driven by armour above AP).',
    ],
    keywords: ['ap', 'penetration', 'pierce'],
  },
  {
    id: 'graze',
    term: 'Graze',
    category: 'combat',
    summary: 'A glancing hit dealing only 0.25× damage; likelier against heavy armour.',
    details: [
      'Graze chance = 3% for every point of target armour above the weapon’s Armour Piercing.',
      'A graze deals 0.25× the rolled damage (a 75% reduction).',
      'Raising AP toward the target’s armour value shrinks graze chance and grows critical chance.',
    ],
    keywords: ['glance', 'reduced', '0.25x'],
  },
  {
    id: 'fallback',
    term: 'Fallback',
    category: 'movement',
    summary: 'Eligible units can disengage from melee instead of being pinned.',
    details: [
      'Units with the “Can Fall Back” data flag may retreat out of base contact with an enemy.',
      'Use it to reposition fragile ranged units that get charged, or to break a bad melee.',
      'Units without the flag are locked in melee until the engagement resolves.',
    ],
    keywords: ['fall back', 'retreat', 'disengage', 'melee'],
  },
  {
    id: 'pistol-reaction',
    term: 'Pistol Reaction',
    category: 'combat',
    summary: 'Pistol weapons can fire in melee and react to adjacent enemies.',
    details: [
      'Weapons flagged as Pistol may be used while in melee, unlike other ranged weapons.',
      'This lets a model contribute ranged damage even when locked in base contact.',
      'Pistols therefore double as melee-viable sidearms on many loadouts.',
    ],
    keywords: ['pistol', 'react', 'reaction', 'melee'],
  },
  {
    id: 'charge-attack',
    term: 'Charge Attack',
    category: 'combat',
    summary: 'Moving into melee contact triggers a charge with attack bonuses.',
    details: [
      'Closing the distance into base contact lets a unit make a charge (melee) attack.',
      'Charging units gain the initiative of striking as they engage.',
      'Pair charges with high-momentum turns and melee buffs for maximum impact.',
    ],
    keywords: ['charge', 'melee', 'assault'],
  },
  {
    id: 'momentum',
    term: 'Momentum',
    category: 'resource',
    summary: 'A faction resource earned from kills that powers faction passives.',
    details: [
      'Momentum builds up over the battle — each unit contributes momentum when its models die (per-model value).',
      'The current momentum total feeds each faction’s passive (e.g. scaling critical chance, damage, or armour piercing).',
      'See a unit’s detail page and the calculator’s momentum slider to preview passive effects at a given momentum.',
    ],
    keywords: ['momentum', '勢能', 'passive', 'faction', 'resource'],
  },
];
