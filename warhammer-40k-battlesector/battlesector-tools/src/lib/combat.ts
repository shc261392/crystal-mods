// Combat formulas derived from the decompiled DamageCalculationConfig tooltips
// and the in-game unit panel. Pure functions, shared by pages and tools.
// See .copilot_workspace/battlesector-data/docs_damage_armor_formula.md

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

export function effectiveArmor(targetArmor: number, armorPiercing: number): number {
  return Math.max(0, Math.round(targetArmor - armorPiercing));
}

/** Damage range after subtracting effective armor from both min/max damage. */
export function damageRangeAfterArmor(
  maxDamage: number,
  targetArmor: number,
  armorPiercing: number,
): { min: number; max: number } {
  const base = damageRange(maxDamage);
  const reduction = effectiveArmor(targetArmor, armorPiercing);
  return {
    min: Math.max(0, base.min - reduction),
    max: Math.max(0, base.max - reduction),
  };
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
 * Expected damage per hit accounting for crit/graze probabilities.
 * Formula: avgDmg × [(1 - crit% - graze%) + (crit% × 1.5) + (graze% × 0.25)]
 * Returns exact decimal value (no rounding).
 */
export function expectedDamagePerHit(
  avgDamage: number,
  critPercent: number,
  grazePercent: number,
): number {
  const crit = critPercent / 100;
  const graze = grazePercent / 100;
  const normal = 1 - crit - graze;
  return avgDamage * (normal + crit * CRIT_DAMAGE_MULT + graze * GRAZE_DAMAGE_MULT);
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
