/**
 * Stat hexagon ("六邊形能力指數圖") — renders a 6-axis radar/hexagon SVG showing how
 * a unit or weapon ranks against the whole roster. Each axis is a quintile grade
 * (1–5) precomputed by scripts/generate-stat-ranks.ts; grade 5 reaches the
 * outermost ring.
 *
 * Pure string builder (no DOM) so it can render at build time via Astro
 * `set:html` AND client-side when the explorer swaps the detail pane.
 */

export interface AxisEntry {
  v: number;
  g: number;
  pr: number;
}
export type RankRecord = Record<string, AxisEntry>;

export interface HexAxis {
  key: string;
  /** English fallback label. */
  label: string;
  /** i18n UI key. */
  i18nKey: string;
  /** Format the raw value for the axis label. */
  fmt?: (v: number) => string;
}

export const UNIT_HEX_AXES: HexAxis[] = [
  { key: 'hp', label: 'HP', i18nKey: 'hex.u.hp' },
  { key: 'ap', label: 'AP', i18nKey: 'hex.u.ap' },
  { key: 'mp', label: 'MP', i18nKey: 'hex.u.mp' },
  { key: 'armor', label: 'Armor', i18nKey: 'hex.u.armor' },
  { key: 'dodge', label: 'Dodge', i18nKey: 'hex.u.dodge' },
  { key: 'pts', label: 'Points', i18nKey: 'hex.u.pts' },
];

const dmgFmt = (v: number): string => (Number.isInteger(v) ? String(v) : v.toFixed(1));

export const WEAPON_HEX_AXES: HexAxis[] = [
  { key: 'dmg3', label: 'Dmg A3', i18nKey: 'hex.w.dmg3', fmt: dmgFmt },
  { key: 'dmg6', label: 'Dmg A6', i18nKey: 'hex.w.dmg6', fmt: dmgFmt },
  { key: 'dmg9', label: 'Dmg A9', i18nKey: 'hex.w.dmg9', fmt: dmgFmt },
  { key: 'range', label: 'Range', i18nKey: 'hex.w.range' },
  { key: 'splash', label: 'Splash', i18nKey: 'hex.w.splash' },
  { key: 'hits', label: 'Hits', i18nKey: 'hex.w.hits' },
];

const GRADE_COLORS = [
  'var(--color-faint)', // 1
  'var(--color-muted)', // 2
  'var(--color-gold-dim)', // 3
  'var(--color-gold)', // 4
  'var(--color-hp)', // 5
];

const CX = 130;
const CY = 118;
const MAX_R = 82;
const LEVELS = 5;

function vertex(i: number, r: number): [number, number] {
  const angle = (-90 + 60 * i) * (Math.PI / 180);
  return [CX + r * Math.cos(angle), CY + r * Math.sin(angle)];
}

function poly(points: Array<[number, number]>): string {
  return points.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' ');
}

function esc(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/**
 * Build the hexagon SVG for a single entity's rank record.
 * @param rank precomputed axis grades keyed by axis key
 * @param axes axis configuration (UNIT_HEX_AXES or WEAPON_HEX_AXES)
 */
export function statHexagonHTML(rank: RankRecord | undefined, axes: HexAxis[]): string {
  if (!rank) return '';
  const n = axes.length;

  // Grid rings (levels 1..5)
  let grid = '';
  for (let lvl = 1; lvl <= LEVELS; lvl++) {
    const r = (MAX_R * lvl) / LEVELS;
    const pts = poly(Array.from({ length: n }, (_, i) => vertex(i, r)));
    grid += `<polygon points="${pts}" fill="none" stroke="var(--color-border)" stroke-width="1" opacity="${lvl === LEVELS ? 0.55 : 0.28}"/>`;
  }

  // Axis spokes
  let spokes = '';
  for (let i = 0; i < n; i++) {
    const [x, y] = vertex(i, MAX_R);
    spokes += `<line x1="${CX}" y1="${CY}" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}" stroke="var(--color-border)" stroke-width="1" opacity="0.28"/>`;
  }

  // Data polygon + dots
  const dataPts: Array<[number, number]> = [];
  let dots = '';
  let maxGrade = 1;
  axes.forEach((axis, i) => {
    const entry = rank[axis.key];
    const g = entry?.g ?? 1;
    maxGrade = Math.max(maxGrade, g);
    const r = (MAX_R * g) / LEVELS;
    const [x, y] = vertex(i, r);
    dataPts.push([x, y]);
    dots += `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="3" fill="${GRADE_COLORS[g - 1]}"/>`;
  });
  const shape = poly(dataPts);
  const accent = GRADE_COLORS[Math.min(5, maxGrade) - 1];

  // Axis labels + values
  let labels = '';
  axes.forEach((axis, i) => {
    const [lx, ly] = vertex(i, MAX_R + 16);
    const entry = rank[axis.key];
    const val = entry ? (axis.fmt ? axis.fmt(entry.v) : String(entry.v)) : '';
    const anchor = lx < CX - 6 ? 'end' : lx > CX + 6 ? 'start' : 'middle';
    const dy = ly < CY - 20 ? -2 : ly > CY + 20 ? 10 : 3;
    labels += `<text x="${lx.toFixed(1)}" y="${(ly + dy).toFixed(1)}" text-anchor="${anchor}" font-size="10" font-weight="700" fill="var(--color-muted)"><tspan data-i18n-ui="${axis.i18nKey}">${esc(axis.label)}</tspan><tspan dx="3" fill="var(--color-ink)">${esc(val)}</tspan></text>`;
  });

  return `<svg viewBox="-30 0 320 236" class="stat-hexagon w-full h-auto max-w-[300px]" role="img" aria-label="Stat index hexagon">${grid}${spokes}<polygon points="${shape}" fill="${accent}" fill-opacity="0.18" stroke="${accent}" stroke-width="2" stroke-linejoin="round"/>${dots}${labels}</svg>`;
}
