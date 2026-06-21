// Behaviour for the unit detail page: copy link + add to army builder.
import { addToArmy } from './army-store';

function toast(message: string): void {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = message;
  el.classList.remove('hidden');
  window.setTimeout(() => el.classList.add('hidden'), 1800);
}

export function initUnitDetail(): void {
  const copyBtn = document.getElementById('copy-link');
  copyBtn?.addEventListener('click', async () => {
    const path = copyBtn.getAttribute('data-url') ?? location.pathname;
    const url = `${location.origin}${path}`;
    try {
      await navigator.clipboard.writeText(url);
      toast('Link copied to clipboard');
    } catch {
      toast(url);
    }
  });

  const addBtn = document.getElementById('add-army');
  addBtn?.addEventListener('click', () => {
    const id = Number(addBtn.getAttribute('data-id'));
    const name = addBtn.getAttribute('data-name') ?? '';
    const points = Number(addBtn.getAttribute('data-points'));
    const faction = addBtn.getAttribute('data-faction') ?? '';
    if (!Number.isFinite(id)) return;
    addToArmy({ id, name, points, faction });
    toast(`${name} added to army`);
  });
}
