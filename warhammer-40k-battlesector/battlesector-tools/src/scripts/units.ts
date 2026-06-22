// Client-side filtering/sorting for the units browser. Operates on the
// server-rendered cards via data-* attributes and syncs state to the URL so
// any filtered view is shareable.

type SortKey = 'name' | 'points-desc' | 'points-asc' | 'hp-desc' | 'armor-desc' | 'move-desc';

import { applyI18n, factionName, roleName, tf } from './i18n';

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
  const faction = document.getElementById('faction') as HTMLSelectElement | null;
  const role = document.getElementById('role') as HTMLSelectElement | null;
  const sort = document.getElementById('sort') as HTMLSelectElement | null;
  const count = document.getElementById('count');
  const empty = document.getElementById('empty');
  const reset = document.getElementById('reset');
  if (!grid || !q || !faction || !role || !sort) return;
  const factionSelect = faction;
  const roleSelect = role;

  const cards = Array.from(grid.querySelectorAll<HTMLElement>('.unit-card'));

  // Hydrate controls from URL
  const params = new URLSearchParams(location.search);
  if (params.get('q')) q.value = params.get('q') ?? '';
  if (params.get('faction')) faction.value = params.get('faction') ?? '';
  if (params.get('role')) role.value = params.get('role') ?? '';
  if (params.get('sort')) sort.value = params.get('sort') ?? 'name';

  function syncUrl(): void {
    const p = new URLSearchParams();
    if (q?.value) p.set('q', q.value);
    if (faction?.value) p.set('faction', faction.value);
    if (role?.value) p.set('role', role.value);
    if (sort && sort.value !== 'name') p.set('sort', sort.value);
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
      case 'armor-desc':
        return num(b, 'armor') - num(a, 'armor');
      case 'move-desc':
        return num(b, 'move') - num(a, 'move');
      default:
        return displayName(a).localeCompare(displayName(b));
    }
  }

  function localizeSelectOptions(): void {
    for (const opt of Array.from(factionSelect.options)) {
      const id = Number(opt.getAttribute('data-faction-id'));
      if (!Number.isFinite(id)) continue;
      opt.textContent = factionName(id, opt.value);
    }
    for (const opt of Array.from(roleSelect.options)) {
      const id = Number(opt.getAttribute('data-role-id'));
      if (!Number.isFinite(id)) continue;
      opt.textContent = roleName(id, opt.value);
    }
  }

  function apply(): void {
    const term = q?.value.trim().toLowerCase() ?? '';
    const fac = faction?.value ?? '';
    const rol = role?.value ?? '';
    let visible = 0;

    for (const card of cards) {
      const matches =
        (!term || displayName(card).toLowerCase().includes(term)) &&
        (!fac || text(card, 'faction') === fac) &&
        (!rol || text(card, 'role') === rol);
      card.style.display = matches ? '' : 'none';
      if (matches) visible++;
    }

    const ordered = [...cards]
      .filter((c) => c.style.display !== 'none')
      .sort((a, b) => compare(a, b, (sort?.value as SortKey) ?? 'name'));
    for (const c of ordered) grid?.appendChild(c);

    if (count) {
      count.textContent = tf('common.count.unitsVisible', {
        visible,
        total: cards.length,
      });
    }
    empty?.classList.toggle('hidden', visible !== 0);
    syncUrl();
  }

  q.addEventListener('input', apply);
  faction.addEventListener('change', apply);
  role.addEventListener('change', apply);
  sort.addEventListener('change', apply);
  reset?.addEventListener('click', () => {
    q.value = '';
    faction.value = '';
    role.value = '';
    sort.value = 'name';
    apply();
  });

  window.addEventListener('bs:locale-changed', () => {
    applyI18n();
    localizeSelectOptions();
    apply();
  });

  applyI18n();
  localizeSelectOptions();
  apply();
}
