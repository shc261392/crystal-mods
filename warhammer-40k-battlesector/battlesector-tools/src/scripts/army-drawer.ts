// Global army drawer controller. Renders the multi-army store into the
// persistent drawer shell (components/ArmyDrawer.astro) and wires all actions:
// open/close, army switch/create/rename/delete, entry qty/remove, clear, share.
//
// The drawer DOM uses transition:persist, so it (and its directly-bound element
// listeners) survive ClientRouter navigations — bound once via a dataset guard.
// Document-level listeners (toggle button, Escape) are re-bound each navigation
// through pageSignal so they never target a stale/removed node.

import unitsData from '../data/units.json';
import weaponsData from '../data/weapons.json';
import { damageRange } from '../lib/combat';
import type { Unit, Weapon } from '../lib/types';
import { resolveWeaponType, weaponTypeMeta } from '../lib/weapon-display';
import {
  ARMY_UNIT_CAP,
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
  totalPoints,
  totalUnits,
} from './army-store';
import { unitName } from './i18n';
import { getFactionEmblem, getUnitPortrait, getWeaponPortrait, getWeaponTypeIcon } from './images';
import { pageSignal } from './reinit';

const unitById = new Map((unitsData as Unit[]).map((u) => [u.id, u]));
const weaponById = new Map((weaponsData as Weapon[]).map((w) => [w.id, w]));
// Faction name -> id, so we can resolve an army's faction emblem from its
// stored faction name.
const factionIdByName = new Map((unitsData as Unit[]).map((u) => [u.factionName, u.faction]));

/** Stable per-entry key: unit id + loadout, so the same unit with different
 * loadouts are distinct rows. */
function entryKey(e: ArmyEntry): string {
  return `${e.id}:${(e.loadout ?? []).join('-')}`;
}

/** A weapon's in-game icon, falling back to its type icon. */
function weaponIcon(w: Weapon): string | null {
  return getWeaponPortrait(w.icon) ?? getWeaponTypeIcon(resolveWeaponType(w));
}

/** Multiline weapon stat summary shown on hover — mirrors the weapon card's
 * notation (damage range, accuracy, hits, AP). One value per line. */
function weaponStatText(w: Weapon): string {
  const dmg = damageRange(w.damage);
  const hits = w.numAttacks * Math.max(1, w.shotsPerAttack || 1);
  const acc = w.isMelee && w.accuracy <= 0 ? 'Melee' : `${w.accuracy}%`;
  const lines = [
    w.name,
    weaponTypeMeta(w).label,
    `${dmg.min}–${dmg.max} dmg`,
    acc,
    `${hits} hits`,
    `AP ${w.armorPiercing}`,
  ];
  if (w.pistol) lines.push('Pistol');
  return lines.join('\n');
}

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

  // Totals: unit count out of the cap, plus points.
  const pts = qs<HTMLElement>(root, '[data-army-total-points]');
  const units = qs<HTMLElement>(root, '[data-army-total-units]');
  if (pts) pts.textContent = String(totalPoints(active.entries));
  if (units) units.textContent = `${totalUnits(active.entries)}/${ARMY_UNIT_CAP}`;
}

