// Filterable icon+name combobox that enhances an existing <select>. The native
// select stays in the DOM as the single source of truth (all existing state /
// URL / change-handler wiring keeps working); this only layers a nicer picker
// on top. Reused for the calculator's attacker + target unit selects.

export interface ItemMeta {
  icon?: string | null;
  factionId?: string;
  factionName?: string;
  color?: string;
}

export interface ComboOptions {
  /** Metadata (icon, faction) for a given option value. */
  metaFor: (value: string) => ItemMeta;
  /** Faction chips for filtering, when the options are units. */
  factions?: { id: string; name: string; color: string }[];
  searchPlaceholder: string;
  allLabel: string;
}

interface Combo {
  refresh: () => void;
}

const ACTIVE = ['!text-[var(--color-gold)]', '!border-[var(--color-gold-dim)]'];
const INIT_KEY = 'comboInit';

export function enhanceSelect(select: HTMLSelectElement, opts: ComboOptions): Combo {
  if (select.dataset[INIT_KEY] === '1') {
    // Re-enhanced after a client navigation: reuse the existing controller.
    const existing = comboRegistry.get(select);
    if (existing) {
      existing.refresh();
      return existing;
    }
  }
  select.dataset[INIT_KEY] = '1';
  select.style.display = 'none';
  select.setAttribute('aria-hidden', 'true');
  select.tabIndex = -1;

  const wrap = document.createElement('div');
  wrap.className = 'relative';
  // The layout margin lived on the (now hidden) select — move it to the wrapper.
  for (const c of Array.from(select.classList)) {
    if (/^m[btlrxy]?-/.test(c)) wrap.classList.add(c);
  }
  select.parentNode?.insertBefore(wrap, select);
  wrap.appendChild(select);

  const trigger = document.createElement('button');
  trigger.type = 'button';
  trigger.className =
    'select w-full flex items-center gap-2 text-left cursor-pointer !pr-8 relative';
  trigger.setAttribute('aria-haspopup', 'listbox');
  trigger.setAttribute('aria-expanded', 'false');
  trigger.innerHTML =
    '<span class="combo-trigger-content flex items-center gap-2 min-w-0 flex-1"></span><svg class="absolute right-2.5 top-1/2 -translate-y-1/2 opacity-60" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>';
  wrap.appendChild(trigger);

  const panel = document.createElement('div');
  panel.className =
    'absolute z-50 mt-1 left-0 right-0 rounded-lg border border-[var(--color-border-strong)] bg-[var(--color-elevated)] shadow-2xl p-2 hidden';
  panel.innerHTML = `
    <input type="search" class="input !h-9 mb-2" placeholder="${escapeHtml(opts.searchPlaceholder)}" autocomplete="off" />
    <div class="combo-factions flex flex-wrap gap-1.5 mb-2"></div>
    <div class="combo-list max-h-64 overflow-y-auto flex flex-col gap-0.5 pr-0.5"></div>`;
  wrap.appendChild(panel);

  const searchInput = panel.querySelector<HTMLInputElement>('input');
  const factionsRow = panel.querySelector<HTMLDivElement>('.combo-factions');
  const list = panel.querySelector<HTMLDivElement>('.combo-list');
  let activeFaction = '';

  if (opts.factions && factionsRow) {
    factionsRow.innerHTML = [{ id: '', name: opts.allLabel, color: '' }, ...opts.factions]
      .map(
        (f) =>
          `<button type="button" class="chip cursor-pointer !py-0.5 !px-2 text-[11px]" data-faction="${f.id}">${escapeHtml(f.name)}</button>`,
      )
      .join('');
  }

  function iconHtml(meta: ItemMeta): string {
    if (meta.icon) {
      return `<img src="${meta.icon}" alt="" class="w-6 h-6 rounded object-contain shrink-0 bg-[var(--color-base)]" loading="lazy" />`;
    }
    return `<span class="w-6 h-6 rounded shrink-0 bg-[var(--color-base)] border border-[var(--color-border)]"></span>`;
  }

  function setTrigger(): void {
    const opt = select.selectedOptions[0];
    const content = trigger.querySelector('.combo-trigger-content');
    if (!content) return;
    if (!opt || opt.value === '') {
      content.innerHTML = `<span class="truncate text-[var(--color-faint)]">${escapeHtml(opt?.textContent ?? '')}</span>`;
      return;
    }
    const meta = opts.metaFor(opt.value);
    content.innerHTML = `${iconHtml(meta)}<span class="truncate">${escapeHtml(opt.textContent ?? '')}</span>`;
  }

  function renderList(): void {
    if (!list) return;
    const term = (searchInput?.value ?? '').trim().toLowerCase();
    const rows: string[] = [];
    for (const opt of Array.from(select.options)) {
      const label = opt.textContent ?? '';
      const meta = opt.value === '' ? {} : opts.metaFor(opt.value);
      if (term && !label.toLowerCase().includes(term)) continue;
      if (activeFaction && opt.value !== '' && meta.factionId !== activeFaction) continue;
      const selected = opt.value === select.value;
      rows.push(
        `<button type="button" role="option" data-value="${escapeHtml(opt.value)}" aria-selected="${selected}" class="flex items-center gap-2 rounded px-2 py-1.5 text-sm text-left hover:bg-[var(--color-surface)] ${selected ? 'bg-[var(--color-surface)] !text-[var(--color-gold)]' : ''}">${opt.value === '' ? '<span class="w-6 h-6 shrink-0"></span>' : iconHtml(meta)}<span class="truncate flex-1">${escapeHtml(label)}</span>${meta.factionName ? `<span class="text-[10px] text-[var(--color-faint)] shrink-0">${escapeHtml(meta.factionName)}</span>` : ''}</button>`,
      );
    }
    list.innerHTML =
      rows.join('') ||
      `<p class="text-xs text-[var(--color-faint)] text-center py-4">No matches</p>`;
  }

  function open(): void {
    panel.classList.remove('hidden');
    trigger.setAttribute('aria-expanded', 'true');
    renderList();
    searchInput?.focus();
  }
  function close(): void {
    panel.classList.add('hidden');
    trigger.setAttribute('aria-expanded', 'false');
  }
  function toggle(): void {
    if (panel.classList.contains('hidden')) open();
    else close();
  }

  trigger.addEventListener('click', toggle);
  searchInput?.addEventListener('input', renderList);

  factionsRow?.addEventListener('click', (e) => {
    const btn = (e.target as HTMLElement).closest(
      'button[data-faction]',
    ) as HTMLButtonElement | null;
    if (!btn) return;
    activeFaction = btn.getAttribute('data-faction') ?? '';
    for (const b of factionsRow.querySelectorAll('button')) {
      const on = (b.getAttribute('data-faction') ?? '') === activeFaction;
      for (const c of ACTIVE) b.classList.toggle(c, on);
    }
    renderList();
  });

  list?.addEventListener('click', (e) => {
    const btn = (e.target as HTMLElement).closest('button[data-value]') as HTMLButtonElement | null;
    if (!btn) return;
    select.value = btn.getAttribute('data-value') ?? '';
    select.dispatchEvent(new Event('change', { bubbles: true }));
    setTrigger();
    close();
  });

  document.addEventListener('click', (e) => {
    if (!wrap.contains(e.target as Node)) close();
  });
  wrap.addEventListener('keydown', (e) => {
    if ((e as KeyboardEvent).key === 'Escape') close();
  });

  const controller: Combo = {
    refresh() {
      setTrigger();
      if (!panel.classList.contains('hidden')) renderList();
    },
  };
  comboRegistry.set(select, controller);
  setTrigger();
  return controller;
}

const comboRegistry = new WeakMap<HTMLSelectElement, Combo>();

function escapeHtml(s: string): string {
  return s.replace(
    /[&<>"']/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c] ?? c,
  );
}
