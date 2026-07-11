/**
 * Autonomous generator: computes percentile-based stat grades ("六邊形能力指數圖"
 * ability-index rankings) for every non-hidden unit and weapon, so the stat
 * hexagon component can render how a unit/weapon ranks against the whole roster.
 *
 * Grading: each axis is percentile-ranked across all entities, then bucketed
 * into 5 equal quintile grades (PR 0–20 → 1 … 80–100 → 5). Grade 5 is the
 * outermost ring of the hexagon.
 *
 * Sources (committed): src/data/units.json, src/data/weapons.json.
 * Outputs (committed):
 *   - src/data/unit-ranks.json    ({ [unitId]: { hp,ap,mp,armor,dodge,pts } })
 *   - src/data/weapon-ranks.json  ({ [weaponId]: { dmg3,dmg6,dmg9,range,splash,hits } })
 * Each axis entry is { v: rawValue, g: grade 1–5, pr: percentile 0–100 }.
 *
 * Run: `pnpm gen:ranks` (chained from prebuild + predeploy-check).
 */
import { readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.join(scriptDir, '..');
const dataDir = path.join(projectRoot, 'src', 'data');

interface RawUnit {
  id: number;
  faction: number;
  hidden?: boolean;
  maxHealth: number;
  armor: number;
  armorFront: number;
  armorLeft: number;
  armorRight: number;
  armorRear: number;
  evasion: number;
  maxActionPoints: number;
  maxMovementPoints: number;
  pointCost: number;
}

interface RawWeapon {
  id: number;
  name: string;
  hidden?: boolean;
  damage: number;
  armorPiercing: number;
  numAttacks: number;
  shotsPerAttack: number;
  burstSize: number;
  rangeMax: number;
  impactType?: 'single' | 'splash' | 'tile';
  splashModels?: number;
}

interface AxisEntry {
  v: number;
  g: number;
  pr: number;
}

type RankRecord = Record<string, AxisEntry>;

const HIDDEN_FACTION_IDS = new Set<number>([4]);
const MIN_DAMAGE_MULT = 0.75;
const FLAME_RE = /flame|flamer|burna|incinerat|immolat|inferno|skorcha|conflagrat/i;

function readJson<T>(file: string): T {
  return JSON.parse(readFileSync(path.join(dataDir, file), 'utf8')) as T;
}

/** Representative armor: simple armor value, else mean of nonzero facings. */
function unitArmor(u: RawUnit): number {
  if (u.armor > 0) return u.armor;
  const faces = [u.armorFront, u.armorLeft, u.armorRight, u.armorRear].filter((x) => x > 0);
  if (faces.length === 0) return 0;
  return Math.round(faces.reduce((a, b) => a + b, 0) / faces.length);
}

/** Average damage of one hit after subtracting effective armor (max(0, armor-ap)). */
function dmgAfterArmor(w: RawWeapon, armor: number): number {
  const max = Math.max(0, Math.round(w.damage));
  const min = Math.round(max * MIN_DAMAGE_MULT);
  const reduction = Math.max(0, armor - w.armorPiercing);
  const rMin = Math.max(0, min - reduction);
  const rMax = Math.max(0, max - reduction);
  return (rMin + rMax) / 2;
}

function weaponHits(w: RawWeapon): number {
  return Math.max(1, (w.numAttacks || 1) * (w.shotsPerAttack || 1) * (w.burstSize || 1));
}

/** Models effectively struck: flame/template → 20, splash → splashModels, else 1. */
function effectiveSplashModels(w: RawWeapon): number {
  if (FLAME_RE.test(w.name)) return 20;
  if (w.impactType === 'tile') return 20;
  if (w.impactType === 'splash') return Math.max(1, w.splashModels ?? 1);
  return 1;
}

/**
 * Percentile-rank a list of values and bucket into 5 quintile grades.
 * Returns a parallel array of AxisEntry. Ties share the same percentile/grade.
 */
function gradeAxis(values: number[]): AxisEntry[] {
  const n = values.length;
  const sorted = [...values].sort((a, b) => a - b);
  // For each distinct value, count strictly-less entries (for tie-sharing).
  return values.map((v) => {
    let lo = 0;
    let hi = sorted.length;
    // binary search for first index >= v → countLess
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      const midVal = sorted[mid] ?? Number.POSITIVE_INFINITY;
      if (midVal < v) lo = mid + 1;
      else hi = mid;
    }
    const countLess = lo;
    const pr = n > 1 ? (countLess / (n - 1)) * 100 : 100;
    const g = Math.min(5, Math.max(1, Math.floor(pr / 20) + 1));
    return { v: round2(v), g, pr: Math.round(pr) };
  });
}

