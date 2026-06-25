import factionMomentum from '../data/faction-momentum.json';

export interface PassiveEffect {
  stat: string;
  perMomentum: number | null;
  unit: string;
  affectsCalc: boolean;
}

export interface FactionPassive {
  passive: string;
  statusEffectId: number | null;
  effects: PassiveEffect[];
  note?: string;
  noCalcEffect?: boolean;
  conditional?: { name: string; note: string };
  special?: string;
}

const PASSIVES = (factionMomentum as { factions: Record<string, FactionPassive> }).factions;

/** Resolve a faction's momentum passive (name + verified effects). */
export function getFactionPassive(factionId: number): FactionPassive | null {
  return PASSIVES[String(factionId)] ?? null;
}

const STAT_LABELS: Record<string, string> = {
  criticalChance: 'critical chance',
  accuracy: 'accuracy',
  evasion: 'evasion',
  armorPiercing: 'armour penetration',
  damageMul: 'damage',
  rangedDamageMul: 'ranged damage',
  rangeStability: 'range stability',
  outgoingGraze: 'enemy graze chance',
  heal: 'reanimation / healing',
};

function fmtNum(n: number): string {
  // Trim trailing zeros; keep up to 3 decimals.
  return Number.parseFloat(n.toFixed(3)).toString();
}

/**
 * Render a single verified per-momentum effect as readable text, e.g.
 * "+0.4% critical chance per momentum". Returns null for effects that have no
 * smooth per-momentum value (special/threshold) — those are covered by `note`.
 */
export function formatPassiveEffect(e: PassiveEffect): string | null {
  if (e.perMomentum == null || e.unit === 'special' || e.unit === 'threshold') return null;
  const label = STAT_LABELS[e.stat] ?? e.stat;
  const sign = e.perMomentum < 0 ? '−' : '+';
  const mag = Math.abs(e.perMomentum);
  if (e.unit === 'percent') return `${sign}${fmtNum(mag)}% ${label} per momentum`;
  if (e.unit === 'percentMul') return `${sign}${fmtNum(mag * 100)}% ${label} per momentum`;
  // flat
  return `${sign}${fmtNum(mag)} ${label} per momentum`;
}

/** Build the display lines for a faction passive (effect strings, in order). */
export function passiveEffectLines(p: FactionPassive): string[] {
  return p.effects.map(formatPassiveEffect).filter((s): s is string => s != null);
}
