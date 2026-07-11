// Reference content for the Game Mechanics page.
//
// GROUND-TRUTH POLICY: entries state only facts derived from extracted game
// data — the combat constants in src/lib/combat.ts (from the decompiled
// DamageCalculationConfig) and the literal data flags/buff strings in the unit
// and hq-upgrade data. Mechanics whose exact rules are not yet extracted say so
// explicitly rather than inferring behaviour. Do not add tactical advice or
// inferred explanations without ground truth.

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
      'A critical hit deals 1.5× the rolled damage.',
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
      'Some units use directional armour (front / left / right / rear); the facing struck determines the value used.',
    ],
    keywords: ['armour', 'reduction', 'mitigation', 'directional'],
  },
  {
    id: 'armor-piercing',
    term: 'Armor Piercing',
    category: 'combat',
    summary: 'Reduces the target’s effective armour and drives critical / graze chance.',
    details: [
      'Armour Piercing (AP) lowers effective armour to max(0, armour − AP).',
      'AP above the target’s armour adds critical chance (+5% per point).',
      'Armour above AP adds graze chance (+3% per point).',
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
      'A graze deals 0.25× the rolled damage.',
    ],
    keywords: ['glance', 'reduced', '0.25x'],
  },
  {
    id: 'fallback',
    term: 'Fallback',
    category: 'movement',
    summary: 'A unit data flag governing whether a unit can disengage from melee.',
    details: [
      'Units carry a “Can Fall Back” flag in the game data.',
      'Exact fall-back rules are not yet extracted from game data.',
    ],
    keywords: ['fall back', 'retreat', 'disengage', 'melee'],
  },
  {
    id: 'pistol-reaction',
    term: 'Pistol Reaction',
    category: 'combat',
    summary: 'A reaction mechanic referenced in the game data.',
    details: [
      'Weapons carry a “Pistol” flag, and units carry a melee-reaction flag in the game data.',
      'The game data references a pistol charge reaction (the “IgnorePistolChargeReaction” buff).',
      'The exact rules for this reaction are not yet extracted from game data.',
    ],
    keywords: ['pistol', 'react', 'reaction', 'melee'],
  },
  {
    id: 'charge-attack',
    term: 'Charge Attack',
    category: 'combat',
    summary: 'A charge mechanic referenced in the game data.',
    details: [
      'The game data references a charge reaction (the “IgnorePistolChargeReaction” buff).',
      'The exact charge rules and bonuses are not yet extracted from game data.',
    ],
    keywords: ['charge', 'melee', 'assault'],
  },
  {
    id: 'momentum',
    term: 'Momentum',
    category: 'resource',
    summary: 'A faction resource earned from model deaths that powers faction passives.',
    details: [
      'Each unit has a per-model momentum value (momentumPerModelDeath) contributed when its models die.',
      'The current momentum total feeds each faction’s passive effect.',
    ],
    keywords: ['momentum', '勢能', 'passive', 'faction', 'resource'],
  },
];
