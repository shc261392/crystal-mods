/**
 * Attack simulation engine — group attacks and splash, shared by the damage
 * calculator (one-round test) and the battle simulation.
 *
 * Everything is expressed as discrete integer damage the game actually rolls:
 * results are min–max ranges (best-case → worst-case remaining HP), never
 * decimal averages. Accuracy, crit and graze are surfaced as separate
 * probabilities rather than folded into the damage range.
 *
 * Timing model: projectiles are treated as HITSCAN (hit-confirm time = 0) for
 * now, so every shot resolves instantly and a squad retargets the moment a model
 * dies. The distribution helpers are written so a real projectile-speed /
 * hit-confirm model can slot in later.
 *
 * Formula reference: docs/damage-formula.md. The splash rule (post-armour range
 * × (1 − falloff), floored, applied to secondary models only) is HYPOTHETICAL
 * and pending confirmation against the game.
 */
import { critChance, damageRangeAfterArmor, grazeChance } from './combat';

/**
 * Post-kill targeting method (game enum `BallisticWeaponTargetType`). Only two
 * values occur in the data. Both RETARGET to another model when the current one
 * dies (redistribution is always on — the old "shots wasted" reading was wrong):
 * - `fixedPerMember`: each attacking member picks the least-targeted enemy model
 *   independently, then retargets least-targeted-first on a kill.
 * - `fixedEntireUnit`: the whole squad focuses the same lowest-index model, then
 *   advances to the next lowest-index model on a kill.
 */
export type TargetingType = 'fixedPerMember' | 'fixedEntireUnit';

export interface AttackWeapon {
  damage: number;
  armorPiercing: number;
  accuracy: number;
  numAttacks: number;
  shotsPerAttack: number;
  burstSize: number;
  isMelee: boolean;
  impactType?: 'single' | 'tile' | 'splash' | undefined;
  targetType?: TargetingType | undefined;
  splashModels?: number | undefined;
  splashFalloff?: number | undefined;
  splashMin?: number | undefined;
  splashMax?: number | undefined;
}

export interface TargetUnit {
  /** Number of models in the target squad. */
  models: number;
  /** Health of a single model. */
  hpPerModel: number;
  armor: number;
  evasion: number;
}

export interface AttackModifiers {
  /** Flat damage added to the weapon's max damage before armour. */
  damageBonus?: number;
  /** Flat armour piercing added. */
  apBonus?: number;
  /** Accuracy modifier (attacker buffs, cover penalties, momentum). */
  accuracyMod?: number;
  /** Number of models in the attacking squad, each firing the weapon. */
  attackerModels?: number;
}

export interface ModelOutcome {
  index: number;
  hpMax: number;
  /** Remaining HP if every incoming shot rolls MIN normal damage (best case). */
  remainingBest: number;
  /** Remaining HP if every incoming shot rolls MAX normal damage (worst case). */
  remainingWorst: number;
  primaryHits: number;
  splashHits: number;
}

export interface AttackResult {
  /** Shots fired by the whole attacking squad. */
  totalShots: number;
  hitChance: number;
  critChance: number;
  grazeChance: number;
  /** Post-armour normal damage per primary hit. */
  primaryMin: number;
  primaryMax: number;
  /** Post-armour splash damage per secondary hit (0 if the weapon has no splash). */
  splashMin: number;
  splashMax: number;
  /** Secondary models a single splash shot reaches (splashModels − 1, capped). */
  splashTargetsPerShot: number;
  models: ModelOutcome[];
  killsBest: number;
  killsWorst: number;
}

export function weaponShots(
  w: Pick<AttackWeapon, 'numAttacks' | 'shotsPerAttack' | 'burstSize'>,
): number {
  return Math.max(1, w.numAttacks) * Math.max(1, w.shotsPerAttack) * Math.max(1, w.burstSize);
}

function hasSplash(w: AttackWeapon): boolean {
  return w.impactType === 'splash' && (w.splashModels ?? 0) > 1;
}

/**
 * Splash damage band vs a specific target armour: the post-armour normal range
 * reduced by the weapon's splash falloff, floored. Explicit splashMin/splashMax
 * overrides (when present) are scaled the same way relative to the base max.
 */
function splashRange(
  w: AttackWeapon,
  postArmorMin: number,
  postArmorMax: number,
): { min: number; max: number } {
  const falloff = w.splashFalloff ?? 0;
  return {
    min: Math.max(0, Math.floor(postArmorMin * (1 - falloff))),
    max: Math.max(0, Math.floor(postArmorMax * (1 - falloff))),
  };
}

interface PassModel {
  hp: number;
  targeted: number;
  primaryHits: number;
  splashHits: number;
}

/** Index of the alive, non-excluded model targeted fewest times (ties → lowest index). */
function leastTargeted(models: PassModel[], exclude: Set<number>): number {
  let best = -1;
  let bestCount = Number.POSITIVE_INFINITY;
  for (let i = 0; i < models.length; i++) {
    const m = models[i];
    if (!m || m.hp <= 0 || exclude.has(i)) continue;
    if (m.targeted < bestCount) {
      best = i;
      bestCount = m.targeted;
    }
  }
  return best;
}

