// Client-side filtering/sorting for the weapons browser.

import { applyI18n, t, tf } from './i18n';
import { pageSignal } from './reinit';

type SortKey =
  | 'name'
  | 'total-desc'
  | 'total-asc'
  | 'damage-desc'
  | 'damage-asc'
  | 'acc-desc'
  | 'acc-asc'
  | 'ap-desc'
  | 'ap-asc'
  | 'hits-desc'
  | 'hits-asc';

const DATASET_TAGS_KEY: keyof DOMStringMap = 'tags';

function num(el: HTMLElement, key: string): number {
  return Number(el.dataset[key] ?? 0);
}

function text(el: HTMLElement, key: string): string {
  return el.dataset[key] ?? '';
}

function displayName(el: HTMLElement): string {
  return el.querySelector('h3')?.textContent?.trim() ?? text(el, 'name');
}

// The list scroll captured on row press, restored after a client navigation so
// the persisted rail never moves (no focus-scroll nudge / reflow shift).
let railSavedScroll: number | null = null;

// Filter params owned by the weapons browser (module scope so the URL reflector
// can run outside the main initializer closure).
const WEAPONS_FILTER_KEYS = ['q', 'sort', 'tags', 'faction'];

/** True on the weapons list page or any weapon detail page. */
function inWeaponsArea(): boolean {
  const path = location.pathname.replace(/\/$/, '');
  return path === '/weapons' || path.startsWith('/weapons/');
}

/**
 * Reflect the active filters (stored in sessionStorage) in the URL — on the
 * list page AND on a weapon's detail page — so the filter stays shareable when a
 * weapon is selected, and reapplies after each client navigation.
 */
