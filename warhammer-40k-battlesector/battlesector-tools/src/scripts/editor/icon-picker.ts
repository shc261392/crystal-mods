/**
 * Reusable icon-picker client for the editor suite. Reads the catalog embedded
 * by IconPickerModal.astro and opens a searchable grid. Trigger buttons must
 * carry `data-open-icon-picker` and `data-target-input="<css selector>"`.
 */

interface IconOption {
  key: string;
  url: string;
  source?: string;
}

function readCatalog(): IconOption[] {
  const el = document.getElementById('editor-icon-catalog');
  if (!el) return [];
  try {
    const parsed = JSON.parse(el.textContent ?? '[]') as IconOption[];
    return Array.isArray(parsed)
      ? parsed.filter((r) => r && typeof r.key === 'string' && typeof r.url === 'string')
      : [];
  } catch {
    return [];
  }
}

/**
 * @param onPick called with the target input element and chosen url after a
 *   selection so the caller can persist the change.
 */
export function initIconPicker(onPick: (input: HTMLInputElement, url: string) => void): void {
  const modal = document.getElementById('icon-picker');
  const search = document.getElementById('icon-picker-search') as HTMLInputElement | null;
  const grid = document.getElementById('icon-picker-grid');
  const count = document.getElementById('icon-picker-count');
  const closeBtn = document.getElementById('icon-picker-close');
  if (!modal || !grid) return;

  // Data-attribute keys accessed via variables (strict TS + Biome friendly).
  const iconUrlKey = 'iconUrl';
  const targetInputKey = 'targetInput';

  const catalog = readCatalog();
  let targetSelector: string | null = null;

  const render = (): void => {
    const q = search?.value.trim().toLowerCase() ?? '';
    const filtered =
      q.length === 0
        ? catalog
        : catalog.filter((e) => `${e.key} ${e.source ?? ''} ${e.url}`.toLowerCase().includes(q));
    if (count) count.textContent = `${filtered.length} / ${catalog.length}`;

    grid.innerHTML = '';
    for (const icon of filtered) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className =
        'surface p-2 border border-[var(--color-border)] hover:border-[var(--color-gold)] text-left transition-colors';
      btn.dataset[iconUrlKey] = icon.url;

      const wrap = document.createElement('div');
      wrap.className =
        'h-16 w-full grid place-items-center bg-[var(--color-base)] rounded border border-[var(--color-border)]';
      const img = document.createElement('img');
      img.alt = '';
      img.loading = 'lazy';
      img.decoding = 'async';
      img.className = 'max-h-14 max-w-full object-contain';
      img.src = icon.url;
      wrap.appendChild(img);

      const key = document.createElement('div');
      key.className = 'mt-1.5 text-[11px] font-semibold break-all';
      key.textContent = icon.key;

      btn.append(wrap, key);
      grid.appendChild(btn);
    }
  };

  const open = (selector: string): void => {
    targetSelector = selector;
    document.body.style.overflow = 'hidden';
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    modal.setAttribute('aria-hidden', 'false');
    render();
    search?.focus({ preventScroll: true });
  };

  const close = (): void => {
    document.body.style.overflow = '';
    modal.classList.add('hidden');
    modal.classList.remove('flex');
    modal.setAttribute('aria-hidden', 'true');
    targetSelector = null;
  };

  document.addEventListener('click', (event) => {
    const trigger = (event.target as HTMLElement).closest<HTMLElement>('[data-open-icon-picker]');
    if (!trigger) return;
    const sel = trigger.dataset[targetInputKey];
    if (!sel) return;
    event.preventDefault();
    open(sel);
  });

  closeBtn?.addEventListener('click', close);
  search?.addEventListener('input', render);

  modal.addEventListener('click', (event) => {
    const target = event.target as HTMLElement;
    if (target === modal) {
      close();
      return;
    }
    const pick = target.closest<HTMLButtonElement>('[data-icon-url]');
    if (!pick || !targetSelector) return;
    const url = pick.dataset[iconUrlKey];
    if (!url) return;
    const input = document.querySelector<HTMLInputElement>(targetSelector);
    if (input) {
      input.value = url;
      onPick(input, url);
    }
    close();
  });

  window.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !modal.classList.contains('hidden')) close();
  });
}
