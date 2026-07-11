// Global army drawer controller. Renders the multi-army store into the
// persistent drawer shell (components/ArmyDrawer.astro) and wires all actions:
// open/close, army switch/create/rename/delete, entry qty/remove, clear, share.
//
// The drawer DOM uses transition:persist, so it (and its directly-bound element
// listeners) survive ClientRouter navigations — bound once via a dataset guard.
// Document-level listeners (toggle button, Escape) are re-bound each navigation
// through pageSignal so they never target a stale/removed node.

import {
  type ArmyEntry,
  createArmy,
  deleteArmy,
  encodeArmy,
  getActiveArmy,
  getArmies,
  renameArmy,
  saveArmy,
  setActiveArmy,
  totalModels,
  totalPoints,
} from './army-store';
import { pageSignal } from './reinit';

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
  return `
    <div class="surface flex items-center gap-2 p-2" data-entry-id="${e.id}">
      <div class="min-w-0 flex-1">
        <p class="text-sm font-semibold truncate">${escapeHtml(e.name)}</p>
        <p class="text-xs text-[var(--color-faint)] truncate">${escapeHtml(e.faction)} · ${
          e.points
        } pts</p>
      </div>
      <div class="flex items-center gap-1 shrink-0">
        <button type="button" data-entry-dec class="btn btn-ghost h-7 w-7 !px-0" aria-label="Decrease">−</button>
        <span class="tabular-nums text-sm w-6 text-center" data-entry-qty>${e.qty}</span>
        <button type="button" data-entry-inc class="btn btn-ghost h-7 w-7 !px-0" aria-label="Increase">+</button>
        <button type="button" data-entry-remove class="btn btn-ghost h-7 w-7 !px-0 text-[var(--color-blood)]" aria-label="Remove">×</button>
      </div>
    </div>`;
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
  window.setTimeout(() => root.classList.add('hidden'), 200);
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

  // Entry qty/remove via delegation.
  qs<HTMLElement>(root, '[data-army-entries]')?.addEventListener('click', (e) => {
    const target = e.target as HTMLElement;
    const rowEl = target.closest<HTMLElement>('[data-entry-id]');
    if (!rowEl) return;
    const id = Number(rowEl.getAttribute('data-entry-id'));
    const active = getActiveArmy();
    const entry = active.entries.find((x) => x.id === id);
    if (!entry) return;
    if (target.closest('[data-entry-inc]')) entry.qty += 1;
    else if (target.closest('[data-entry-dec]')) entry.qty = Math.max(0, entry.qty - 1);
    else if (target.closest('[data-entry-remove]')) entry.qty = 0;
    else return;
    const next: ArmyEntry[] = active.entries.filter((x) => (x.id === id ? entry.qty > 0 : true));
    saveArmy(next);
    render(root);
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

  // Refresh when other pages mutate the army (e.g. unit-detail "+ Army").
  document.addEventListener('bs:army-changed', () => render(root), { signal });
}
