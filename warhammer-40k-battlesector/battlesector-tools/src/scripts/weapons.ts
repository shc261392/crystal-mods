// Client-side filtering/sorting for the weapons browser.

import { applyI18n, tf } from './i18n';

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

export function initWeaponsBrowser(): void {
  const grid = document.getElementById('grid');
  const q = document.getElementById('q') as HTMLInputElement | null;
  const sort = document.getElementById('sort') as HTMLSelectElement | null;
  const tagFilter = document.getElementById('weapon-tag-filter');
  const count = document.getElementById('count');
  const empty = document.getElementById('empty');
  const reset = document.getElementById('reset');
  if (!grid || !q || !sort || !tagFilter) return;

  const cards = Array.from(grid.querySelectorAll<HTMLElement>('.weapon-card'));
  const selectedTags = new Set<string>();
  const tagButtons = Array.from(tagFilter.querySelectorAll<HTMLButtonElement>('button[data-tag]'));

  const params = new URLSearchParams(location.search);
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
    history.replaceState(null, '', qs ? `?${qs}` : location.pathname);
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
    const ordered = [...cards]
      .filter((c) => c.style.display !== 'none')
      .sort((a, b) => compare(a, b, (sort?.value as SortKey) ?? 'name'));
    for (const c of ordered) grid?.appendChild(c);

    if (count) {
      count.textContent = tf('common.count.weaponsVisible', {
        visible,
        total: cards.length,
      });
    }
    empty?.classList.toggle('hidden', visible !== 0);
    syncUrl();
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

  window.addEventListener('bs:locale-changed', () => {
    applyI18n();
    apply();
  });

  applyI18n();
  paintTagButtons();
  apply();
}
