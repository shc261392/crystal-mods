// Client-side filtering/sorting for the weapons browser.

import { applyI18n, tf } from './i18n';
import { pageSignal } from './reinit';

type SortKey =
  | 'name'
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
  if (!firstInit) return;
  grid.setAttribute('data-rail-init', '1');

  const q = document.getElementById('q') as HTMLInputElement | null;
  const sort = document.getElementById('sort') as HTMLSelectElement | null;
  const tagFilter = document.getElementById('weapon-tag-filter');
  const count = document.getElementById('count');
  const empty = document.getElementById('empty');
  const reset = document.getElementById('reset');
  const filtersToggle = document.getElementById('filters-toggle');
  const filtersBody = document.getElementById('filters-body');
  const filtersCountBadge = document.getElementById('filters-count-badge');
  if (!q || !sort || !tagFilter) return;

  const cards = Array.from(grid.querySelectorAll<HTMLElement>('.weapon-card'));
  const selectedTags = new Set<string>();
  const tagButtons = Array.from(tagFilter.querySelectorAll<HTMLButtonElement>('button[data-tag]'));

  // Hydrate controls from the URL on the list page, or from the session-stored
  // filter state (so the rail stays filtered when navigating to a detail page).
  const urlParams = new URLSearchParams(location.search);
  const FILTER_KEYS = ['q', 'sort', 'tags'];
  const hasUrlFilters = FILTER_KEYS.some((k) => urlParams.has(k));
  const params = hasUrlFilters
    ? urlParams
    : new URLSearchParams(sessionStorage.getItem('bs.weapons.filters') ?? '');
  if (params.get('q')) q.value = params.get('q') ?? '';
  if (params.get('sort')) sort.value = params.get('sort') ?? 'name';
  const tags = (params.get('tags') ?? '')
    .split(',')
    .map((t) => t.trim())
    .filter(Boolean);
  for (const t of tags) selectedTags.add(t);

  function syncUrl(): void {
    const p = new URLSearchParams();
    if (q?.value) p.set('q', q.value);
    if (sort && sort.value !== 'name') p.set('sort', sort.value);
    if (selectedTags.size > 0) p.set('tags', [...selectedTags].sort().join(','));
    const qs = p.toString();
    try {
      sessionStorage.setItem('bs.weapons.filters', qs);
    } catch {
      // sessionStorage may be unavailable; filtering still works in-page.
    }
    // Only reflect filters in the URL on the list page, not on a weapon's detail
    // URL. Preserve ClientRouter's history.state (nulling it breaks back-nav).
    if (location.pathname.replace(/\/$/, '') === '/weapons') {
      history.replaceState(history.state, '', qs ? `?${qs}` : location.pathname);
    }
  }

  function updateFilterBadge(): void {
    if (!filtersCountBadge) return;
    const active = selectedTags.size + (sort && sort.value !== 'name' ? 1 : 0);
    filtersCountBadge.textContent = String(active);
    filtersCountBadge.classList.toggle('hidden', active === 0);
  }

  function compare(a: HTMLElement, b: HTMLElement, key: SortKey): number {
    switch (key) {
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
      const matchesTags = [...selectedTags].every((tag) => cardTags.has(tag));
      const matches = (!term || displayName(card).toLowerCase().includes(term)) && matchesTags;
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
    paintTagButtons();
    apply();
  });

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
  apply();
  // One-time deep-link scroll: centre the current weapon's row after filters.
  syncCurrentRow(grid, true);
}
