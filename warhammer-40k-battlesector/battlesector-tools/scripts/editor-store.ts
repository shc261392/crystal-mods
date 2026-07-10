/**
 * Editor data store — the single source of truth for how curated edits are
 * written back into the git-tracked JSON files under `src/data/`.
 *
 * Used by:
 *   - the dev-only editor API middleware (scripts/editor-integration.ts)
 *   - the predeploy validation script (scripts/predeploy-check.ts)
 *
 * Every editable field is whitelisted and type-coerced here so the browser can
 * never write arbitrary keys into the game-data files. Player "notes" are
 * clamped to a short length to keep them as brief field-test observations.
 */
import { readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { generateAbilityUi } from './generate-ability-ui.ts';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
export const PROJECT_ROOT = path.join(scriptDir, '..');
export const DATA_DIR = path.join(PROJECT_ROOT, 'src', 'data');

export const UNITS_PATH = path.join(DATA_DIR, 'units.json');
export const WEAPONS_PATH = path.join(DATA_DIR, 'weapons.json');
export const ABILITY_SOURCE_PATH = path.join(DATA_DIR, 'ability-overrides.source.json');

export type EditorTarget = 'unit' | 'weapon' | 'ability';

/** Max length for a player field note (~100 words). */
export const NOTES_MAX_CHARS = 600;
export const NOTES_MAX_WORDS = 100;

type Coercer = (value: unknown) => unknown;

const asTrimmedString: Coercer = (v) => (typeof v === 'string' ? v.trim() : '');
const asBool: Coercer = (v) => v === true || v === 'true';
const asInt: Coercer = (v) => {
  const n = Number(v);
  return Number.isFinite(n) ? Math.round(n) : 0;
};
const asNum: Coercer = (v) => {
  const n = Number(v);
  return Number.isFinite(n) ? n : 0;
};
/** Like asInt but returns undefined for blank/invalid so the field can be unset. */
const asOptionalInt: Coercer = (v) => {
  if (v === '' || v === null || v === undefined) return undefined;
  const n = Number(v);
  return Number.isFinite(n) ? Math.round(n) : undefined;
};
const WEAPON_TYPES = new Set(['melee', 'ballistic', 'flame', 'artillery']);
const asWeaponType: Coercer = (v) => (typeof v === 'string' && WEAPON_TYPES.has(v) ? v : undefined);

/** Clamp a player note to a brief observation (<=100 words / <=600 chars). */
export function clampNote(value: unknown): string {
  if (typeof value !== 'string') return '';
  const words = value.trim().split(/\s+/).filter(Boolean).slice(0, NOTES_MAX_WORDS);
  return words.join(' ').slice(0, NOTES_MAX_CHARS);
}

const UNIT_FIELDS: Record<string, Coercer> = {
  name: asTrimmedString,
  portrait: asTrimmedString,
  pointCost: asInt,
  members: asInt,
  maxHealth: asInt,
  totalHealth: asInt,
  evasion: asInt,
  armor: asInt,
  armorFront: asInt,
  armorLeft: asInt,
  armorRight: asInt,
  armorRear: asInt,
  meleeAccuracy: asInt,
  rangedAccuracyModifier: asInt,
  maxActionPoints: asInt,
  maxMovementPoints: asInt,
  momentumPerModelDeath: asNum,
  unitHeight: asNum,
  activationRange: asNum,
  awarenessRange: asNum,
  isLarge: asBool,
  campaignOnly: asBool,
  canMeleeReact: asBool,
  canFallback: asBool,
  hidden: asBool,
  notes: clampNote,
};

const WEAPON_FIELDS: Record<string, Coercer> = {
  name: asTrimmedString,
  icon: asTrimmedString,
  description: asTrimmedString,
  damage: asNum,
  accuracy: asInt,
  numAttacks: asInt,
  shotsPerAttack: asInt,
  burstSize: asInt,
  armorPiercing: asInt,
  isMelee: asBool,
  isRanged: asBool,
  weaponType: asWeaponType,
  rangeMin: asNum,
  rangeOptimal: asNum,
  rangeMax: asNum,
  accuracyFalloff: asNum,
  damageFalloff: asNum,
  ignoresRangePenalty: asBool,
  pistol: asBool,
  splashModels: asInt,
  splashFalloff: asNum,
  splashHeavyAll: asBool,
  splashMin: asOptionalInt,
  splashMax: asOptionalInt,
  hidden: asBool,
  notes: clampNote,
};

const ABILITY_FIELDS: Record<string, Coercer> = {
  title: asTrimmedString,
  icon: asTrimmedString,
  description: asTrimmedString,
  actionPoints: asInt,
  cooldown: asInt,
  notes: clampNote,
};

function coercePatch(fields: Record<string, Coercer>, patch: Record<string, unknown>) {
  const clean: Record<string, unknown> = {};
  for (const [key, raw] of Object.entries(patch)) {
    const coerce = fields[key];
    if (!coerce) continue; // drop non-whitelisted keys
    clean[key] = coerce(raw);
  }
  return clean;
}

function readJson<T>(file: string): T {
  return JSON.parse(readFileSync(file, 'utf8')) as T;
}

/**
 * Serialize a single array-element object and re-indent it to sit at the given
 * base indentation (the array element indent), matching JSON.stringify's
 * 2-space style. Only the edited object is reformatted; the rest of the file is
 * preserved byte-for-byte by the splice below.
 */
function serializeElement(obj: unknown, baseIndent: string): string {
  const raw = JSON.stringify(obj, null, 2);
  return raw
    .split('\n')
    .map((line, i) => (i === 0 ? line : baseIndent + line))
    .join('\n');
}

/**
 * Find the character span [start, end] of the top-level array element whose
 * `"id"` equals `id`. String-aware brace/bracket scanner so braces inside string
 * values are ignored.
 */
function findElementSpan(text: string, id: number): [number, number] | null {
  let depth = 0;
  let inStr = false;
  let esc = false;
  let elemStart = -1;
  const spans: Array<[number, number]> = [];

  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inStr) {
      if (esc) esc = false;
      else if (c === '\\') esc = true;
      else if (c === '"') inStr = false;
      continue;
    }
    if (c === '"') {
      inStr = true;
    } else if (c === '{' || c === '[') {
      depth += 1;
      if (depth === 2 && c === '{') elemStart = i;
    } else if (c === '}' || c === ']') {
      if (depth === 2 && c === '}' && elemStart >= 0) {
        spans.push([elemStart, i]);
        elemStart = -1;
      }
      depth -= 1;
    }
  }

  const idRe = new RegExp(`"id"\\s*:\\s*${id}\\b`);
  for (const [start, end] of spans) {
    if (idRe.test(text.slice(start, end + 1))) return [start, end];
  }
  return null;
}