function entryRow(e: ArmyEntry): string {
  const unit = unitById.get(e.id);
  const showLoadout = unit ? hasLoadoutChoice(unit) : false;
  const loadout = unit ? normalizeLoadout(unit, e.loadout) : [];
  const portrait = unit ? (getUnitPortrait(unit.name, unit.portrait) ?? '') : '';
  const roleColor = unit?.roleColor ?? 'var(--color-border)';
  // Display the localized short name (matches the unit card), not the raw
  // faction-prefixed data name.
  const displayName = unitName(e.id, e.name);
  const icon = portrait
    ? `<img src="${portrait}" alt="" width="40" height="40" class="w-full h-full object-cover object-top" />`
    : `<span class="grid place-items-center w-full h-full text-xs font-black" style="background:${roleColor}">${escapeHtml(
        displayName.slice(0, 1),
      )}</span>`;
  const loadoutBtn = showLoadout
    ? `<button type="button" data-entry-loadout-toggle class="btn btn-ghost h-7 w-7 !px-0" aria-label="Loadout" title="Change loadout">
         <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M14.5 3.5 3 15v6h6L20.5 9.5M14.5 3.5 20.5 9.5M14.5 3.5 18 0l6 6-3.5 3.5"/></svg>
       </button>`
    : '';
  // Icon-based weapon selection (no dropdown). Each option shows the weapon
  // icon + point cost; hover reveals its stats via the shared tooltip system.
  const loadoutPanel =
    showLoadout && unit
      ? `<div data-entry-loadout class="hidden mt-2 pt-2 border-t border-[var(--color-border)] flex flex-col gap-2">${unit.weaponSlots
          .map((slot, i) => {
            if (slot.options.length <= 1) return '';
            const opts = slot.options
              .map((o) => {
                const w = weaponById.get(o.weaponId);
                const wIcon = w ? weaponIcon(w) : null;
                const selected = o.weaponId === loadout[i];
                const tip = w ? weaponStatText(w) : o.name;
                const cost = o.pointCost ? `+${o.pointCost}` : '';
                const inner = wIcon
                  ? `<img src="${wIcon}" alt="" class="w-8 h-8 object-contain p-0.5" />`
                  : `<span class="text-[10px] font-bold">${escapeHtml(o.name.slice(0, 2))}</span>`;
                const costBadge = cost
                  ? `<span class="absolute -bottom-1 -right-1 text-[9px] font-bold leading-none px-1 py-px rounded bg-[var(--color-elevated)] border border-[var(--color-border)] tabular-nums">${cost}</span>`
                  : '';
                return `<button type="button" data-entry-slot="${i}" data-weapon-id="${o.weaponId}" aria-pressed="${selected}" aria-label="${escapeHtml(o.name)}" class="tooltip-target relative grid place-items-center w-11 h-11 rounded-md border-2 bg-black/30 ${selected ? 'border-[var(--color-gold)]' : 'border-[var(--color-border)] hover:border-[var(--color-border-strong)]'}" data-tooltip="${escapeHtml(tip)}">${inner}${costBadge}</button>`;
              })
              .join('');
            return `<div class="flex flex-col gap-1"><span class="text-[10px] uppercase tracking-wide text-[var(--color-faint)]">Slot ${i + 1}</span><div class="flex flex-wrap gap-1.5">${opts}</div></div>`;
          })
          .join('')}</div>`
      : '';
  return `
    <div class="surface p-2" data-entry-key="${entryKey(e)}">
      <div class="flex items-start gap-2.5">
        <span class="w-10 h-10 rounded-md overflow-hidden shrink-0 border-2" style="border-color:${roleColor}">${icon}</span>
        <div class="min-w-0 flex-1">
          <div class="flex items-start justify-between gap-2">
            <p class="text-sm font-semibold truncate mt-0.5">${escapeHtml(displayName)}</p>
            <div class="text-right shrink-0">
              <p class="text-[9px] uppercase tracking-wide text-[var(--color-faint)] leading-none">PTS</p>
              <p class="font-black text-lg text-[var(--color-gold)] leading-tight tabular-nums">${e.points}</p>
            </div>
          </div>
          <div class="flex items-center justify-end gap-0.5 mt-1">
            ${loadoutBtn}
            <button type="button" data-entry-dec class="btn btn-ghost h-7 w-7 !px-0" aria-label="Decrease">−</button>
            <span class="tabular-nums text-sm w-6 text-center" data-entry-qty>${e.qty}</span>
            <button type="button" data-entry-inc class="btn btn-ghost h-7 w-7 !px-0" aria-label="Increase">+</button>
            <button type="button" data-entry-remove class="btn btn-ghost h-7 w-7 !px-0 text-[var(--color-blood)]" aria-label="Remove">×</button>
          </div>
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

  // Entry qty/remove/loadout-toggle/weapon-select via delegation.
  qs<HTMLElement>(root, '[data-army-entries]')?.addEventListener('click', (e) => {
    const target = e.target as HTMLElement;
    const rowEl = target.closest<HTMLElement>('[data-entry-key]');
    if (!rowEl) return;
    const key = rowEl.getAttribute('data-entry-key');
    const active = getActiveArmy();
    const entry = active.entries.find((x) => entryKey(x) === key);
    if (!entry) return;
    // Loadout expand/collapse doesn't mutate the store — toggle in place.
    if (target.closest('[data-entry-loadout-toggle]')) {
      qs<HTMLElement>(rowEl, '[data-entry-loadout]')?.classList.toggle('hidden');
      return;
    }
    // Weapon icon selection: change this entry's loadout (merging duplicates).
    const optBtn = target.closest<HTMLElement>('[data-entry-slot]');
    if (optBtn) {
      const unit = unitById.get(entry.id);
      if (!unit) return;
      const slot = Number(optBtn.getAttribute('data-entry-slot'));
      const weaponId = Number(optBtn.getAttribute('data-weapon-id'));
      if (!Number.isFinite(slot) || !Number.isFinite(weaponId)) return;
      const current = normalizeLoadout(unit, entry.loadout);
      const next = [...current];
      next[slot] = weaponId;
      // Match on the entry's stored loadout signature (may be the empty
      // default) — not the normalized form — so the right row is found.
      setEntryLoadout(entry.id, entry.loadout ?? [], next, loadoutCost(unit, next));
      render(root);
      updateMiniBar();
      updateArmyBadge();
      // Re-expand the (possibly re-keyed / merged) row we were editing.
      const newKey = `${entry.id}:${next.join('-')}`;
      qs<HTMLElement>(
        qs<HTMLElement>(root, `[data-entry-key="${newKey}"]`) ?? root,
        '[data-entry-loadout]',
      )?.classList.remove('hidden');
      return;
    }
    if (target.closest('[data-entry-inc]')) {
      if (totalUnits(active.entries) >= ARMY_UNIT_CAP) return;
      entry.qty += 1;
    } else if (target.closest('[data-entry-dec]')) entry.qty = Math.max(0, entry.qty - 1);
    else if (target.closest('[data-entry-remove]')) entry.qty = 0;
    else return;
    const next: ArmyEntry[] = active.entries.filter((x) =>
      entryKey(x) === key ? entry.qty > 0 : true,
    );
    saveArmy(next);
    render(root);
    updateMiniBar();
    updateArmyBadge();
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

/** Reflect the active army's unit count on the nav army button(s). */
function updateArmyBadge(): void {
  const active = getActiveArmy();
  const count = totalUnits(active.entries);
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
  const units = totalUnits(active.entries);
  const root = document.getElementById('army-drawer-root');
  const drawerOpen = root ? !root.classList.contains('hidden') : false;
  if (units > 0 && !drawerOpen) {
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
    // Faction is conveyed by the emblem; show the cap progress + points.
    if (nameEl) nameEl.textContent = `${units}/${ARMY_UNIT_CAP}`;
    if (statsEl) statsEl.textContent = `${totalPoints(active.entries)} pts`;
  } else {
    bar.classList.add('hidden');
    bar.classList.remove('flex');
  }
}
