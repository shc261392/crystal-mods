// Compare MODE for the units two-pane. A "Compare" toggle in the rail turns
// row clicks into multi-select (up to 4); the side-by-side comparison renders
// in the index page's detail pane. Selection + mode persist across navigation
// via sessionStorage, and a shareable URL (/units?compare=1&ids=1,2,3).

import unitsData from '../data/units.json';
import type { Unit } from '../lib/types';
import { factionName, roleName, t, tf, unitName } from './i18n';
import { pageSignal } from './reinit';

const units = (unitsData as Unit[]).filter((u) => u.faction !== 4);
const unitById = new Map(units.map((u) => [u.id, u]));
const MAX = 4;
const IDS_KEY = 'bs.compare.ids';
const MODE_KEY = 'bs.compare.mode';

interface Row {
  label: string;
  get: (u: Unit) => number | string;
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
  { label: 'common.evasion', get: (u) => u.evasion, best: 'high' },
  { label: 'common.movement', get: (u) => u.maxMovementPoints, best: 'high' },
  { label: 'common.actionPoints', get: (u) => u.maxActionPoints, best: 'high' },
  { label: 'unitDetail.stat.meleeAccuracy', get: (u) => u.meleeAccuracy, best: 'high' },
  { label: 'common.momentumPerKill', get: (u) => u.momentumPerModelDeath, best: 'high' },
];