/**
 * Update one object in an array-of-objects JSON file in place, rewriting only
 * that object's text span so unrelated entries keep their exact formatting.
 */
function spliceElement(
  file: string,
  id: number,
  mutate: (obj: Record<string, unknown>) => void,
): { found: boolean; wrote: boolean } {
  const text = readFileSync(file, 'utf8');
  const span = findElementSpan(text, id);
  if (!span) return { found: false, wrote: false };
  const [start, end] = span;

  const obj = JSON.parse(text.slice(start, end + 1)) as Record<string, unknown>;
  mutate(obj);

  // Base indent = whitespace preceding the element's opening brace on its line.
  const lineStart = text.lastIndexOf('\n', start) + 1;
  const baseIndent = text.slice(lineStart, start);

  const replacement = serializeElement(obj, baseIndent);
  const original = text.slice(start, end + 1);
  if (replacement === original) return { found: true, wrote: false };
  writeFileSync(file, text.slice(0, start) + replacement + text.slice(end + 1), 'utf8');
  return { found: true, wrote: true };
}

function writeJson(file: string, data: unknown): void {
  writeFileSync(file, `${JSON.stringify(data, null, 2)}\n`, 'utf8');
}

function stableJson(value: unknown): string {
  return JSON.stringify(value);
}

/** Remove empty-string / empty-note keys so we don't persist blank fields. */
function stripEmpty(obj: Record<string, unknown>, dropKeys: string[]): void {
  for (const key of dropKeys) {
    if (obj[key] === '' || obj[key] === undefined) delete obj[key];
  }
}

