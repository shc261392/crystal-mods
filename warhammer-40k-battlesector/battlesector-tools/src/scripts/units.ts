// Client-side filtering/sorting for the units browser. Operates on the
// server-rendered cards via data-* attributes and syncs state to the URL so
// any filtered view is shareable.

type SortKey =
  | 'tier-name'
  | 'name'
  | 'name-desc'
  | 'points-desc'
  | 'points-asc'
  | 'hp-desc'
  | 'hp-asc'
  | 'armor-desc'
  | 'armor-asc'
  | 'move-desc'
  | 'move-asc';

import { addToArmyLocked, getActiveArmyFaction } from './army-store';
import { applyI18n, roleName, t, tf } from './i18n';
import { pageSignal } from './reinit';

const DATASET_TAGS_KEY: keyof DOMStringMap = 'tags';

/** Briefly flash a card's add control green (success) or red (rejected). */
function flashAdd(el: HTMLElement, ok: boolean): void {
  const cls = ok ? 'text-[var(--color-gold)]' : 'text-[var(--color-blood)]';
  el.classList.add(cls, 'scale-110');
  window.setTimeout(() => el.classList.remove(cls, 'scale-110'), 600);
}

/** Transient bottom toast (created on demand; shared across calls). */
function showArmyToast(message: string): void {
  let toast = document.getElementById('army-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'army-toast';
    toast.className =
      'fixed bottom-24 lg:bottom-6 left-1/2 -translate-x-1/2 z-[140] px-4 py-2 rounded-lg bg-[var(--color-elevated)] border border-[var(--color-border)] text-sm font-semibold shadow-2xl transition-opacity duration-200';
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.classList.remove('opacity-0');
  window.clearTimeout((toast as HTMLElement & { _t?: number })._t);
  (toast as HTMLElement & { _t?: number })._t = window.setTimeout(() => {
    toast?.classList.add('opacity-0');
  }, 2000);
}

function num(el: HTMLElement, key: string): number {
  return Number(el.dataset[key] ?? 0);
}

function text(el: HTMLElement, key: string): string {
  return el.dataset[key] ?? '';
}

function displayName(el: HTMLElement): string {
  return el.querySelector('h3')?.textContent?.trim() ?? text(el, 'name');
}

// The list scroll position captured when a rail row is pressed, so it can be
// restored verbatim after a client navigation (the persisted rail must not move
// at all — no focus-scroll nudge, no reflow shift).
let railSavedScroll: number | null = null;

// Filter params owned by the units browser. Kept at module scope so the URL
// reflector below can run outside the main initializer closure.
const UNITS_FILTER_KEYS = ['q', 'faction', 'role', 'sort', 'campaign', 'tags'];

/** True on the units list page or any unit detail page (`/units` or `/units/…`). */
function inUnitsArea(): boolean {
  const path = location.pathname.replace(/\/$/, '');
  return path === '/units' || path.startsWith('/units/');
}

/**
 * Reflect the active filters (stored in sessionStorage) in the URL — on the
 * list page AND on a unit's detail page. This keeps the filter shareable when a
 * unit is selected (e.g. /units/2000-…?faction=Necrons) and reapplies it after
 * each client navigation, while preserving any non-filter params (compare/ids).
 */
function reflectFiltersInUrl(): void {
  if (!inUnitsArea()) return;
  let stored = '';
  try {
    stored = sessionStorage.getItem('bs.units.filters') ?? '';
  } catch {
    stored = '';
  }
  const params = new URLSearchParams(location.search);
  for (const k of UNITS_FILTER_KEYS) params.delete(k);
  for (const [k, v] of new URLSearchParams(stored)) params.set(k, v);
  const qs = params.toString();
  const nextSearch = qs ? `?${qs}` : '';
  if (location.search !== nextSearch) {
    history.replaceState(history.state, '', `${location.pathname}${nextSearch}`);
  }
}

/**
 * The rail is a persisted island (`transition:persist`), so its server-baked
 * `aria-current` highlight is stale after a client navigation. Recompute the
 * selected row from the current URL. Only scroll it into view on the very first
 * (deep-link) load — never on later navigations, so the list stays completely
 * still when switching units.
 */
function syncCurrentRow(grid: HTMLElement, scrollIntoView: boolean): void {
  const path = location.pathname.replace(/\/$/, '');
  let current: HTMLElement | null = null;
  for (const row of grid.querySelectorAll<HTMLElement>('.unit-card')) {
    const href = row.getAttribute('href')?.replace(/\/$/, '');
    if (href && href === path) {
      row.setAttribute('aria-current', 'page');
      current = row;
    } else {
      row.removeAttribute('aria-current');
    }
  }
  // Keep the filter query on the URL after every navigation (incl. detail
  // pages). Skipped on the very first load — see initUnitsBrowser, which runs
  // this only after filter state has been hydrated (otherwise it would wipe a
  // deep-linked ?faction=… before it is read).
  if (scrollIntoView && current) {
    const gRect = grid.getBoundingClientRect();
    const rRect = current.getBoundingClientRect();
    grid.scrollTop += rRect.top - gRect.top - (grid.clientHeight - current.clientHeight) / 2;
  } else if (!scrollIntoView && railSavedScroll !== null) {
    // Navigation: pin the list exactly where it was when the row was pressed,
    // undoing any focus-scroll nudge or reflow so the rail never moves.
    grid.scrollTop = railSavedScroll;
  }
}

export function initUnitsBrowser(): void {
  const grid = document.getElementById('grid');
  if (!grid) return;

  // Whether this is the first initialization of the persisted rail.
  const firstInit = grid.getAttribute('data-rail-init') !== '1';

  // Keep the selected-row highlight in sync on every navigation, WITHOUT
  // scrolling — switching units must leave the list scroll position untouched.
  // (The one-time deep-link scroll happens after filters apply, below.)
  syncCurrentRow(grid, false);

  // The rail persists across client navigations, so its elements are NOT
  // replaced and their listeners survive. Bind them (and hydrate filter state)
  // only once to avoid stacking duplicate handlers on every navigation.
  if (!firstInit) {
    // On a client navigation (e.g. selecting a unit), carry the already-loaded
    // filters onto the new URL so the filter stays shareable on detail pages.
    reflectFiltersInUrl();
    return;
  }
  grid.setAttribute('data-rail-init', '1');

  const q = document.getElementById('q') as HTMLInputElement | null;
  const factionBar = document.getElementById('faction-bar');
  const role = document.getElementById('role') as HTMLSelectElement | null;
  const sort = document.getElementById('sort') as HTMLSelectElement | null;
  const showCampaign = document.getElementById(
    'show-campaign-units-browser',
  ) as HTMLInputElement | null;
  const tagFilter = document.getElementById('unit-tag-filter');
  const count = document.getElementById('count');
  const empty = document.getElementById('empty');
  const reset = document.getElementById('reset');
  const filtersToggle = document.getElementById('filters-toggle');
  const filtersBody = document.getElementById('filters-body');
  const filtersCountBadge = document.getElementById('filters-count-badge');
  if (!grid || !q || !factionBar || !role || !sort || !tagFilter || !showCampaign) return;
  const roleSelect = role;
  const showCampaignInput = showCampaign;

  const cards = Array.from(grid.querySelectorAll<HTMLElement>('.unit-card'));
  const factionBtns = Array.from(factionBar.querySelectorAll<HTMLButtonElement>('.faction-btn'));

  // Warm the browser HTTP cache for every image (portrait, weapon, ability) used
  // by a faction's cards the moment that faction is selected, so scrolling the
  // filtered grid never waits on lazy image loads. The R2 asset URLs are stable
  // and content-addressed, so the browser dedupes/caches them consistently.
  const preloadedFactions = new Set<string>();
  function preloadFactionImages(faction: string): void {
    if (preloadedFactions.has(faction)) return;
    preloadedFactions.add(faction);
    const urls = new Set<string>();
    for (const card of cards) {
      if (faction && text(card, 'faction') !== faction) continue;
      for (const img of card.querySelectorAll<HTMLImageElement>('img[src]')) {
        const src = img.getAttribute('src');
        if (src) urls.add(src);
      }
    }
    for (const url of urls) {
      const img = new Image();
      img.decoding = 'async';
      img.src = url;
    }
  }

  // Classes applied to the active faction button.
  const ACTIVE = [
    '!text-[var(--color-gold)]',
    '!border-[var(--color-gold-dim)]',
    'bg-[color-mix(in_oklab,var(--color-gold)_14%,transparent)]',
  ];

  const defaultFaction = '';
  let activeFaction = defaultFaction;
  const selectedTags = new Set<string>();
  const tagButtons = Array.from(tagFilter.querySelectorAll<HTMLButtonElement>('button[data-tag]'));

  // Hydrate controls from the URL on the list page, or from the session-stored
  // filter state (so the rail stays filtered when navigating to a detail page).
  const urlParams = new URLSearchParams(location.search);
  const FILTER_KEYS = ['q', 'faction', 'role', 'sort', 'campaign', 'tags'];
  const hasUrlFilters = FILTER_KEYS.some((k) => urlParams.has(k));
  const params = hasUrlFilters
    ? urlParams
    : new URLSearchParams(sessionStorage.getItem('bs.units.filters') ?? '');
  if (params.get('q')) q.value = params.get('q') ?? '';
  const urlFaction = params.get('faction');
  if (urlFaction && factionBtns.some((b) => text(b, 'faction') === urlFaction)) {
    activeFaction = urlFaction;
  }
  if (params.get('role')) role.value = params.get('role') ?? '';
  if (params.get('sort')) sort.value = params.get('sort') ?? 'tier-name';
  showCampaign.checked = params.get('campaign') === '1';
  const tags = (params.get('tags') ?? '')
    .split(',')
    .map((t) => t.trim())
    .filter(Boolean);
  for (const t of tags) selectedTags.add(t);

  function paintFactionButtons(): void {
    for (const b of factionBtns) {
      const on = text(b, 'faction') === activeFaction;
      b.classList.toggle('is-active', on);
      for (const c of ACTIVE) b.classList.toggle(c, on);
      b.setAttribute('aria-selected', on ? 'true' : 'false');
    }
  }

  function syncUrl(): void {
    const p = new URLSearchParams();
    if (q?.value) p.set('q', q.value);
    if (activeFaction && activeFaction !== defaultFaction) p.set('faction', activeFaction);
    if (role?.value) p.set('role', role.value);
    if (sort && sort.value !== 'tier-name') p.set('sort', sort.value);
    if (showCampaignInput.checked) p.set('campaign', '1');
    if (selectedTags.size > 0) p.set('tags', [...selectedTags].sort().join(','));
    const qs = p.toString();
    try {
      sessionStorage.setItem('bs.units.filters', qs);
    } catch {
      // sessionStorage may be unavailable; filtering still works in-page.
    }
    // Reflect the filters in the URL — on the list page AND on a unit's detail
    // page — so the filter is always shareable. Preserves history.state and any
    // non-filter params (compare/ids).
    reflectFiltersInUrl();
  }

  function compare(a: HTMLElement, b: HTMLElement, key: SortKey): number {
    switch (key) {
      case 'points-desc':
        return num(b, 'points') - num(a, 'points');
      case 'points-asc':
        return num(a, 'points') - num(b, 'points');
      case 'hp-desc':
        return num(b, 'hp') - num(a, 'hp');
      case 'hp-asc':
        return num(a, 'hp') - num(b, 'hp');
      case 'armor-desc':
        return num(b, 'armor') - num(a, 'armor');
      case 'armor-asc':
        return num(a, 'armor') - num(b, 'armor');
      case 'move-desc':
        return num(b, 'move') - num(a, 'move');
      case 'move-asc':
        return num(a, 'move') - num(b, 'move');
      case 'tier-name': {
        const tier = num(a, 'tierRank') - num(b, 'tierRank');
        if (tier !== 0) return tier;
        return displayName(a).localeCompare(displayName(b));
      }
      case 'name-desc':
        return displayName(b).localeCompare(displayName(a));
      default:
        return displayName(a).localeCompare(displayName(b));
    }
  }

  function paintTagButtons(): void {
    for (const b of tagButtons) {
      const tag = b.getAttribute('data-tag') ?? '';
      const on = selectedTags.has(tag);
      b.classList.toggle('!text-[var(--color-gold)]', on);
      b.classList.toggle('!border-[var(--color-gold-dim)]', on);
      b.classList.toggle('bg-[color-mix(in_oklab,var(--color-gold)_14%,transparent)]', on);
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
    }
  }

  function localizeRoleOptions(): void {
    for (const opt of Array.from(roleSelect.options)) {
      const id = Number(opt.getAttribute('data-role-id'));
      if (!Number.isFinite(id)) continue;
      opt.textContent = roleName(id, opt.value);
    }
  }

  function activeFilterCount(): number {
    let n = 0;
    if (q?.value.trim()) n++;
    if (activeFaction && activeFaction !== defaultFaction) n++;
    if (role?.value) n++;
    if (sort && sort.value !== 'tier-name') n++;
    if (showCampaignInput.checked) n++;
    n += selectedTags.size;
    return n;
  }

  function updateFilterBadge(): void {
    if (!filtersCountBadge) return;
    const n = activeFilterCount();
    if (n > 0) {
      filtersCountBadge.textContent = String(n);
      filtersCountBadge.classList.remove('hidden');
    } else {
      filtersCountBadge.textContent = '';
      filtersCountBadge.classList.add('hidden');
    }
  }

  // The server renders cards already in the default 'tier-name' order, so we
  // must NOT re-append them on initial load (that causes a visible reflow/jump).
  // Only physically reorder the DOM once a non-default sort has been applied.
  let domReordered = false;

  function apply(): void {
    const term = q?.value.trim().toLowerCase() ?? '';
    const rol = role?.value ?? '';
    let visible = 0;
    let scopeTotal = 0;

    for (const card of cards) {
      const inFaction = !activeFaction || text(card, 'faction') === activeFaction;
      if (inFaction) scopeTotal++;
      const cardTags = new Set(
        (card.dataset[DATASET_TAGS_KEY] ?? '')
          .split(',')
          .map((t) => t.trim())
          .filter(Boolean),
      );
      const matchesTags = [...selectedTags].every((tag) => cardTags.has(tag));
      const matches =
        inFaction &&
        (!term || displayName(card).toLowerCase().includes(term)) &&
        (!rol || text(card, 'role') === rol) &&
        (showCampaignInput.checked || !cardTags.has('campaign')) &&
        matchesTags;
      card.style.display = matches ? '' : 'none';
      if (matches) visible++;
    }

    const sortKey = (sort?.value as SortKey) ?? 'tier-name';
    if (sortKey !== 'tier-name' || domReordered) {
      const ordered = [...cards]
        .filter((c) => c.style.display !== 'none')
        .sort((a, b) => compare(a, b, sortKey));
      for (const c of ordered) grid?.appendChild(c);
      domReordered = sortKey !== 'tier-name';
    }

    if (count) {
      count.textContent = tf('common.count.unitsVisible', {
        visible,
        total: scopeTotal,
      });
    }
    empty?.classList.toggle('hidden', visible !== 0);
    syncUrl();
    updateFilterBadge();
  }

  for (const b of factionBtns) {
    b.addEventListener('click', () => {
      // Read the button's faction verbatim. The "All factions" button carries an
      // empty data-faction, so we must NOT fall back to the current selection
      // (that made "All factions" impossible to re-select after picking one).
      activeFaction = text(b, 'faction');
      paintFactionButtons();
      preloadFactionImages(activeFaction);
      apply();
    });
  }
  q.addEventListener('input', apply);
  role.addEventListener('change', apply);
  sort.addEventListener('change', apply);
  showCampaignInput.addEventListener('change', apply);
  tagFilter.addEventListener('click', (event) => {
    const btn = (event.target as HTMLElement).closest(
      'button[data-tag]',
    ) as HTMLButtonElement | null;
    if (!btn) return;
    const tag = btn.getAttribute('data-tag');
    if (!tag) return;
    if (selectedTags.has(tag)) selectedTags.delete(tag);
    else selectedTags.add(tag);
    paintTagButtons();
    apply();
  });
  reset?.addEventListener('click', () => {
    q.value = '';
    activeFaction = defaultFaction;
    role.value = '';
    sort.value = 'tier-name';
    selectedTags.clear();
    paintFactionButtons();
    paintTagButtons();
    apply();
  });

  // Mobile: toggle the collapsible filter body so it never blocks the unit grid.
  if (filtersToggle && filtersBody) {
    const toggle = filtersToggle;
    const body = filtersBody;
    toggle.addEventListener('click', () => {
      const open = body.classList.toggle('hidden');
      // `open` is the post-toggle hidden state, so expanded === !hidden.
      toggle.setAttribute('aria-expanded', open ? 'false' : 'true');
    });
  }

  const signal = pageSignal('units');

  // Record the list scroll position when a row is pressed, so syncCurrentRow can
  // restore it verbatim after the client navigation (rail must not move at all).
  grid.addEventListener(
    'pointerdown',
    () => {
      railSavedScroll = grid.scrollTop;
    },
    { signal },
  );

  // Copy a shareable link that reproduces the current filters. Uses the same
  // filter query the URL/sessionStorage carry, so it works from a detail page
  // too (where the address bar shows the unit, not the filters).
  document.getElementById('copy-filters')?.addEventListener(
    'click',
    async () => {
      // On the list page, copy exactly what's in the address bar (the live
      // filter query). On a detail page, rebuild it from the stored filters.
      let qs = '';
      const onList = location.pathname.replace(/\/$/, '') === '/units';
      if (onList) {
        qs = location.search.replace(/^\?/, '');
      } else {
        try {
          qs = sessionStorage.getItem('bs.units.filters') ?? '';
        } catch {
          qs = '';
        }
      }
      const url = `${location.origin}/units${qs ? `?${qs}` : ''}`;
      try {
        await navigator.clipboard.writeText(url);
        showArmyToast(t('toast.linkCopied'));
      } catch {
        showArmyToast(url);
      }
    },
    { signal },
  );

  window.addEventListener(
    'bs:locale-changed',
    () => {
      applyI18n();
      localizeRoleOptions();
      apply();
    },
    { signal },
  );

  // Quick "+ Army" on each card: add to the active army (faction-locked) without
  // opening the detail page, then reveal the army drawer.
  grid.addEventListener(
    'click',
    (event) => {
      const add = (event.target as HTMLElement).closest<HTMLElement>('[data-army-add]');
      if (!add) return;
      event.preventDefault();
      event.stopPropagation();
      const id = num(add, 'armyId');
      const name = text(add, 'armyName');
      const points = num(add, 'armyPoints');
      const faction = text(add, 'armyFaction');
      if (!Number.isFinite(id) || id <= 0) return;
      const result = addToArmyLocked({ id, name, points, faction });
      if (result.ok) {
        document.dispatchEvent(new CustomEvent('bs:army-changed'));
        flashAdd(add, true);
      } else {
        flashAdd(add, false);
        showArmyToast(
          result.reason === 'cap'
            ? tf('army.capToast', { cap: result.cap })
            : tf('army.lockedToast', { faction: result.lockedTo }),
        );
      }
    },
    { signal },
  );

  // Dim the "+" on cards that can't be added because the active army is locked
  // to another faction, so the lock is obvious before clicking.
  function updateAddButtons(): void {
    const locked = getActiveArmyFaction();
    for (const btn of document.querySelectorAll<HTMLElement>('#grid [data-army-add]')) {
      const disabled = locked !== null && text(btn, 'armyFaction') !== locked;
      btn.classList.toggle('opacity-30', disabled);
      btn.classList.toggle('grayscale', disabled);
      btn.setAttribute(
        'title',
        disabled ? tf('army.lockedToast', { faction: locked }) : 'Add to army',
      );
    }
  }
  document.addEventListener('bs:army-changed', updateAddButtons, { signal });

  applyI18n();
  localizeRoleOptions();
  paintFactionButtons();
  paintTagButtons();
  apply();
  updateAddButtons();
  // One-time deep-link scroll: centre the current unit's row after filters have
  // been applied. Only runs on first init (later navigations return early).
  syncCurrentRow(grid, true);
  // Preload images for a faction that was pre-selected via the URL.
  if (activeFaction) preloadFactionImages(activeFaction);
}
