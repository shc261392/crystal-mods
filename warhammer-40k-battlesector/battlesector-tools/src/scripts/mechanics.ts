// Client-side search filter for the Game Mechanics reference page.
import { applyI18n } from './i18n';

export function initMechanics(): void {
  const search = document.getElementById('mech-search') as HTMLInputElement | null;
  const grid = document.getElementById('mech-grid');
  const empty = document.getElementById('mech-empty');
  const count = document.getElementById('mech-count');
  if (!grid) return;
  const cards = Array.from(grid.querySelectorAll<HTMLElement>('[data-mech]'));

  function apply(): void {
    const term = search?.value.trim().toLowerCase() ?? '';
    const dataKey = 'mech';
    let visible = 0;
    for (const card of cards) {
      const haystack = card.dataset[dataKey] ?? '';
      const match = !term || haystack.includes(term);
      card.style.display = match ? '' : 'none';
      if (match) visible++;
    }
    empty?.classList.toggle('hidden', visible !== 0);
    if (count) count.textContent = String(visible);
  }

  search?.addEventListener('input', apply);
  applyI18n();
  apply();
}