/** Drop a boolean flag when it is false, so we only persist the "on" state. */
function stripFalse(obj: Record<string, unknown>, keys: string[]): void {
  for (const key of keys) {
    if (obj[key] === false) delete obj[key];
  }
}

export interface ApplyResult {
  ok: boolean;
  target: EditorTarget;
  id: string | number;
  changed: string[];
  wrote?: boolean; // GOLDEN RULE: Report if disk write actually happened
  message?: string;
}

/**
 * Apply a whitelisted patch to a single unit/weapon/ability and persist it to
 * the git-tracked JSON. For abilities the TS UI modules are regenerated too so
 * the running dev site reflects the change immediately.
 */
export function applyPatch(
  target: EditorTarget,
  id: string | number,
  patch: Record<string, unknown>,
): ApplyResult {
  if (target === 'unit') {
    const clean = coercePatch(UNIT_FIELDS, patch);
    const write = spliceElement(UNITS_PATH, Number(id), (unit) => {
      Object.assign(unit, clean);
      stripEmpty(unit, ['notes']);
      stripFalse(unit, ['hidden']);
    });
    if (!write.found)
      return { ok: false, target, id, changed: [], message: `Unit ${id} not found` };
    return {
      ok: true,
      target,
      id,
      changed: write.wrote ? Object.keys(clean) : [],
      wrote: write.wrote,
    };
  }

  if (target === 'weapon') {
    const clean = coercePatch(WEAPON_FIELDS, patch);
    const write = spliceElement(WEAPONS_PATH, Number(id), (weapon) => {
      Object.assign(weapon, clean);
      // Keep the legacy melee/ranged flags consistent with the new weaponType.
      // Variable keys satisfy both ts(4111) index-signature and Biome useLiteralKeys.
      const typeKey = 'weaponType';
      const meleeKey = 'isMelee';
      const rangedKey = 'isRanged';
      const wt = clean[typeKey];
      if (typeof wt === 'string') {
        weapon[meleeKey] = wt === 'melee';
        weapon[rangedKey] = wt !== 'melee';
      }
      stripEmpty(weapon, ['notes', 'description', 'weaponType', 'splashMin', 'splashMax']);
      stripFalse(weapon, ['hidden']);
    });
    if (!write.found)
      return { ok: false, target, id, changed: [], message: `Weapon ${id} not found` };
    return {
      ok: true,
      target,
      id,
      changed: write.wrote ? Object.keys(clean) : [],
      wrote: write.wrote,
    };
  }

  // ability
  const source = readJson<{
    entries: Record<string, Record<string, unknown>>;
    generatedAt?: string;
  }>(ABILITY_SOURCE_PATH);
  const key = String(id);
  const clean = coercePatch(ABILITY_FIELDS, patch);
  const kindKey = 'kind';
  const kindRaw = patch[kindKey];
  if (kindRaw === 'active' || kindRaw === 'passive') clean[kindKey] = kindRaw;
  const existing = source.entries[key] ?? {};
  const merged = { ...existing, ...clean };
  stripEmpty(merged, ['notes', 'icon', 'description', 'title']);
  if (stableJson(existing) === stableJson(merged)) {
    return { ok: true, target, id, changed: [], wrote: false }; // No-op: ability not in source
  }
  source.entries[key] = merged;
  source.generatedAt = new Date().toISOString();
  writeJson(ABILITY_SOURCE_PATH, source);
  // Regenerate the TS modules the site consumes.
  generateAbilityUi(ABILITY_SOURCE_PATH);
  return { ok: true, target, id, changed: Object.keys(clean), wrote: true };
}
