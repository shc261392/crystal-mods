// Faction picker: shows one faction panel at a time and reflects the choice in
// the URL (?faction=id) so a specific faction is shareable/deep-linkable.
import { applyI18n } from './i18n';

const ACTIVE_CLASSES = [
  '!text-[var(--color-gold)]',
  '!border-[var(--color-gold-dim)]',
  'bg-[color-mix(in_oklab,var(--color-gold)_14%,transparent)]',
];

export function initFactions(): void {
  const pillBar = document.getElementById('faction-pills');
  if (!pillBar) return;
  const pills = Array.from(pillBar.querySelectorAll<HTMLButtonElement>('.faction-pill'));
  const panels = Array.from(document.querySelectorAll<HTMLElement>('[data-faction-panel]'));

  function show(id: string): void {
    for (const panel of panels) {
      const on = panel.getAttribute('data-faction-panel') === id;
      panel.hidden = !on;
    }
    for (const pill of pills) {
      const on = pill.getAttribute('data-faction-id') === id;
      pill.setAttribute('aria-pressed', on ? 'true' : 'false');
      for (const c of ACTIVE_CLASSES) pill.classList.toggle(c, on);
    }
    const params = new URLSearchParams(location.search);
    params.set('faction', id);
    history.replaceState(history.state, '', `?${params.toString()}`);
  }

  for (const pill of pills) {
    pill.addEventListener('click', () => {
      const id = pill.getAttribute('data-faction-id');
      if (id) show(id);
    });
  }

  // Hydrate from URL, else default to the first faction.
  const urlId = new URLSearchParams(location.search).get('faction');
  const firstId = pills[0]?.getAttribute('data-faction-id') ?? '';
  const initial =
    urlId && pills.some((p) => p.getAttribute('data-faction-id') === urlId) ? urlId : firstId;
  applyI18n();
  if (initial) show(initial);
}