function round2(v: number): number {
  return Math.round(v * 100) / 100;
}

function buildRecords<T extends { id: number }>(
  entities: T[],
  axes: Record<string, (e: T) => number>,
): Record<string, RankRecord> {
  const axisNames = Object.keys(axes);
  const graded: Record<string, AxisEntry[]> = {};
  for (const [axis, fn] of Object.entries(axes)) {
    graded[axis] = gradeAxis(entities.map(fn));
  }
  const out: Record<string, RankRecord> = {};
  entities.forEach((e, i) => {
    const rec: RankRecord = {};
    for (const axis of axisNames) {
      const entry = graded[axis]?.[i];
      if (entry) rec[axis] = entry;
    }
    out[String(e.id)] = rec;
  });
  return out;
}

// ---- Units ----------------------------------------------------------------
export interface RankSummary {
  units: number;
  weapons: number;
}

export function generateStatRanks(): RankSummary {
  const rawUnits = readJson<RawUnit[]>('units.json').filter(
    (u) => !HIDDEN_FACTION_IDS.has(u.faction) && !u.hidden,
  );
  const unitRanks = buildRecords(rawUnits, {
    hp: (u) => u.maxHealth, // per-model HP
    ap: (u) => u.maxActionPoints,
    mp: (u) => u.maxMovementPoints,
    armor: (u) => unitArmor(u),
    dodge: (u) => u.evasion,
    pts: (u) => u.pointCost,
  });

  // Weapons: mirror data.ts — only weapons used by a non-hidden unit are public.
  const usedWeaponIds = new Set<number>();
  const fullUnits = readJson<
    Array<RawUnit & { weaponSlots: { options: { weaponId: number }[] }[] }>
  >('units.json').filter((u) => !HIDDEN_FACTION_IDS.has(u.faction) && !u.hidden);
  for (const u of fullUnits) {
    for (const slot of u.weaponSlots)
      for (const opt of slot.options) usedWeaponIds.add(opt.weaponId);
  }
  const rawWeapons = readJson<RawWeapon[]>('weapons.json').filter(
    (w) => !w.hidden && usedWeaponIds.has(w.id),
  );
  const weaponRanks = buildRecords(rawWeapons, {
    dmg3: (w) => dmgAfterArmor(w, 3),
    dmg6: (w) => dmgAfterArmor(w, 6),
    dmg9: (w) => dmgAfterArmor(w, 9),
    range: (w) => w.rangeMax,
    splash: (w) => effectiveSplashModels(w),
    hits: (w) => weaponHits(w),
  });

  writeFileSync(path.join(dataDir, 'unit-ranks.json'), `${JSON.stringify(unitRanks)}\n`);
  writeFileSync(path.join(dataDir, 'weapon-ranks.json'), `${JSON.stringify(weaponRanks)}\n`);
  return { units: Object.keys(unitRanks).length, weapons: Object.keys(weaponRanks).length };
}

// CLI entry (guarded so predeploy-check can import the function without side effects).
if (import.meta.url === `file://${process.argv[1]}`) {
  const s = generateStatRanks();
  console.log(`  ✓ stat ranks: ${s.units} units, ${s.weapons} weapons`);
}