/**
 * Run one deterministic distribution pass at a fixed per-shot damage (used twice:
 * MIN damage → best-case remaining HP, MAX damage → worst-case).
 *
 * `fixedPerMember`: each attacking member targets the least-targeted enemy model,
 * fires all its shots there, and retargets least-targeted-first when that model
 * dies. `fixedEntireUnit`: the whole squad focuses the lowest-index alive model
 * and advances to the next lowest-index model on a kill. Damage never overflows
 * between models. Splash lands with each primary shot on the N least-targeted
 * OTHER models.
 */
function distributePass(
  target: TargetUnit,
  attackerModels: number,
  shotsPerModel: number,
  primaryDmg: number,
  splashDmg: number,
  splashTargets: number,
  targeting: TargetingType,
): PassModel[] {
  const n = target.models;
  const models: PassModel[] = Array.from({ length: n }, () => ({
    hp: target.hpPerModel,
    targeted: 0,
    primaryHits: 0,
    splashHits: 0,
  }));
  const noExclude = new Set<number>();

  const applySplash = (primaryIdx: number) => {
    if (splashDmg <= 0 || splashTargets <= 0) return;
    const localHit = new Set<number>([primaryIdx]);
    let placed = 0;
    while (placed < splashTargets) {
      const pick = leastTargeted(models, localHit);
      const sm = models[pick];
      if (!sm) break;
      sm.hp = Math.max(0, sm.hp - splashDmg);
      sm.splashHits++;
      sm.targeted++;
      localHit.add(pick);
      placed++;
    }
  };

  const fireAt = (i: number) => {
    const pm = models[i];
    if (!pm) return;
    pm.hp = Math.max(0, pm.hp - primaryDmg);
    pm.primaryHits++;
    pm.targeted++;
    applySplash(i);
  };

  if (targeting === 'fixedEntireUnit') {
    // Whole squad focuses the lowest-index alive model; advance on kill.
    const totalShots = attackerModels * shotsPerModel;
    for (let s = 0; s < totalShots; s++) {
      let t = -1;
      for (let i = 0; i < n; i++) {
        const m = models[i];
        if (m && m.hp > 0) {
          t = i;
          break;
        }
      }
      if (t === -1) break;
      fireAt(t);
    }
  } else {
    // Each member locks the least-targeted model, retargeting on a kill.
    for (let m = 0; m < attackerModels; m++) {
      let t = leastTargeted(models, noExclude);
      if (t === -1) break;
      for (let s = 0; s < shotsPerModel; s++) {
        const cur = models[t];
        if (!cur || cur.hp <= 0) {
          t = leastTargeted(models, noExclude);
          if (t === -1) break;
        }
        fireAt(t);
      }
    }
  }

  return models;
}

/** Simulate a full attack (group fire + splash) against a target squad. */
export function simulateAttack(
  weapon: AttackWeapon,
  target: TargetUnit,
  mods: AttackModifiers = {},
): AttackResult {
  const damage = Math.max(0, weapon.damage + (mods.damageBonus ?? 0));
  const ap = Math.max(0, weapon.armorPiercing + (mods.apBonus ?? 0));
  const attackerModels = Math.max(1, mods.attackerModels ?? 1);
  const totalShots = attackerModels * weaponShots(weapon);

  const { min: primaryMin, max: primaryMax } = damageRangeAfterArmor(damage, target.armor, ap);

  const splash = hasSplash(weapon)
    ? splashRange(weapon, primaryMin, primaryMax)
    : { min: 0, max: 0 };
  const splashTargetsPerShot = hasSplash(weapon)
    ? Math.min((weapon.splashModels ?? 1) - 1, Math.max(0, target.models - 1))
    : 0;

  const baseAcc = weapon.isMelee && weapon.accuracy <= 0 ? 80 : weapon.accuracy;
  const hit = Math.max(0, Math.min(100, baseAcc + (mods.accuracyMod ?? 0) - target.evasion));

  const shotsPerModel = weaponShots(weapon);
  const targeting: TargetingType = weapon.targetType ?? 'fixedPerMember';

  // Best case for the defender = every shot rolls MIN damage; worst = MAX.
  const best = distributePass(
    target,
    attackerModels,
    shotsPerModel,
    primaryMin,
    splash.min,
    splashTargetsPerShot,
    targeting,
  );
  const worst = distributePass(
    target,
    attackerModels,
    shotsPerModel,
    primaryMax,
    splash.max,
    splashTargetsPerShot,
    targeting,
  );

  const models: ModelOutcome[] = Array.from({ length: target.models }, (_, i) => {
    const b = best[i];
    const w = worst[i];
    return {
      index: i,
      hpMax: target.hpPerModel,
      remainingBest: b ? b.hp : target.hpPerModel,
      remainingWorst: w ? w.hp : target.hpPerModel,
      primaryHits: w ? w.primaryHits : 0,
      splashHits: w ? w.splashHits : 0,
    };
  });

  return {
    totalShots,
    hitChance: hit,
    critChance: critChance(0, ap, target.armor),
    grazeChance: grazeChance(ap, target.armor),
    primaryMin,
    primaryMax,
    splashMin: splash.min,
    splashMax: splash.max,
    splashTargetsPerShot,
    models,
    killsBest: best.filter((m) => m.hp <= 0).length,
    killsWorst: worst.filter((m) => m.hp <= 0).length,
  };
}
