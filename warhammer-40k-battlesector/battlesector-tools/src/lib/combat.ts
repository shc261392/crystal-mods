// Combat formulas derived from the decompiled DamageCalculationConfig tooltips
// and the in-game unit panel. Pure functions, shared by pages and tools.
// See .copilot_workspace/battlesector-data/docs_damage_armor_formula.md

/**
 * Minimum damage as a fraction of maximum damage. The weapon's `damage` stat is
 * the MAXIMUM; the minimum is `MIN_DAMAGE_MULT * max`. Confirmed = 0.75 from the
 * in-game display (base damage 15–20 = 0.75 × 20).
 */
export const MIN_DAMAGE_MULT = 0.75;

/**
 * Graze/critical chance gained per point of armour differential (|AP − armour|).
 * ASSUMPTION: 1% per point. The real GrazeDifferentialFactor /
 * CriticalDifferentialFactor are native and not extractable; calibrate here when
 * known (see the formula doc).
 */
export const DIFFERENTIAL_FACTOR = 1;

/** The in-game damage range of a weapon: [0.75 × max, max]. */
export function damageRange(maxDamage: number): { min: number; max: number } {
  const max = Math.max(0, Math.round(maxDamage));
  return { min: Math.round(max * MIN_DAMAGE_MULT), max };
}

/** Average (expected) damage of a single hit, before hit chance. */
export function damagePerHit(maxDamage: number): number {
  const { min, max } = damageRange(maxDamage);
  return Math.round((min + max) / 2);
}

/** Graze chance (%): rises as the target's armour exceeds armour piercing. */
export function grazeChance(armorPiercing: number, targetArmor: number): number {
  return clamp(Math.max(0, targetArmor - armorPiercing) * DIFFERENTIAL_FACTOR, 0, 100);
}

/** Critical chance (%): base weapon crit + bonus as AP exceeds armour. */
export function critChance(
  baseCritChance: number,
  armorPiercing: number,
  targetArmor: number,
): number {
  return clamp(
    baseCritChance + Math.max(0, armorPiercing - targetArmor) * DIFFERENTIAL_FACTOR,
    0,
    100,
  );
}

/** Final hit chance clamped to 0..100. */
export function hitChance(
  weaponAccuracy: number,
  attackerAccuracyModifier: number,
  targetEvasion: number,
): number {
  return clamp(weaponAccuracy + attackerAccuracyModifier - targetEvasion, 0, 100);
}

/** Models removed from a unit. Damage does not overflow between models. */
export function modelsKilled(totalDamage: number, healthPerModel: number): number {
  if (healthPerModel <= 0) return 0;
  return Math.floor(totalDamage / healthPerModel);
}

/** Expected damage accounting for hit chance (per full attack). */
export function expectedDamage(rawDamage: number, hitPercent: number): number {
  return Math.round(rawDamage * (clamp(hitPercent, 0, 100) / 100));
}

export function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

export function formatPercent(value: number): string {
  return `${Math.round(value)}%`;
}
