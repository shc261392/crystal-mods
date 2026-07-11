// Shared army-list store backed by localStorage. Used by the unit detail page
// ("+ Army Builder"), the army builder page, and the global army drawer.
//
// v2 supports MULTIPLE named armies. A single "active" army is the target for
// the v1-compatible helpers (getArmy/saveArmy/addToArmy) so existing callers
// keep working unchanged. The legacy single-army `bs.army.v1` value is migrated
// into the first v2 army on first access.

export interface ArmyEntry {
  id: number;
  name: string;
  points: number;
  faction: string;
  qty: number;
  /** Selected weapon ids (one per slot). Absent = default loadout. */
  loadout?: number[];
}

/** A named army: a list of entries plus metadata. */
export interface Army {
  id: string;
  name: string;
  entries: ArmyEntry[];
  createdAt: number;
}

interface ArmiesState {
  armies: Army[];
  activeId: string;
}

const KEY = 'bs.army.v1';
const KEY_V2 = 'bs.armies.v2';

/** Army name length bounds (goal: 1–30 chars). */
export const ARMY_NAME_MIN = 1;
export const ARMY_NAME_MAX = 30;

/** Maximum number of units (sum of quantities) an army may contain. */
export const ARMY_UNIT_CAP = 30;

function uid(): string {
  return `a${Date.now().toString(36)}${Math.random().toString(36).slice(2, 7)}`;
}

function clampName(name: string, fallback: string): string {
  const trimmed = name.trim().slice(0, ARMY_NAME_MAX);
  return trimmed.length >= ARMY_NAME_MIN ? trimmed : fallback;
}

/** Next default army name: "Army N" where N avoids collisions. */
function defaultArmyName(armies: Army[]): string {
  let n = armies.length + 1;
  const names = new Set(armies.map((a) => a.name));
  while (names.has(`Army ${n}`)) n += 1;
  return `Army ${n}`;
}

