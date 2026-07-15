// Shared domain types for Battlesector game data.
// These mirror the structure produced by the data extraction pipeline.

/** Attack-delivery classification shown to players. */
export type WeaponType = 'melee' | 'ballistic' | 'flame' | 'artillery';

export interface WeaponOption {
  weaponId: number;
  name: string;
  pointCost: number;
  startsLocked: boolean;
}

export interface WeaponSlot {
  options: WeaponOption[];
}

export interface Unit {
  id: number;
  name: string;
  faction: number;
  factionName: string;
  role: number;
  roleName: string;
  roleColor: string;
  substance: number;
  substanceName: string;
  pointCost: number;
  members: number;
  maxHealth: number;
  totalHealth: number;
  evasion: number;
  armorProfile: number;
  armor: number;
  armorFront: number;
  armorLeft: number;
  armorRight: number;
  armorRear: number;
  meleeAccuracy: number;
  rangedAccuracyModifier: number;
  maxActionPoints: number;
  maxMovementPoints: number;
  momentumPerModelDeath: number;
  unitHeight: number;
  isLarge: boolean;
  campaignOnly?: boolean;
  portrait?: string;
  canMeleeReact: boolean;
  canFallback: boolean;
  activationRange: number;
  awarenessRange: number;
  weaponSlots: WeaponSlot[];
  abilityIds: number[];
  /** Player field-test note (not in game data). Curated locally via the editor. */
  notes?: string;
  /** When true, the unit is excluded from the public site (editor-only). */
  hidden?: boolean;
}

export interface Weapon {
  id: number;
  name: string;
  damage: number;
  accuracy: number;
  numAttacks: number;
  shotsPerAttack: number;
  burstSize: number;
  armorPiercing: number;
  isMelee: boolean;
  isRanged: boolean;
  /** Player-facing attack classification. Defaults from isMelee when absent. */
  weaponType?: WeaponType;
  rangeMin: number;
  rangeOptimal: number;
  rangeMax: number;
  accuracyFalloff: number;
  damageFalloff: number;
  ignoresRangePenalty: boolean;
  icon?: string;
  pistol?: boolean;
  impactType?: 'single' | 'tile' | 'splash';
  splashModels?: number;
  splashFalloff?: number;
  splashHeavyAll?: boolean;
  /** Explicit splash damage range. When unset, derived from damage + splashFalloff. */
  splashMin?: number;
  splashMax?: number;
  targetType?: 'fixedPerMember' | 'fixedEntireUnit';
  /** Curated descriptive text (not in extracted game data). Editable locally. */
  description?: string;
  /** Player field-test note (not in game data). Curated locally via the editor. */
  notes?: string;
  /** When true, the weapon is excluded from the public site (editor-only). */
  hidden?: boolean;
  /** Weapon abilities (extracted from game data, optional). */
  abilities?: Array<{ Ability: number; StartsLocked: number }>;
}

export interface Faction {
  id: number;
  name: string;
  slogan: string;
}

export interface Role {
  id: number;
  name: string;
  color: string;
  sort: number;
}

export interface Summary {
  unitCount: number;
  weaponCount: number;
  factionCount: number;
  factions: string[];
  maxDamage: number;
  maxHealth: number;
  maxPoints: number;
}

export interface LocaleInfo {
  code: string;
  label: string;
  native: string;
}

export interface I18nBundle {
  locales: LocaleInfo[];
  ui: Record<string, Record<string, string>>;
  unitNames: Record<string, Record<string, string>>;
  weaponNames: Record<string, Record<string, string>>;
  factionNames: Record<string, Record<string, string>>;
  roleNames: Record<string, Record<string, string>>;
}
