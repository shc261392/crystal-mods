// Display metadata for weapon attack types. Shared by the weapons index,
// weapon detail page, unit loadout, and the weapon stat zone so the label,
// colour, and i18n key stay consistent everywhere.

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

/** Display metadata (label, colour, i18n key) for a weapon's type. */
export function weaponTypeMeta(weapon: Pick<Weapon, 'weaponType' | 'isMelee'>): WeaponTypeMeta {
  return META[resolveWeaponType(weapon)];
}

export const WEAPON_TYPES: WeaponType[] = ['melee', 'ballistic', 'flame', 'artillery'];