function readV1(): ArmyEntry[] {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as ArmyEntry[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

/** Load the full multi-army state, migrating from v1 and self-healing. */
function loadState(): ArmiesState {
  try {
    const raw = localStorage.getItem(KEY_V2);
    if (raw) {
      const parsed = JSON.parse(raw) as Partial<ArmiesState>;
      const armies = Array.isArray(parsed.armies) ? parsed.armies.filter(isArmy) : [];
      const firstArmy = armies[0];
      if (firstArmy) {
        const activeId = armies.some((a) => a.id === parsed.activeId)
          ? (parsed.activeId as string)
          : firstArmy.id;
        return { armies, activeId };
      }
    }
  } catch {
    // fall through to migration / fresh state
  }
  // Migrate a legacy v1 army (if any) into a fresh v2 state.
  const legacy = readV1();
  const first: Army = {
    id: uid(),
    name: 'Army 1',
    entries: legacy,
    createdAt: Date.now(),
  };
  const state: ArmiesState = { armies: [first], activeId: first.id };
  writeState(state);
  return state;
}

function isArmy(v: unknown): v is Army {
  if (!v || typeof v !== 'object') return false;
  const a = v as { id?: unknown; name?: unknown; entries?: unknown };
  return typeof a.id === 'string' && typeof a.name === 'string' && Array.isArray(a.entries);
}

function writeState(state: ArmiesState): void {
  localStorage.setItem(KEY_V2, JSON.stringify(state));
}

/** All armies (always ≥ 1). */
export function getArmies(): Army[] {
  return loadState().armies;
}

/** The id of the currently active army. */
export function getActiveArmyId(): string {
  return loadState().activeId;
}

/** The active army object. */
export function getActiveArmy(): Army {
  const state = loadState();
  return state.armies.find((a) => a.id === state.activeId) ?? (state.armies[0] as Army);
}

/** Switch the active army. No-op if the id is unknown. */
export function setActiveArmy(id: string): void {
  const state = loadState();
  if (!state.armies.some((a) => a.id === id)) return;
  writeState({ ...state, activeId: id });
}

/** Create a new (empty) army and make it active. Returns the new army. */
export function createArmy(name?: string): Army {
  const state = loadState();
  const army: Army = {
    id: uid(),
    name: clampName(name ?? '', defaultArmyName(state.armies)),
    entries: [],
    createdAt: Date.now(),
  };
  writeState({ armies: [...state.armies, army], activeId: army.id });
  return army;
}

/** Rename an army (clamped to 1–30 chars; empty reverts to a default name). */
export function renameArmy(id: string, name: string): void {
  const state = loadState();
  const army = state.armies.find((a) => a.id === id);
  if (!army) return;
  army.name = clampName(name, army.name || defaultArmyName(state.armies));
  writeState(state);
}

/** Delete an army. Always keeps at least one army (recreates an empty one). */
export function deleteArmy(id: string): void {
  const state = loadState();
  const armies = state.armies.filter((a) => a.id !== id);
  if (armies.length === 0) {
    const fresh: Army = { id: uid(), name: 'Army 1', entries: [], createdAt: Date.now() };
    writeState({ armies: [fresh], activeId: fresh.id });
    return;
  }
  const activeId = armies.some((a) => a.id === state.activeId)
    ? state.activeId
    : (armies[0] as Army).id;
  writeState({ armies, activeId });
}

// --- v1-compatible helpers (operate on the ACTIVE army) --------------------

export function getArmy(): ArmyEntry[] {
  return getActiveArmy().entries;
}

export function saveArmy(army: ArmyEntry[]): void {
  const state = loadState();
  const active = state.armies.find((a) => a.id === state.activeId);
  if (!active) return;
  active.entries = army;
  writeState(state);
}

/** Loadout signature used to distinguish entries of the same unit. */
function loadoutSig(loadout?: number[]): string {
  return (loadout ?? []).join('-');
}

export function addToArmy(entry: Omit<ArmyEntry, 'qty'>): ArmyEntry[] {
  const army = getArmy();
  // Match on unit id AND loadout so the same unit with a different loadout
  // forms a separate entry (mirrors the standalone army builder).
  const sig = loadoutSig(entry.loadout);
  const existing = army.find((e) => e.id === entry.id && loadoutSig(e.loadout) === sig);
  if (existing) {
    existing.qty += 1;
  } else {
    army.push({ ...entry, qty: 1 });
  }
  saveArmy(army);
  return army;
}

/** The faction the active army is locked to (its first entry), or null if empty. */
export function getActiveArmyFaction(): string | null {
  return getActiveArmy().entries[0]?.faction ?? null;
}

/**
 * Add a unit to the active army with faction locking and the unit cap. Returns
 * { ok } or a rejection with a reason: 'faction' (wrong faction) or 'cap' (full).
 */
export function addToArmyLocked(
  entry: Omit<ArmyEntry, 'qty'>,
):
  | { ok: true }
  | { ok: false; reason: 'faction'; lockedTo: string }
  | { ok: false; reason: 'cap'; cap: number } {
  const locked = getActiveArmyFaction();
  if (locked !== null && locked !== entry.faction) {
    return { ok: false, reason: 'faction', lockedTo: locked };
  }
  if (totalUnits(getArmy()) >= ARMY_UNIT_CAP) {
    return { ok: false, reason: 'cap', cap: ARMY_UNIT_CAP };
  }
  addToArmy(entry);
  return { ok: true };
}

/** Replace an entry's loadout (weapon selection) and recomputed point cost.
 * Targets the entry by its current loadout signature; merges into a duplicate
 * (same unit + resulting loadout) when one already exists. */
export function setEntryLoadout(
  id: number,
  oldLoadout: number[],
  loadout: number[],
  points: number,
): void {
  const army = getArmy();
  const oldSig = loadoutSig(oldLoadout);
  const entry = army.find((e) => e.id === id && loadoutSig(e.loadout) === oldSig);
  if (!entry) return;
  const newSig = loadoutSig(loadout);
  const dup = army.find((e) => e !== entry && e.id === id && loadoutSig(e.loadout) === newSig);
  if (dup) {
    dup.qty += entry.qty;
    saveArmy(army.filter((e) => e !== entry));
    return;
  }
  entry.loadout = loadout;
  entry.points = points;
  saveArmy(army);
}

export function totalPoints(army: ArmyEntry[]): number {
  return army.reduce((sum, e) => sum + e.points * e.qty, 0);
}

export function totalModels(army: ArmyEntry[]): number {
  return army.reduce((sum, e) => sum + e.qty, 0);
}

/** Number of units in an army (sum of quantities) — the army-cap metric. */
export function totalUnits(army: ArmyEntry[]): number {
  return army.reduce((sum, e) => sum + e.qty, 0);
}

/** Encode the army as a compact, URL-safe string: "id.qty.w-w_id.qty". */
export function encodeArmy(army: ArmyEntry[]): string {
  return army
    .map((e) => {
      const lo = e.loadout?.length ? `.${e.loadout.join('-')}` : '';
      return `${e.id}.${e.qty}${lo}`;
    })
    .join('_');
}

/** Parse the "ids" share param into [id, qty, loadout] tuples. */
export function decodeArmy(value: string): Array<[number, number, number[]]> {
  return value
    .split('_')
    .map((part): [number, number, number[]] => {
      const [id, qty, lo] = part.split('.');
      const loadout = lo ? lo.split('-').map(Number).filter(Number.isFinite) : [];
      return [Number(id), Math.max(1, Number(qty) || 1), loadout];
    })
    .filter(([id]) => Number.isFinite(id) && id >= 0);
}
