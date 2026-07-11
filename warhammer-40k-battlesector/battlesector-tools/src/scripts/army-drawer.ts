// Global army drawer controller. Renders the multi-army store into the
// persistent drawer shell (components/ArmyDrawer.astro) and wires all actions:
// open/close, army switch/create/rename/delete, entry qty/remove, clear, share.
//
// The drawer DOM uses transition:persist, so it (and its directly-bound element
// listeners) survive ClientRouter navigations — bound once via a dataset guard.
// Document-level listeners (toggle button, Escape) are re-bound each navigation
// through pageSignal so they never target a stale/removed node.

import unitsData from '../data/units.json';
import type { Unit } from '../lib/types';
import {
  type ArmyEntry,
  createArmy,
  deleteArmy,
  encodeArmy,
  getActiveArmy,
  getActiveArmyFaction,
  getArmies,
  renameArmy,
  saveArmy,
  setActiveArmy,
  setEntryLoadout,
  totalModels,
  totalPoints,
} from './army-store';
import { getFactionEmblem } from './images';
import { pageSignal } from './reinit';

const unitById = new Map((unitsData as Unit[]).map((u) => [u.id, u]));
// Faction name -> id, so we can resolve an army's faction emblem from its
// stored faction name.
const factionIdByName = new Map((unitsData as Unit[]).map((u) => [u.factionName, u.faction]));

function factionEmblemForName(name: string | null): string | null {
  if (!name) return null;
  const id = factionIdByName.get(name);
  return id === undefined ? null : getFactionEmblem(id);
}

/** The default loadout: the zero-cost option in each weapon slot. */
function defaultLoadout(u: Unit): number[] {
  return u.weaponSlots.map((slot) => {
    const free = slot.options.find((o) => (o.pointCost ?? 0) === 0) ?? slot.options[0];
    return free?.weaponId ?? -1;
  });
}

/** Total points for a unit with a given loadout = base + selected upgrade costs. */
function loadoutCost(u: Unit, loadout: number[]): number {
  let pts = u.pointCost;
  u.weaponSlots.forEach((slot, i) => {
    const opt = slot.options.find((o) => o.weaponId === loadout[i]);
    if (opt) pts += opt.pointCost ?? 0;
  });
  return pts;
}

/** True when a unit has at least one slot offering a real choice. */
function hasLoadoutChoice(u: Unit): boolean {
  return u.weaponSlots.some((slot) => slot.options.length > 1);
}

function qs<T extends HTMLElement>(root: ParentNode, sel: string): T | null {
  return root.querySelector<T>(sel);
}

function render(root: HTMLElement): void {
  const armies = getArmies();
  const active = getActiveArmy();

  // Switcher options
  const switcher = qs<HTMLSelectElement>(root, '[data-army-switcher]');
  if (switcher) {
    switcher.innerHTML = armies
      .map(
        (a) =>
          `<option value="${a.id}"${a.id === active.id ? ' selected' : ''}>${escapeHtml(
            a.name,
          )} (${a.entries.reduce((s, e) => s + e.qty, 0)})</option>`,
      )
      .join('');
  }

  // Name input
  const nameInput = qs<HTMLInputElement>(root, '[data-army-name]');
  if (nameInput && document.activeElement !== nameInput) nameInput.value = active.name;

  // Faction lock indicator
  const faction = getActiveArmyFaction();
  const factionEmblem = qs<HTMLImageElement>(root, '[data-army-faction-emblem]');
  const factionLabel = qs<HTMLElement>(root, '[data-army-faction-label]');
  const emblemUrl = factionEmblemForName(faction);
  if (factionEmblem) {
    if (emblemUrl) {
      factionEmblem.src = emblemUrl;
      factionEmblem.classList.remove('hidden');
    } else {
      factionEmblem.classList.add('hidden');
    }
  }
  if (factionLabel) {
    factionLabel.textContent = faction
      ? `${faction} · faction locked`
      : 'Any faction — the first unit sets the lock';
  }

  // Entries
  const list = qs<HTMLElement>(root, '[data-army-entries]');
  const empty = qs<HTMLElement>(root, '[data-army-empty]');
  if (list && empty) {
    if (active.entries.length === 0) {
      list.classList.add('hidden');
      empty.classList.remove('hidden');
      empty.classList.add('grid');
      list.innerHTML = '';
    } else {
      list.classList.remove('hidden');
      empty.classList.add('hidden');
      empty.classList.remove('grid');
      list.innerHTML = active.entries.map(entryRow).join('');
    }
  }

  // Totals
  const pts = qs<HTMLElement>(root, '[data-army-total-points]');
  const models = qs<HTMLElement>(root, '[data-army-total-models]');
  if (pts) pts.textContent = String(totalPoints(active.entries));
  if (models) models.textContent = String(totalModels(active.entries));
}

