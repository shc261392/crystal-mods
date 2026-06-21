// Army builder: localStorage-backed list with live totals, faction breakdown
// and URL sharing (?ids=id.qty_id.qty).

import unitsData from '../data/units.json';
import type { Unit } from '../lib/types';
import {
  type ArmyEntry,
  decodeArmy,
  encodeArmy,
  getArmy,
  saveArmy,
  totalModels,
  totalPoints,
} from './army-store';

const units = unitsData as Unit[];
const unitById = new Map(units.map((u) => [u.id, u]));

function unitSlug(u: Unit): string {
  const s = u.name
    .toLowerCase()
    .replace(/['’]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
  return `${u.id}-${s}`;
}

export function initArmyBuilder(): void {
  const select = document.getElementById('add-unit') as HTMLSelectElement | null;
  const addBtn = document.getElementById('add-btn');
  const list = document.getElementById('army-list');
  const empty = document.getElementById('empty');
  if (!select || !list) return;
  // Non-null alias for use inside the nested render() closure.
  const listEl = list;

  select.innerHTML = [...units]
    .sort((a, b) => a.name.localeCompare(b.name))
    .map(
      (u) => `<option value="${u.id}">${u.name} — ${u.pointCost} pts (${u.factionName})</option>`,
    )
    .join('');

  let army: ArmyEntry[] = getArmy();

  // If a shared list is present in the URL, it takes precedence.
  const shared = new URLSearchParams(location.search).get('ids');
  if (shared) {
    army = decodeArmy(shared)
      .map(([id, qty]): ArmyEntry | null => {
        const u = unitById.get(id);
        if (!u) return null;
        return { id: u.id, name: u.name, points: u.pointCost, faction: u.factionName, qty };
      })
      .filter((e): e is ArmyEntry => e !== null);
    saveArmy(army);
    history.replaceState(null, '', location.pathname);
  }

  function persist(): void {
    saveArmy(army);
  }

  function render(): void {
    if (empty) empty.style.display = army.length ? 'none' : '';
    listEl.innerHTML = army
      .map((e) => {
        const u = unitById.get(e.id);
        const href = u ? `/units/${unitSlug(u)}` : '#';
        return `<li class="flex items-center gap-3 rounded-lg bg-[var(--color-base)] border border-[var(--color-border)] px-3 py-2.5" data-id="${e.id}">
          <span class="flex-1 min-w-0">
            <a href="${href}" class="font-semibold text-sm truncate block hover:text-[var(--color-gold)]">${e.name}</a>
            <span class="text-xs text-[var(--color-faint)]">${e.faction} · ${e.points} pts each</span>
          </span>
          <span class="flex items-center gap-1.5 shrink-0">
            <button type="button" data-act="dec" class="btn btn-ghost !px-2 !py-1 text-base leading-none" aria-label="Decrease">−</button>
            <span class="w-7 text-center font-bold tabular-nums">${e.qty}</span>
            <button type="button" data-act="inc" class="btn btn-ghost !px-2 !py-1 text-base leading-none" aria-label="Increase">+</button>
          </span>
          <span class="w-16 text-right font-bold text-[var(--color-gold-dim)] tabular-nums shrink-0">${e.points * e.qty}</span>
          <button type="button" data-act="del" class="text-[var(--color-faint)] hover:text-[var(--color-blood)] shrink-0" aria-label="Remove">✕</button>
        </li>`;
      })
      .join('');

    setText('sum-points', String(totalPoints(army)));
    setText('sum-units', String(army.length));
    setText('sum-models', String(totalModels(army)));
    renderFactions();
  }

  function renderFactions(): void {
    const box = document.getElementById('faction-breakdown');
    if (!box) return;
    if (army.length === 0) {
      box.innerHTML = '<p class="text-sm text-[var(--color-faint)]">No factions yet.</p>';
      return;
    }
    const totals = new Map<string, number>();
    for (const e of army) {
      totals.set(e.faction, (totals.get(e.faction) ?? 0) + e.points * e.qty);
    }
    box.innerHTML = `<p class="label mb-1">By faction</p>${[...totals.entries()]
      .sort((a, b) => b[1] - a[1])
      .map(
        ([name, pts]) =>
          `<div class="flex justify-between text-sm"><span class="text-[var(--color-muted)] truncate">${name}</span><span class="font-semibold tabular-nums">${pts}</span></div>`,
      )
      .join('')}`;
  }

  function setText(id: string, value: string): void {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  function add(id: number): void {
    const u = unitById.get(id);
    if (!u) return;
    const existing = army.find((e) => e.id === id);
    if (existing) existing.qty += 1;
    else army.push({ id: u.id, name: u.name, points: u.pointCost, faction: u.factionName, qty: 1 });
    persist();
    render();
  }

  addBtn?.addEventListener('click', () => add(Number(select.value)));

  list.addEventListener('click', (ev) => {
    const btn = (ev.target as HTMLElement).closest('button[data-act]');
    if (!btn) return;
    const li = btn.closest('li');
    const id = Number(li?.getAttribute('data-id'));
    const entry = army.find((e) => e.id === id);
    if (!entry) return;
    const act = btn.getAttribute('data-act');
    if (act === 'inc') entry.qty += 1;
    else if (act === 'dec') entry.qty = Math.max(1, entry.qty - 1);
    else if (act === 'del') army = army.filter((e) => e.id !== id);
    persist();
    render();
  });

  document.getElementById('share-btn')?.addEventListener('click', async () => {
    if (army.length === 0) {
      toast('Add units first');
      return;
    }
    const url = `${location.origin}/army-builder?ids=${encodeArmy(army)}`;
    try {
      await navigator.clipboard.writeText(url);
      toast('Share link copied');
    } catch {
      toast(url);
    }
  });

  document.getElementById('clear-btn')?.addEventListener('click', () => {
    army = [];
    persist();
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
