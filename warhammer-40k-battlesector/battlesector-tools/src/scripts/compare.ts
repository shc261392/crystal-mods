// Unit comparison: up to four units side by side with the best value per row
// highlighted. State syncs to the URL (?ids=1,2,3) for sharing.

import unitsData from '../data/units.json';
import type { Unit } from '../lib/types';
import { factionName, roleName, t, tf, unitName } from './i18n';

const units = (unitsData as Unit[]).filter((u) => u.faction !== 4);
const unitById = new Map(units.map((u) => [u.id, u]));
const MAX = 4;

interface Row {
  label: string;
  get: (u: Unit) => number | string;
  /** Direction for "best": higher or lower wins. null = no highlight. */
  best: 'high' | 'low' | null;
}

const rows: Row[] = [
  { label: 'common.faction', get: (u) => factionName(u.faction, u.factionName), best: null },
  { label: 'common.role', get: (u) => roleName(u.role, u.roleName), best: null },
  { label: 'common.points', get: (u) => u.pointCost, best: 'low' },
  { label: 'compare.row.totalHealth', get: (u) => u.totalHealth, best: 'high' },
  { label: 'compare.row.healthPerModel', get: (u) => u.maxHealth, best: 'high' },
  { label: 'common.models', get: (u) => u.members, best: 'high' },
  {
    label: 'common.armor',
    get: (u) => (u.armorProfile === 1 ? u.armorFront : u.armor),
    best: 'high',
  },
  { label: 'Evasion', get: (u) => u.evasion, best: 'high' },
  { label: 'common.movement', get: (u) => u.maxMovementPoints, best: 'high' },
  { label: 'Action Points', get: (u) => u.maxActionPoints, best: 'high' },
  { label: 'Melee Accuracy', get: (u) => u.meleeAccuracy, best: 'high' },
  { label: 'compare.row.momentumPerKill', get: (u) => u.momentumPerModelDeath, best: 'high' },
];

function unitSlug(u: Unit): string {
  const s = u.name
    .toLowerCase()
    .replace(/['’]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
  return `${u.id}-${s}`;
}

export function initCompare(): void {
  const select = document.getElementById('add-unit') as HTMLSelectElement | null;
  const head = document.getElementById('compare-head');
  const body = document.getElementById('compare-body');
  const wrap = document.getElementById('compare-wrap');
  const empty = document.getElementById('empty');
  if (!select || !head || !body || !wrap || !empty) return;
  // Non-null aliases: control-flow narrowing is not preserved inside the nested
  // closures below, so capture stable non-null references here.
  const headEl = head;
  const bodyEl = body;
  const wrapEl = wrap;
  const emptyEl = empty;

  select.innerHTML = [...units]
    .sort((a, b) => unitName(a.id, a.name).localeCompare(unitName(b.id, b.name)))
    .map(
      (u) =>
        `<option value="${u.id}">${unitName(u.id, u.name)} (${factionName(u.faction, u.factionName)})</option>`,
    )
    .join('');

  let ids: number[] = [];
  const shared = new URLSearchParams(location.search).get('ids');
  if (shared) {
    ids = shared
      .split(',')
      .map(Number)
      .filter((n) => unitById.has(n))
      .slice(0, MAX);
  }

  function syncUrl(): void {
    const qs = ids.length ? `?ids=${ids.join(',')}` : '';
    history.replaceState(null, '', `${location.pathname}${qs}`);
  }

  function bestValue(row: Row, selected: Unit[]): number | null {
    if (!row.best) return null;
    const nums = selected.map((u) => row.get(u)).filter((v): v is number => typeof v === 'number');
    if (nums.length < 2) return null;
    return row.best === 'high' ? Math.max(...nums) : Math.min(...nums);
  }

  function render(): void {
    const selected = ids.map((id) => unitById.get(id)).filter((u): u is Unit => u !== undefined);

    const hasUnits = selected.length > 0;
    wrapEl.classList.toggle('hidden', !hasUnits);
    emptyEl.classList.toggle('hidden', hasUnits);
    if (!hasUnits) {
      syncUrl();
      return;
    }

    headEl.innerHTML = `<tr>
      <th class="text-left p-3 sticky left-0 bg-[var(--color-surface)] z-10 label">${t('compare.table.stat')}</th>
      ${selected
        .map(
          (u) => `<th class="p-3 text-left min-w-[10rem]">
            <a href="/units/${unitSlug(u)}" class="font-bold hover:text-[var(--color-gold)] block">${unitName(u.id, u.name)}</a>
            <span class="text-xs text-[var(--color-faint)] font-normal">${factionName(u.faction, u.factionName)}</span>
            <button type="button" data-remove="${u.id}" class="block mt-1 text-xs text-[var(--color-faint)] hover:text-[var(--color-blood)]">${t('compare.button.remove')}</button>
          </th>`,
        )
        .join('')}
    </tr>`;

    bodyEl.innerHTML = rows
      .map((row, i) => {
        const best = bestValue(row, selected);
        const isHp = row.label.includes('Health');
        const cells = selected
          .map((u) => {
            const v = row.get(u);
            const isBest = best !== null && v === best;
            const color = isBest
              ? 'text-[var(--color-gold)] font-bold'
              : isHp
                ? 'text-[var(--color-hp)] font-semibold'
                : '';
            return `<td class="p-3 tabular-nums ${color}">${v}${isBest ? ' ★' : ''}</td>`;
          })
          .join('');
        return `<tr class="${i % 2 ? 'bg-[color-mix(in_oklab,var(--color-base)_50%,transparent)]' : ''}">
          <td class="p-3 text-[var(--color-muted)] sticky left-0 bg-[var(--color-surface)] z-10 font-medium">${t(row.label)}</td>
          ${cells}
        </tr>`;
      })
      .join('');

    syncUrl();
  }

  function add(id: number): void {
    if (ids.includes(id)) {
      toast(t('compare.toast.alreadyAdded'));
      return;
    }
    if (ids.length >= MAX) {
      toast(tf('compare.toast.maximum', { max: MAX }));
      return;
    }
    ids.push(id);
    render();
  }

  document.getElementById('add-btn')?.addEventListener('click', () => {
    add(Number(select.value));
  });

  head.addEventListener('click', (ev) => {
    const btn = (ev.target as HTMLElement).closest('button[data-remove]');
    if (!btn) return;
    const id = Number(btn.getAttribute('data-remove'));
    ids = ids.filter((x) => x !== id);
    render();
  });

  document.getElementById('clear-btn')?.addEventListener('click', () => {
    ids = [];
    render();
  });

  document.getElementById('share-btn')?.addEventListener('click', async () => {
    if (ids.length === 0) {
      toast(t('toast.addUnitsFirst'));
      return;
    }
    const url = `${location.origin}/compare?ids=${ids.join(',')}`;
    try {
      await navigator.clipboard.writeText(url);
      toast(t('toast.linkCopied'));
    } catch {
      toast(url);
    }
  });

  window.addEventListener('bs:locale-changed', () => {
    const current = select.value;
    select.innerHTML = [...units]
      .sort((a, b) => unitName(a.id, a.name).localeCompare(unitName(b.id, b.name)))
      .map(
        (u) =>
          `<option value="${u.id}">${unitName(u.id, u.name)} (${factionName(u.faction, u.factionName)})</option>`,
      )
      .join('');
    if (current) select.value = current;
    render();
  });

  function toast(message: string): void {
    const el = document.getElementById('toast');
    if (!el) return;
    el.textContent = message;
    el.classList.remove('hidden');
    window.setTimeout(() => el.classList.add('hidden'), 1600);
  }

  render();
}