function entryRow(e: ArmyEntry): string {
  const unit = unitById.get(e.id);
  const showLoadout = unit ? hasLoadoutChoice(unit) : false;
  const loadout = unit ? normalizeLoadout(unit, e.loadout) : [];
  const loadoutBtn = showLoadout
    ? `<button type="button" data-entry-loadout-toggle class="btn btn-ghost h-7 w-7 !px-0" aria-label="Loadout" title="Loadout">
         <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M14.5 3.5 3 15v6h6L20.5 9.5M14.5 3.5 20.5 9.5M14.5 3.5 18 0l6 6-3.5 3.5"/></svg>
       </button>`
    : '';
  const loadoutPanel =
    showLoadout && unit
      ? `<div data-entry-loadout class="hidden mt-2 pt-2 border-t border-[var(--color-border)] flex flex-col gap-1.5">${unit.weaponSlots
          .map((slot, i) => {
            if (slot.options.length <= 1) return '';
            const opts = slot.options
              .map((o) => {
                const cost = o.pointCost ? ` (+${o.pointCost})` : '';
                const sel = o.weaponId === loadout[i] ? ' selected' : '';
                return `<option value="${o.weaponId}"${sel}>${escapeHtml(o.name)}${cost}</option>`;
              })
              .join('');
            return `<select data-entry-slot="${i}" class="select h-8 text-xs">${opts}</select>`;
          })
          .join('')}</div>`
      : '';
  return `
    <div class="surface p-2" data-entry-id="${e.id}">
      <div class="flex items-center gap-2">
        <div class="min-w-0 flex-1">
          <p class="text-sm font-semibold truncate">${escapeHtml(e.name)}</p>
          <p class="text-xs text-[var(--color-faint)] truncate">${escapeHtml(e.faction)} · ${
            e.points
          } pts</p>
        </div>
        <div class="flex items-center gap-1 shrink-0">
          ${loadoutBtn}
          <button type="button" data-entry-dec class="btn btn-ghost h-7 w-7 !px-0" aria-label="Decrease">−</button>
          <span class="tabular-nums text-sm w-6 text-center" data-entry-qty>${e.qty}</span>
          <button type="button" data-entry-inc class="btn btn-ghost h-7 w-7 !px-0" aria-label="Increase">+</button>
          <button type="button" data-entry-remove class="btn btn-ghost h-7 w-7 !px-0 text-[var(--color-blood)]" aria-label="Remove">×</button>
        </div>
      </div>
      ${loadoutPanel}
    </div>`;
}

function normalizeLoadout(u: Unit, loadout?: number[]): number[] {
  const base = [...(loadout?.length ? loadout : defaultLoadout(u))];
  while (base.length < u.weaponSlots.length) base.push(defaultLoadout(u)[base.length] ?? -1);
  return base;
}

