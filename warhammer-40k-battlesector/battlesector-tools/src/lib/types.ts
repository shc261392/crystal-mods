// Shared domain types for Battlesector game data.
// These mirror the structure produced by the data extraction pipeline.

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
  canMeleeReact: boolean;
  canFallback: boolean;
  activationRange: number;
  awarenessRange: number;
  weaponSlots: WeaponSlot[];
  abilityIds: number[];
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