function reflectFiltersInUrl(): void {
  if (!inWeaponsArea()) return;
  let stored = '';
  try {
    stored = sessionStorage.getItem('bs.weapons.filters') ?? '';
  } catch {
    stored = '';
  }
  const params = new URLSearchParams(location.search);
  for (const k of WEAPONS_FILTER_KEYS) params.delete(k);
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
 * selected row from the current URL. Scroll into view only on the first
 * (deep-link) load; on navigation, pin the scroll exactly where it was.
 */
function syncCurrentRow(grid: HTMLElement, scrollIntoView: boolean): void {
  const path = location.pathname.replace(/\/$/, '');
  let current: HTMLElement | null = null;
  for (const row of grid.querySelectorAll<HTMLElement>('.weapon-card')) {
    const href = row.getAttribute('href')?.replace(/\/$/, '');
    if (href && href === path) {
      row.setAttribute('aria-current', 'page');
      current = row;
    } else {
      row.removeAttribute('aria-current');
    }
  }
  if (scrollIntoView && current) {
    const gRect = grid.getBoundingClientRect();
    const rRect = current.getBoundingClientRect();
    grid.scrollTop += rRect.top - gRect.top - (grid.clientHeight - current.clientHeight) / 2;
  } else if (!scrollIntoView && railSavedScroll !== null) {
    grid.scrollTop = railSavedScroll;
  }
}

export function initWeaponsBrowser(): void {
  const grid = document.getElementById('grid');
  if (!grid) return;

  // Whether this is the first initialization of the persisted rail.
  const firstInit = grid.getAttribute('data-rail-init') !== '1';

  // Update the selected-row highlight on every navigation WITHOUT scrolling.
  syncCurrentRow(grid, false);

  // Persisted rail: elements (and their listeners) survive navigations — bind
  // once and hydrate filter state once.
  if (!firstInit) {
    // Carry the already-loaded filters onto the new URL so the filter stays
    // shareable on weapon detail pages.
    reflectFiltersInUrl();
    return;
  }
  grid.setAttribute('data-rail-init', '1');

  const q = document.getElementById('q') as HTMLInputElement | null;
  const sort = document.getElementById('sort') as HTMLSelectElement | null;
  const tagFilter = document.getElementById('weapon-tag-filter');
  const typeFilter = document.getElementById('weapon-type-filter');
  const factionBar = document.getElementById('faction-bar');
  const count = document.getElementById('count');
  const empty = document.getElementById('empty');
  const reset = document.getElementById('reset');
  const filtersToggle = document.getElementById('filters-toggle');
  const filtersBody = document.getElementById('filters-body');
  const filtersCountBadge = document.getElementById('filters-count-badge');
  if (!q || !sort || !tagFilter) return;

  const cards = Array.from(grid.querySelectorAll<HTMLElement>('.weapon-card'));
  const selectedTags = new Set<string>();
  // Tag + type chips share the same data-tag filtering; collect both groups.
  const tagContainers = [typeFilter, tagFilter].filter((el): el is HTMLElement => el !== null);
  const tagButtons = tagContainers.flatMap((c) =>
    Array.from(c.querySelectorAll<HTMLButtonElement>('button[data-tag]')),
  );
  const factionBtns = factionBar
    ? Array.from(factionBar.querySelectorAll<HTMLButtonElement>('.faction-btn'))
    : [];
  let activeFactionId = '';

  const ACTIVE = [
    '!text-[var(--color-gold)]',
    '!border-[var(--color-gold-dim)]',
    'bg-[color-mix(in_oklab,var(--color-gold)_14%,transparent)]',
  ];

  // Hydrate controls from the URL on the list page, or from the session-stored
  // filter state (so the rail stays filtered when navigating to a detail page).
  const urlParams = new URLSearchParams(location.search);
  const FILTER_KEYS = ['q', 'sort', 'tags', 'faction'];
  const hasUrlFilters = FILTER_KEYS.some((k) => urlParams.has(k));
  const params = hasUrlFilters
    ? urlParams
    : new URLSearchParams(sessionStorage.getItem('bs.weapons.filters') ?? '');
  if (params.get('q')) q.value = params.get('q') ?? '';
  if (params.get('sort')) sort.value = params.get('sort') ?? 'name';
  if (params.get('faction')) activeFactionId = params.get('faction') ?? '';
  const tags = (params.get('tags') ?? '')
    .split(',')
    .map((t) => t.trim())
    .filter(Boolean);
  for (const t of tags) selectedTags.add(t);

  function syncUrl(): void {
    const p = new URLSearchParams();
    if (q?.value) p.set('q', q.value);
    if (sort && sort.value !== 'name') p.set('sort', sort.value);
    if (activeFactionId) p.set('faction', activeFactionId);
    if (selectedTags.size > 0) p.set('tags', [...selectedTags].sort().join(','));
    const qs = p.toString();
    try {
      sessionStorage.setItem('bs.weapons.filters', qs);
    } catch {
      // sessionStorage may be unavailable; filtering still works in-page.
    }
    // Reflect the filters in the URL — on the list page AND on a weapon's detail
    // page — so the filter is always shareable. Preserves history.state.
    reflectFiltersInUrl();
  }

  function updateFilterBadge(): void {
    if (!filtersCountBadge) return;
    const active =
      selectedTags.size + (sort && sort.value !== 'name' ? 1 : 0) + (activeFactionId ? 1 : 0);
    filtersCountBadge.textContent = String(active);
    filtersCountBadge.classList.toggle('hidden', active === 0);
  }

  function paintFactionButtons(): void {
    for (const b of factionBtns) {
      const on = (b.getAttribute('data-faction-id') ?? '') === activeFactionId;
      for (const c of ACTIVE) b.classList.toggle(c, on);
      b.setAttribute('aria-selected', on ? 'true' : 'false');
    }
  }

  function compare(a: HTMLElement, b: HTMLElement, key: SortKey): number {
    switch (key) {
      case 'total-desc':
        return num(b, 'total') - num(a, 'total');
      case 'total-asc':
        return num(a, 'total') - num(b, 'total');
      case 'damage-desc':
        return num(b, 'damage') - num(a, 'damage');
      case 'damage-asc':
        return num(a, 'damage') - num(b, 'damage');
      case 'acc-desc':
        return num(b, 'acc') - num(a, 'acc');
      case 'acc-asc':
        return num(a, 'acc') - num(b, 'acc');
      case 'ap-desc':
        return num(b, 'ap') - num(a, 'ap');
      case 'ap-asc':
        return num(a, 'ap') - num(b, 'ap');
      case 'hits-desc':
        return num(b, 'hits') - num(a, 'hits');
      case 'hits-asc':
        return num(a, 'hits') - num(b, 'hits');
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

  // Server renders cards already in the default 'name' order — avoid re-appending
  // them on initial load (that causes a visible reflow). Reorder only once a
  // non-default sort is chosen.
  let domReordered = false;

  function apply(): void {
    const term = q?.value.trim().toLowerCase() ?? '';
    let visible = 0;
    for (const card of cards) {
      const cardTags = new Set(
        (card.dataset[DATASET_TAGS_KEY] ?? '')
          .split(',')
          .map((t) => t.trim())
          .filter(Boolean),
      );
      const cardFactions = new Set(
        text(card, 'factionIds')
          .split(',')
          .map((f) => f.trim())
          .filter(Boolean),
      );
      const matchesTags = [...selectedTags].every((tag) => cardTags.has(tag));
      const matchesFaction = !activeFactionId || cardFactions.has(activeFactionId);
      const matches =
        (!term || displayName(card).toLowerCase().includes(term)) && matchesTags && matchesFaction;
      card.style.display = matches ? '' : 'none';
      if (matches) visible++;
    }
    const sortKey = (sort?.value as SortKey) ?? 'name';
    if (sortKey !== 'name' || domReordered) {
      const ordered = [...cards]
        .filter((c) => c.style.display !== 'none')
        .sort((a, b) => compare(a, b, sortKey));
      for (const c of ordered) grid?.appendChild(c);
      domReordered = sortKey !== 'name';
    }

    if (count) {
      count.textContent = tf('common.count.weaponsVisible', {
        visible,
        total: cards.length,
      });
    }
    empty?.classList.toggle('hidden', visible !== 0);
    syncUrl();
    updateFilterBadge();
  }

  q.addEventListener('input', apply);
  sort.addEventListener('change', apply);
  reset?.addEventListener('click', () => {
    q.value = '';
    sort.value = 'name';
    selectedTags.clear();
    activeFactionId = '';
    paintTagButtons();
    paintFactionButtons();
    apply();
  });

  for (const container of tagContainers) {
    container.addEventListener('click', (event) => {
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
  }

  for (const b of factionBtns) {
    b.addEventListener('click', () => {
      activeFactionId = b.getAttribute('data-faction-id') ?? '';
      paintFactionButtons();
      apply();
    });
  }

  // Collapsible filter body (so the narrow rail isn't cluttered).
  if (filtersToggle && filtersBody) {
    const toggle = filtersToggle;
    const body = filtersBody;
    toggle.addEventListener('click', () => {
      const open = body.classList.toggle('hidden');
      toggle.setAttribute('aria-expanded', open ? 'false' : 'true');
    });
  }

  const signal = pageSignal('weapons');

  // Record the list scroll on row press so syncCurrentRow can restore it after
  // the client navigation (rail must not move).
  grid.addEventListener(
    'pointerdown',
    () => {
      railSavedScroll = grid.scrollTop;
    },
    { signal },
  );

  // Copy a shareable link that reproduces the current filters (works from a
  // weapon detail page too, via the session-stored filter query).
  document.getElementById('copy-filters')?.addEventListener(
    'click',
    async () => {
      // On the list page, copy the live address-bar query; on a detail page,
      // rebuild from the stored filters.
      let qs = '';
      const onList = location.pathname.replace(/\/$/, '') === '/weapons';
      if (onList) {
        qs = location.search.replace(/^\?/, '');
      } else {
        try {
          qs = sessionStorage.getItem('bs.weapons.filters') ?? '';
        } catch {
          qs = '';
        }
      }
      const url = `${location.origin}/weapons${qs ? `?${qs}` : ''}`;
      let toast = document.getElementById('weapons-toast');
      if (!toast) {
        toast = document.createElement('div');
        toast.id = 'weapons-toast';
        toast.className =
          'fixed bottom-24 lg:bottom-6 left-1/2 -translate-x-1/2 z-[140] px-4 py-2 rounded-lg bg-[var(--color-elevated)] border border-[var(--color-border)] text-sm font-semibold shadow-2xl transition-opacity duration-200';
        document.body.appendChild(toast);
      }
      try {
        await navigator.clipboard.writeText(url);
        toast.textContent = t('toast.linkCopied');
      } catch {
        toast.textContent = url;
      }
      toast.classList.remove('opacity-0');
      window.setTimeout(() => toast?.classList.add('opacity-0'), 1800);
    },
    { signal },
  );

  window.addEventListener(
    'bs:locale-changed',
    () => {
      applyI18n();
      apply();
    },
    { signal },
  );

  applyI18n();
  paintTagButtons();
  paintFactionButtons();
  apply();
  // One-time deep-link scroll: centre the current weapon's row after filters.
  syncCurrentRow(grid, true);
}