function escapeHtml(s: string): string {
  return s.replace(
    /[&<>"']/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c] ?? c,
  );
}

function open(root: HTMLElement): void {
  root.classList.remove('hidden');
  root.setAttribute('aria-hidden', 'false');
  render(root);
  updateMiniBar();
  // Next frame so the transition runs from the hidden state.
  requestAnimationFrame(() => {
    qs<HTMLElement>(root, '[data-army-backdrop]')?.classList.add('opacity-100');
    const panel = qs<HTMLElement>(root, '[data-army-panel]');
    panel?.classList.remove('translate-x-full');
  });
}

function close(root: HTMLElement): void {
  qs<HTMLElement>(root, '[data-army-backdrop]')?.classList.remove('opacity-100');
  qs<HTMLElement>(root, '[data-army-panel]')?.classList.add('translate-x-full');
  root.setAttribute('aria-hidden', 'true');
  window.setTimeout(() => {
    root.classList.add('hidden');
    updateMiniBar();
  }, 200);
}

function isOpen(root: HTMLElement): boolean {
  return !root.classList.contains('hidden');
}

/** Bind element-scoped listeners once (drawer persists across navigations). */
function bindOnce(root: HTMLElement): void {
  const BOUND = 'bound';
  if (root.dataset[BOUND] === '1') return;
  root.dataset[BOUND] = '1';

  qs<HTMLElement>(root, '[data-army-close]')?.addEventListener('click', () => close(root));
  qs<HTMLElement>(root, '[data-army-backdrop]')?.addEventListener('click', () => close(root));

  qs<HTMLSelectElement>(root, '[data-army-switcher]')?.addEventListener('change', (e) => {
    setActiveArmy((e.target as HTMLSelectElement).value);
    render(root);
  });

  qs<HTMLElement>(root, '[data-army-new]')?.addEventListener('click', () => {
    createArmy();
    render(root);
    qs<HTMLInputElement>(root, '[data-army-name]')?.focus();
  });

  qs<HTMLInputElement>(root, '[data-army-name]')?.addEventListener('input', (e) => {
    renameArmy(getActiveArmy().id, (e.target as HTMLInputElement).value);
    // Update the switcher label without stealing focus from the name field.
    const switcher = qs<HTMLSelectElement>(root, '[data-army-switcher]');
    const opt = switcher?.selectedOptions[0];
    if (opt)
      opt.textContent = `${(e.target as HTMLInputElement).value} (${getActiveArmy().entries.reduce((s, x) => s + x.qty, 0)})`;
  });

  qs<HTMLElement>(root, '[data-army-delete]')?.addEventListener('click', () => {
    const active = getActiveArmy();
    if (active.entries.length > 0 && !confirm(`Delete "${active.name}"?`)) return;
    deleteArmy(active.id);
    render(root);
  });

  qs<HTMLElement>(root, '[data-army-clear]')?.addEventListener('click', () => {
    if (getActiveArmy().entries.length === 0) return;
    if (!confirm('Clear all units from this army?')) return;
    saveArmy([]);
    render(root);
  });

  qs<HTMLElement>(root, '[data-army-share]')?.addEventListener('click', async (e) => {
    const btn = e.currentTarget as HTMLElement;
    const entries = getActiveArmy().entries;
    if (entries.length === 0) return;
    const url = `${location.origin}/army-builder?ids=${encodeArmy(entries)}`;
    try {
      await navigator.clipboard.writeText(url);
      const prev = btn.textContent;
      btn.textContent = '✓';
      window.setTimeout(() => {
        btn.textContent = prev;
      }, 1200);
    } catch {
      // ignore clipboard failures
    }
  });

  // Entry qty/remove/loadout-toggle via delegation.
  qs<HTMLElement>(root, '[data-army-entries]')?.addEventListener('click', (e) => {
    const target = e.target as HTMLElement;
    const rowEl = target.closest<HTMLElement>('[data-entry-id]');
    if (!rowEl) return;
    const id = Number(rowEl.getAttribute('data-entry-id'));
    const active = getActiveArmy();
    const entry = active.entries.find((x) => x.id === id);
    if (!entry) return;
    // Loadout expand/collapse doesn't mutate the store — toggle in place.
    if (target.closest('[data-entry-loadout-toggle]')) {
      qs<HTMLElement>(rowEl, '[data-entry-loadout]')?.classList.toggle('hidden');
      return;
    }
    if (target.closest('[data-entry-inc]')) entry.qty += 1;
    else if (target.closest('[data-entry-dec]')) entry.qty = Math.max(0, entry.qty - 1);
    else if (target.closest('[data-entry-remove]')) entry.qty = 0;
    else return;
    const next: ArmyEntry[] = active.entries.filter((x) => (x.id === id ? entry.qty > 0 : true));
    saveArmy(next);
    render(root);
  });

  // Weapon-loadout change: recompute the entry's points, keep the panel open.
  qs<HTMLElement>(root, '[data-army-entries]')?.addEventListener('change', (e) => {
    const sel = (e.target as HTMLElement).closest<HTMLSelectElement>('[data-entry-slot]');
    if (!sel) return;
    const rowEl = sel.closest<HTMLElement>('[data-entry-id]');
    if (!rowEl) return;
    const id = Number(rowEl.getAttribute('data-entry-id'));
    const unit = unitById.get(id);
    if (!unit) return;
    const loadout = [...rowEl.querySelectorAll<HTMLSelectElement>('[data-entry-slot]')].reduce(
      (acc, s) => {
        acc[Number(s.getAttribute('data-entry-slot'))] = Number(s.value);
        return acc;
      },
      normalizeLoadout(unit),
    );
    setEntryLoadout(id, loadout, loadoutCost(unit, loadout));
    render(root);
    // Re-expand the panel we were editing (render replaced the DOM).
    qs<HTMLElement>(
      qs<HTMLElement>(root, `[data-entry-id="${id}"]`) ?? root,
      '[data-entry-loadout]',
    )?.classList.remove('hidden');
  });
}

export function initArmyDrawer(): void {
  const root = document.getElementById('army-drawer-root');
  if (!root) return;
  bindOnce(root);
  render(root);

  const signal = pageSignal('army-drawer');

  // Toggle button lives in the (swapped) Nav — bind per navigation.
  document.addEventListener(
    'click',
    (e) => {
      if ((e.target as HTMLElement).closest('[data-army-toggle]')) {
        e.preventDefault();
        isOpen(root) ? close(root) : open(root);
      }
    },
    { signal },
  );

  document.addEventListener(
    'keydown',
    (e) => {
      if (e.key === 'Escape' && isOpen(root)) close(root);
    },
    { signal },
  );

  // Refresh (and badge) when other pages mutate the army (e.g. list/detail "+").
  document.addEventListener(
    'bs:army-changed',
    () => {
      render(root);
      updateArmyBadge();
    },
    { signal },
  );

  // Reveal the drawer when a unit is added from the list, so the army in
  // progress is always visible while building.
  document.addEventListener('bs:army-open', () => open(root), { signal });

  // The persistent mini-bar opens the full drawer.
  document.addEventListener(
    'click',
    (e) => {
      if ((e.target as HTMLElement).closest('[data-army-mini]')) open(root);
    },
    { signal },
  );

  updateArmyBadge();
}

/** Reflect the active army's model count on the nav army button(s). */
function updateArmyBadge(): void {
  const active = getActiveArmy();
  const count = totalModels(active.entries);
  for (const btn of document.querySelectorAll<HTMLElement>('[data-army-toggle]')) {
    let badge = btn.querySelector<HTMLElement>('[data-army-badge]');
    if (count > 0) {
      if (!badge) {
        badge = document.createElement('span');
        badge.setAttribute('data-army-badge', '');
        badge.className =
          'absolute -top-1 -right-1 min-w-[1.1rem] h-[1.1rem] px-1 grid place-items-center rounded-full bg-[var(--color-gold)] text-[var(--color-void)] text-[10px] font-bold tabular-nums pointer-events-none';
        btn.appendChild(badge);
      }
      badge.textContent = String(count);
    } else if (badge) {
      badge.remove();
    }
  }
  updateMiniBar();
}

/** Show a persistent mini-bar while the army has units and the drawer is closed. */
function updateMiniBar(): void {
  const bar = document.getElementById('army-mini-bar');
  if (!bar) return;
  const active = getActiveArmy();
  const models = totalModels(active.entries);
  const root = document.getElementById('army-drawer-root');
  const drawerOpen = root ? !root.classList.contains('hidden') : false;
  if (models > 0 && !drawerOpen) {
    bar.classList.remove('hidden');
    bar.classList.add('flex');
    const nameEl = bar.querySelector<HTMLElement>('[data-army-mini-name]');
    const statsEl = bar.querySelector<HTMLElement>('[data-army-mini-stats]');
    const emblemImg = bar.querySelector<HTMLImageElement>('[data-army-mini-emblem]');
    const iconSvg = bar.querySelector<HTMLElement>('[data-army-mini-icon]');
    const emblemUrl = factionEmblemForName(getActiveArmyFaction());
    if (emblemImg && iconSvg) {
      if (emblemUrl) {
        emblemImg.src = emblemUrl;
        emblemImg.classList.remove('hidden');
        iconSvg.classList.add('hidden');
      } else {
        emblemImg.classList.add('hidden');
        iconSvg.classList.remove('hidden');
      }
    }
    // Show faction so the lock is legible; fall back to the army name.
    if (nameEl) nameEl.textContent = getActiveArmyFaction() ?? active.name;
    if (statsEl) statsEl.textContent = `· ${models} · ${totalPoints(active.entries)} pts`;
  } else {
    bar.classList.add('hidden');
    bar.classList.remove('flex');
  }
}
