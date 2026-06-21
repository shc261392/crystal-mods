// Combat formulas derived from the data-mining analysis. Pure functions so they
// can be shared between server-rendered pages and client-side tools.

/**
 * Damage a single hit deals to a target with the given armor.
 * Armor piercing offsets the target's armor; minimum 1 damage is always dealt.
 */
export function damagePerHit(weaponDamage: number, targetArmor: number, armorPiercing = 0): number {
  const effectiveArmor = Math.max(0, targetArmor - armorPiercing);
  return Math.max(1, weaponDamage - effectiveArmor);
}

/** Total damage from a full attack action (attacks x shots x burst). */
export function totalAttackDamage(
  weaponDamage: number,
  targetArmor: number,
  armorPiercing: number,
  numAttacks: number,
  shotsPerAttack: number,
  burstSize: number,
): number {
  const shots = Math.max(1, numAttacks) * Math.max(1, shotsPerAttack) * Math.max(1, burstSize);
  return damagePerHit(weaponDamage, targetArmor, armorPiercing) * shots;
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
