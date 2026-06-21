// Client-side filtering/sorting for the weapons browser.

type SortKey = 'name' | 'damage-desc' | 'damage-asc' | 'acc-desc';

function num(el: HTMLElement, key: string): number {
  return Number(el.dataset[key] ?? 0);
}

function text(el: HTMLElement, key: string): string {
  return el.dataset[key] ?? '';
}

export function initWeaponsBrowser(): void {
  const grid = document.getElementById('grid');
  const q = document.getElementById('q') as HTMLInputElement | null;
  const sort = document.getElementById('sort') as HTMLSelectElement | null;
  const count = document.getElementById('count');
  const empty = document.getElementById('empty');
  const reset = document.getElementById('reset');
  if (!grid || !q || !sort) return;

  const cards = Array.from(grid.querySelectorAll<HTMLElement>('.weapon-card'));

  const params = new URLSearchParams(location.search);
  if (params.get('q')) q.value = params.get('q') ?? '';
  if (params.get('sort')) sort.value = params.get('sort') ?? 'name';

  function syncUrl(): void {
    const p = new URLSearchParams();
    if (q?.value) p.set('q', q.value);
    if (sort && sort.value !== 'name') p.set('sort', sort.value);
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
      default:
        return text(a, 'name').localeCompare(text(b, 'name'));
    }
  }

  function apply(): void {
    const term = q?.value.trim().toLowerCase() ?? '';
    let visible = 0;
    for (const card of cards) {
      const matches = !term || text(card, 'name').includes(term);
      card.style.display = matches ? '' : 'none';
      if (matches) visible++;
    }
    const ordered = [...cards]
      .filter((c) => c.style.display !== 'none')
      .sort((a, b) => compare(a, b, (sort?.value as SortKey) ?? 'name'));
    for (const c of ordered) grid?.appendChild(c);

    if (count) count.textContent = `${visible} of ${cards.length} weapons`;
    empty?.classList.toggle('hidden', visible !== 0);
    syncUrl();
  }

  q.addEventListener('input', apply);
  sort.addEventListener('change', apply);
  reset?.addEventListener('click', () => {
    q.value = '';
    sort.value = 'name';
    apply();
  });

  apply();
}
