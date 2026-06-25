// Shared army-list store backed by localStorage. Used by the unit detail page
// ("+ Army Builder") and the army builder page. State is a list of entries with
// a unit id, quantity and a snapshot of display fields so the builder can render
// without re-importing the full dataset.

export interface ArmyEntry {
  id: number;
  name: string;
  points: number;
  faction: string;
  qty: number;
  /** Selected weapon ids (one per slot). Absent = default loadout. */
  loadout?: number[];
}

const KEY = 'bs.army.v1';

export function getArmy(): ArmyEntry[] {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as ArmyEntry[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function saveArmy(army: ArmyEntry[]): void {
  localStorage.setItem(KEY, JSON.stringify(army));
}

export function addToArmy(entry: Omit<ArmyEntry, 'qty'>): ArmyEntry[] {
  const army = getArmy();
  const existing = army.find((e) => e.id === entry.id);
  if (existing) {
    existing.qty += 1;
  } else {
    army.push({ ...entry, qty: 1 });
  }
  saveArmy(army);
  return army;
}

export function totalPoints(army: ArmyEntry[]): number {
  return army.reduce((sum, e) => sum + e.points * e.qty, 0);
}

export function totalModels(army: ArmyEntry[]): number {
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
