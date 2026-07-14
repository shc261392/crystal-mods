// Display metadata for weapon attack types. Shared by the weapons index,
// weapon detail page, unit loadout, and the weapon stat zone so the label,
// colour, and i18n key stay consistent everywhere.

import { critChance, damageRangeAfterArmor, expectedDamagePerHit, grazeChance } from './combat';
import type { Weapon, WeaponType } from './types';

interface WeaponTypeMeta {
  type: WeaponType;
  /** English fallback label. */
  label: string;
  /** i18n UI key (falls back to English). */
  i18nKey: string;
  /** CSS colour variable for the type accent. */
  color: string;
}

const META: Record<WeaponType, WeaponTypeMeta> = {
  melee: { type: 'melee', label: 'Melee', i18nKey: 'common.melee', color: 'var(--color-blood)' },
  ballistic: {
    type: 'ballistic',
    label: 'Ballistic',
    i18nKey: 'common.ballistic',
    color: 'var(--color-plasma)',
  },
  flame: { type: 'flame', label: 'Flame', i18nKey: 'common.flame', color: 'var(--color-toxin)' },
  artillery: {
    type: 'artillery',
    label: 'Artillery',
    i18nKey: 'common.artillery',
    color: 'var(--color-momentum)',
  },
};

/** Resolve a weapon's effective type, defaulting from the legacy isMelee flag. */
export function resolveWeaponType(weapon: Pick<Weapon, 'weaponType' | 'isMelee'>): WeaponType {
  return weapon.weaponType ?? (weapon.isMelee ? 'melee' : 'ballistic');
}

// Names that identify flame weapons (same heuristic as the stat-ranks script,
// since weaponType is not present in the extracted data).
const FLAME_RE = /flame|flamer|burna|incinerat|immolat|inferno|skorcha|conflagrat/i;
// Names/impacts that identify artillery (indirect-fire / blast) weapons.
const ARTILLERY_RE =
  /mortar|earthshaker|bombard|whirlwind|basilisk|manticore|deathstrike|battle cannon|siege|demolisher|artiller|thunderfire|griffon|wyvern/i;

/**
 * Best-effort weapon class for display + filtering: melee / flame / artillery /
 * ballistic. NOTE: `lib/data.ts` normalizes `weaponType` to only melee/ballistic
 * (the source data has none), so we must NOT trust a melee/ballistic weaponType
 * here — only an explicit flame/artillery one. Everything else is derived:
 * melee from isMelee, flame from the name, artillery from tile (blast) impact or
 * an artillery name, and ballistic otherwise.
 */
export function weaponClass(
  weapon: Pick<Weapon, 'weaponType' | 'isMelee' | 'name' | 'impactType'>,
): WeaponType {
  if (weapon.weaponType === 'flame' || weapon.weaponType === 'artillery') return weapon.weaponType;
  if (weapon.isMelee) return 'melee';
  if (FLAME_RE.test(weapon.name)) return 'flame';
  if (weapon.impactType === 'tile' || ARTILLERY_RE.test(weapon.name)) return 'artillery';
  return 'ballistic';
}

/** Display metadata (label, colour, i18n key) for a weapon's type. */
export function weaponTypeMeta(
  weapon: Pick<Weapon, 'weaponType' | 'isMelee' | 'name' | 'impactType'>,
): WeaponTypeMeta {
  return META[weaponClass(weapon)];
}

export const WEAPON_TYPES: WeaponType[] = ['melee', 'ballistic', 'flame', 'artillery'];

/**
 * Expected total damage a weapon deals to a single model of the given armour
 * value, across a full attack (all shots × accuracy × per-hit damage after
 * armour, crit and graze). Mirrors the armour table on the weapon detail page,
 * so sorting by A3/A6/A9 matches the numbers shown there.
 */
export function totalDamageVsArmor(
  weapon: Pick<
    Weapon,
    | 'damage'
    | 'armorPiercing'
    | 'accuracy'
    | 'isMelee'
    | 'numAttacks'
    | 'shotsPerAttack'
    | 'burstSize'
  >,
  armor: number,
): number {
  const crit = critChance(0, weapon.armorPiercing, armor);
  const graze = grazeChance(weapon.armorPiercing, armor);
  const range = damageRangeAfterArmor(weapon.damage, armor, weapon.armorPiercing);
  const avgDamage = expectedDamagePerHit(range, crit, graze);
  const baseAcc = weapon.isMelee && weapon.accuracy <= 0 ? 80 : weapon.accuracy;
  const totalShots = weapon.numAttacks * weapon.shotsPerAttack * weapon.burstSize;
  const expectedHits = (totalShots * baseAcc) / 100;
  return expectedHits * avgDamage;
}
