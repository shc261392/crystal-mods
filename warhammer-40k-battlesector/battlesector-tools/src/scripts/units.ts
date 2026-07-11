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

import { applyI18n, roleName, tf } from './i18n';
import { pageSignal } from './reinit';

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

export function initUnitsBrowser(): void {
  const grid = document.getElementById('grid');
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

  // Hydrate controls from URL
  const params = new URLSearchParams(location.search);
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
    history.replaceState(null, '', qs ? `?${qs}` : location.pathname);
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

    const ordered = [...cards]
      .filter((c) => c.style.display !== 'none')
      .sort((a, b) => compare(a, b, (sort?.value as SortKey) ?? 'tier-name'));
    for (const c of ordered) grid?.appendChild(c);

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

  window.addEventListener(
    'bs:locale-changed',
    () => {
      applyI18n();
      localizeRoleOptions();
      apply();
    },
    { signal: pageSignal('units') },
  );

  applyI18n();
  localizeRoleOptions();
  paintFactionButtons();
  paintTagButtons();
  apply();
  // Preload images for a faction that was pre-selected via the URL.
  if (activeFaction) preloadFactionImages(activeFaction);
}