function unitSlug(u: Unit): string {
  const s = u.name
    .toLowerCase()
    .replace(/['’]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
  return `${u.id}-${s}`;
}

function readIds(): number[] {
  try {
    const raw = sessionStorage.getItem(IDS_KEY);
    if (!raw) return [];
    return raw
      .split(',')
      .map(Number)
      .filter((n) => unitById.has(n))
      .slice(0, MAX);
  } catch {
    return [];
  }
}

function writeIds(ids: number[]): void {
  try {
    sessionStorage.setItem(IDS_KEY, ids.join(','));
  } catch {
    // sessionStorage unavailable; in-memory state still works this session.
  }
}

function readMode(): boolean {
  try {
    return sessionStorage.getItem(MODE_KEY) === '1';
  } catch {
    return false;
  }
}

function writeMode(on: boolean): void {
  try {
    sessionStorage.setItem(MODE_KEY, on ? '1' : '0');
  } catch {
    // ignore
  }
}

function bestValue(row: Row, selected: Unit[]): number | null {
  if (!row.best) return null;
  const nums = selected.map((u) => row.get(u)).filter((v): v is number => typeof v === 'number');
  if (nums.length < 2) return null;
  return row.best === 'high' ? Math.max(...nums) : Math.min(...nums);
}

let toastTimer: number | undefined;
function toast(message: string): void {
  let el = document.getElementById('compare-toast');
  if (!el) {
    el = document.createElement('div');
    el.id = 'compare-toast';
    el.className =
      'fixed bottom-24 lg:bottom-6 left-1/2 -translate-x-1/2 z-[140] px-4 py-2 rounded-lg bg-[var(--color-elevated)] border border-[var(--color-border)] text-sm font-semibold shadow-2xl transition-opacity duration-200';
    document.body.appendChild(el);
  }
  el.textContent = message;
  el.classList.remove('opacity-0');
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => el?.classList.add('opacity-0'), 1800);
}

export function initCompareMode(): void {
  const toggle = document.querySelector<HTMLElement>('[data-compare-toggle]');
  if (!toggle) return;

  const onUnitsIndex = location.pathname.replace(/\/$/, '') === '/units';
  const bar = document.querySelector<HTMLElement>('[data-compare-bar]');
  const countEl = document.querySelector<HTMLElement>('[data-compare-count]');
  const panel = document.querySelector<HTMLElement>('[data-compare-panel]');
  const prompt = document.querySelector<HTMLElement>('[data-compare-prompt]');

  // Hydrate mode + selection from the URL (shareable) then sessionStorage.
  const params = new URLSearchParams(location.search);
  if (onUnitsIndex && (params.get('compare') === '1' || params.has('ids'))) {
    writeMode(true);
    const urlIds = (params.get('ids') ?? '')
      .split(',')
      .map(Number)
      .filter((n) => unitById.has(n))
      .slice(0, MAX);
    if (urlIds.length > 0) writeIds(urlIds);
  }

  let mode = readMode();
  let ids = readIds();

  function paintToggle(): void {
    toggle?.setAttribute('aria-pressed', mode ? 'true' : 'false');
    document.body.toggleAttribute('data-compare-mode', mode);
    bar?.classList.toggle('hidden', !mode);
  }

  function paintRows(): void {
    for (const row of document.querySelectorAll<HTMLElement>('[data-units-rail] .unit-card')) {
      const id = Number(row.getAttribute('data-id'));
      row.toggleAttribute('data-compare-selected', mode && ids.includes(id));
    }
  }

  function syncUrl(): void {
    if (!onUnitsIndex) return;
    const p = new URLSearchParams(location.search);
    if (mode) p.set('compare', '1');
    else p.delete('compare');
    if (ids.length > 0) p.set('ids', ids.join(','));
    else p.delete('ids');
    const qs = p.toString();
    history.replaceState(history.state, '', qs ? `?${qs}` : location.pathname);
  }

  function renderPanel(): void {
    if (countEl) countEl.textContent = String(ids.length);
    if (!onUnitsIndex || !panel || !prompt) return;

    if (!mode) {
      panel.classList.add('hidden');
      prompt.classList.remove('hidden');
      return;
    }
    prompt.classList.add('hidden');
    panel.classList.remove('hidden');

    const selected = ids.map((id) => unitById.get(id)).filter((u): u is Unit => u !== undefined);
    if (selected.length === 0) {
      panel.innerHTML = `<div class="surface grid place-items-center min-h-[70vh] text-center p-8">
        <div>
          <p class="eyebrow mb-2">${t('nav.compare')}</p>
          <p class="text-lg font-semibold text-[var(--color-muted)]">${t('compare.pickPrompt')}</p>
        </div>
      </div>`;
      return;
    }

    const head = `<tr>
      <th class="text-left p-3 sticky left-0 bg-[var(--color-surface)] z-10 label">${t('compare.table.stat')}</th>
      ${selected
        .map(
          (u) => `<th class="p-3 text-left min-w-[10rem]">
            <a href="/units/${unitSlug(u)}" class="font-bold hover:text-[var(--color-gold)] block">${unitName(u.id, u.name)}</a>
            <span class="text-xs text-[var(--color-faint)] font-normal">${factionName(u.faction, u.factionName)}</span>
            <button type="button" data-compare-remove="${u.id}" class="block mt-1 text-xs text-[var(--color-faint)] hover:text-[var(--color-blood)]">${t('compare.button.remove')}</button>
          </th>`,
        )
        .join('')}
    </tr>`;

    const bodyHtml = rows
      .map((row, i) => {
        const best = bestValue(row, selected);
        const cells = selected
          .map((u) => {
            const v = row.get(u);
            const isBest = best !== null && v === best;
            const color = isBest ? 'text-[var(--color-gold)] font-bold' : '';
            return `<td class="p-3 tabular-nums ${color}">${v}${isBest ? ' ★' : ''}</td>`;
          })
          .join('');
        return `<tr class="${i % 2 ? 'bg-[color-mix(in_oklab,var(--color-base)_50%,transparent)]' : ''}">
          <td class="p-3 text-[var(--color-muted)] sticky left-0 bg-[var(--color-surface)] z-10 font-medium">${t(row.label)}</td>
          ${cells}
        </tr>`;
      })
      .join('');

    panel.innerHTML = `<div class="overflow-x-auto surface">
      <table class="w-full border-collapse text-sm">
        <thead>${head}</thead>
        <tbody>${bodyHtml}</tbody>
      </table>
    </div>`;
  }

  function paintAll(): void {
    paintToggle();
    paintRows();
    renderPanel();
    syncUrl();
  }

  function toggleUnit(id: number): void {
    if (ids.includes(id)) {
      ids = ids.filter((x) => x !== id);
    } else {
      if (ids.length >= MAX) {
        toast(tf('compare.toast.maximum', { max: MAX }));
        return;
      }
      ids = [...ids, id];
    }
    writeIds(ids);
    paintAll();
  }

  const signal = pageSignal('compare-mode');

  toggle.addEventListener(
    'click',
    () => {
      // From a unit's detail page, compare lives on the index — go there first.
      if (!onUnitsIndex) {
        writeMode(true);
        location.assign('/units?compare=1');
        return;
      }
      mode = !mode;
      writeMode(mode);
      paintAll();
    },
    { signal },
  );

  // Intercept rail row clicks while in compare mode (capture phase, before the
  // anchor navigates), toggling selection instead of opening the unit.
  document.addEventListener(
    'click',
    (event) => {
      if (!mode) return;
      const target = event.target as HTMLElement;
      if (target.closest('[data-army-add]')) return; // let the +army control work
      const row = target.closest<HTMLElement>('[data-units-rail] .unit-card');
      if (!row) return;
      event.preventDefault();
      event.stopPropagation();
      toggleUnit(Number(row.getAttribute('data-id')));
    },
    { capture: true, signal },
  );

  // Remove / clear / copy controls.
  document.addEventListener(
    'click',
    (event) => {
      const rm = (event.target as HTMLElement).closest<HTMLElement>('[data-compare-remove]');
      if (rm) {
        ids = ids.filter((x) => x !== Number(rm.getAttribute('data-compare-remove')));
        writeIds(ids);
        paintAll();
      }
    },
    { signal },
  );

  document.querySelector('[data-compare-clear]')?.addEventListener(
    'click',
    () => {
      ids = [];
      writeIds(ids);
      paintAll();
    },
    { signal },
  );

  document.querySelector('[data-compare-copy]')?.addEventListener(
    'click',
    async () => {
      if (ids.length === 0) {
        toast(t('compare.pickPrompt'));
        return;
      }
      const url = `${location.origin}/units?compare=1&ids=${ids.join(',')}`;
      try {
        await navigator.clipboard.writeText(url);
        toast(t('toast.linkCopied'));
      } catch {
        toast(url);
      }
    },
    { signal },
  );

  window.addEventListener('bs:locale-changed', renderPanel, { signal });

  paintAll();
}
