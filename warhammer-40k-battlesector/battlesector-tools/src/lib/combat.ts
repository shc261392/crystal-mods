// Combat formulas derived from the decompiled DamageCalculationConfig tooltips
// and the in-game unit panel. Pure functions, shared by pages and tools.
// Full model + worked examples: docs/damage-formula.md

import type { Weapon } from './types';

/**
 * Minimum damage as a fraction of maximum damage. The weapon's `damage` stat is
 * the MAXIMUM; the minimum is `MIN_DAMAGE_MULT * max`. Confirmed = 0.75 from the
 * in-game display (base damage 15–20 = 0.75 × 20).
 */
export const MIN_DAMAGE_MULT = 0.75;

/**
 * Critical chance gained per point of armour piercing ABOVE the target's armour.
 * 5% per point (all factions). The base weapon crit is added on top.
 */
export const CRIT_FACTOR = 5;

/**
 * Critical damage multiplier: crits deal 1.5× damage (50% bonus).
 */
export const CRIT_DAMAGE_MULT = 1.5;

/**
 * Graze chance gained per point of armour ABOVE the weapon's armour piercing.
 * 3% per point (all factions).
 */
export const GRAZE_FACTOR = 3;

/**
 * Graze damage multiplier: grazes deal 0.25× damage (75% reduction).
 */
export const GRAZE_DAMAGE_MULT = 0.25;

/** The in-game damage range of a weapon: [floor(0.75 × max), max]. The minimum
 * is floored to match the in-game display (e.g. max 70 → min 52, not 53). */
export function damageRange(maxDamage: number): { min: number; max: number } {
  const max = Math.max(0, Math.round(maxDamage));
  return { min: Math.floor(max * MIN_DAMAGE_MULT), max };
}

/** Average (expected) damage of a single hit, before hit chance. */
export function damagePerHit(maxDamage: number): number {
  const { min, max } = damageRange(maxDamage);
  return Math.round((min + max) / 2);
}

/** Splash damage dealt to secondary models, and how many receive it. */
export interface SplashInfo {
  min: number;
  max: number;
  /** Number of secondary models that take splash (primary takes full damage). */
  models: number;
}

/**
 * Resolve a weapon's splash damage range. Uses explicit splashMin/splashMax when
 * set; otherwise derives them from the weapon's damage range and splash falloff:
 * `splash = floor(damage × (1 − splashFalloff))` for both min and max.
 * Returns null for non-splash weapons or those hitting only the primary model.
 */
export function splashDamage(weapon: Weapon): SplashInfo | null {
  if (weapon.impactType !== 'splash') return null;
  const models = Math.max(0, (weapon.splashModels ?? 0) - 1);
  if (models < 1) return null;
  const falloff = weapon.splashFalloff ?? 0;
  const dr = damageRange(weapon.damage);
  const min = weapon.splashMin ?? Math.floor(dr.min * (1 - falloff));
  const max = weapon.splashMax ?? Math.floor(dr.max * (1 - falloff));
  return { min, max, models };
}

/** Effective armour after piercing: `max(0, armour − AP)`. Never negative. */
export function effectiveArmor(targetArmor: number, armorPiercing: number): number {
  return Math.max(0, Math.round(targetArmor - armorPiercing));
}

/**
 * Damage range after armour, using the in-game multiplicative model: each point
 * of effective armour (armour − AP, floored at 0) removes 10% of the weapon's
 * MAX damage. The reduced max is floored; the min is then 0.75 × that max,
 * floored:
 *   maxAfter = floor(maxDamage × (1 − effArmour/10))
 *   minAfter = floor(0.75 × maxAfter)
 * At effArmour = 0 this reduces to the base range [floor(0.75×max), max].
 */
export function damageRangeAfterArmor(
  maxDamage: number,
  targetArmor: number,
  armorPiercing: number,
): { min: number; max: number } {
  const effArmor = effectiveArmor(targetArmor, armorPiercing);
  const baseMax = Math.max(0, Math.round(maxDamage));
  // Integer-safe: (10 − effArmour)/10 avoids float error (1 − 9/10 = 0.0999…).
  const remaining = Math.max(0, 10 - effArmor);
  const max = Math.floor((baseMax * remaining) / 10);
  const min = Math.floor(max * MIN_DAMAGE_MULT);
  return { min: Math.max(0, min), max: Math.max(0, max) };
}

/** Average damage of a single hit after armor subtraction, before hit chance/graze. */
export function damagePerHitAfterArmor(
  maxDamage: number,
  targetArmor: number,
  armorPiercing: number,
): number {
  const { min, max } = damageRangeAfterArmor(maxDamage, targetArmor, armorPiercing);
  return (min + max) / 2;
}

/**
 * Critical-hit damage range, derived from the post-armour MAX damage:
 *   critMin = normalMax + 1                     (integer)
 *   critMax = round(normalMax × 1.5)            (NORMAL rounding, not floor)
 * The band is clamped so it never inverts on tiny post-armour damage.
 */
export function critDamageRange(postArmorMax: number): { min: number; max: number } {
  const min = postArmorMax + 1;
  const max = Math.max(min, Math.round(postArmorMax * CRIT_DAMAGE_MULT));
  return { min, max };
}

/**
 * Expected damage per hit: probability-weighted blend of the normal, critical
 * and graze damage bands (all post-armour). Normal = avg(range); crit uses the
 * dedicated crit band (max+1 … 1.5×max); graze = 0.25 × normal average.
 */
export function expectedDamagePerHit(
  range: { min: number; max: number },
  critPercent: number,
  grazePercent: number,
): number {
  const crit = critPercent / 100;
  const graze = grazePercent / 100;
  const normal = 1 - crit - graze;
  const normalAvg = (range.min + range.max) / 2;
  const critBand = critDamageRange(range.max);
  const critAvg = (critBand.min + critBand.max) / 2;
  const grazeAvg = normalAvg * GRAZE_DAMAGE_MULT;
  return normal * normalAvg + crit * critAvg + graze * grazeAvg;
}

/** Graze chance (%): 3% per point of target armour above armour piercing. Graze = no damage. */
export function grazeChance(armorPiercing: number, targetArmor: number): number {
  return clamp(Math.max(0, targetArmor - armorPiercing) * GRAZE_FACTOR, 0, 100);
}

/** Critical chance (%): base weapon crit + 5% per point of AP above armour. */
export function critChance(
  baseCritChance: number,
  armorPiercing: number,
  targetArmor: number,
): number {
  return clamp(baseCritChance + Math.max(0, armorPiercing - targetArmor) * CRIT_FACTOR, 0, 100);
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
