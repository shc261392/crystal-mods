// Navigation behaviour: mobile menu toggle + command-palette search.
// The search index is fetched lazily on first open to keep per-page JS minimal.

interface SearchEntry {
  t: 'unit' | 'weapon';
  n: string; // name
  s: string; // slug
  m: string; // meta (faction or damage)
}

let index: SearchEntry[] | null = null;
let loading: Promise<SearchEntry[]> | null = null;
let activeIndex = 0;
let filtered: SearchEntry[] = [];

function loadIndex(): Promise<SearchEntry[]> {
  if (index) return Promise.resolve(index);
  if (loading) return loading;
  loading = fetch('/search-index.json')
    .then((r) => r.json() as Promise<SearchEntry[]>)
    .then((data) => {
      index = data;
      return data;
    });
  return loading;
}

function urlFor(entry: SearchEntry): string {
  return entry.t === 'unit' ? `/units/${entry.s}` : `/weapons/${entry.s}`;
}

function render(results: HTMLElement, query: string): void {
  const items = filtered.slice(0, 30);
  if (items.length === 0) {
    results.innerHTML = `<li class="px-4 py-6 text-center text-sm text-[var(--color-faint)]">${
      query ? 'No matches found' : 'Type to search 632 units & weapons'
    }</li>`;
    return;
  }
  results.innerHTML = items
    .map((e, i) => {
      const icon = e.t === 'unit' ? '◈' : '⚔';
      const active = i === activeIndex;
      return `<li>
        <a href="${urlFor(e)}" data-idx="${i}" class="flex items-center gap-3 px-4 py-2.5 ${
          active ? 'bg-[color-mix(in_oklab,var(--color-gold)_14%,transparent)]' : ''
        }">
          <span class="text-[var(--color-gold-dim)] w-4 text-center">${icon}</span>
          <span class="flex-1 min-w-0">
            <span class="block text-sm font-semibold truncate">${e.n}</span>
            <span class="block text-xs text-[var(--color-faint)]">${
              e.t === 'unit' ? 'Unit' : 'Weapon'
            } · ${e.m}</span>
          </span>
        </a>
      </li>`;
    })
    .join('');
}

function search(query: string): void {
  const q = query.trim().toLowerCase();
  if (!index) {
    filtered = [];
    return;
  }
  if (!q) {
    filtered = index.slice(0, 30);
    return;
  }
  filtered = index
    .filter((e) => e.n.toLowerCase().includes(q))
    .sort((a, b) => {
      const ai = a.n.toLowerCase().indexOf(q);
      const bi = b.n.toLowerCase().indexOf(q);
      return ai - bi || a.n.length - b.n.length;
    });
}

export function initNav(): void {
  const menuToggle = document.getElementById('menu-toggle');
  const mobileMenu = document.getElementById('mobile-menu');
  menuToggle?.addEventListener('click', () => {
    const open = mobileMenu?.classList.toggle('hidden') === false;
    menuToggle.setAttribute('aria-expanded', String(open));
  });

  const overlay = document.getElementById('search-overlay');
  const openBtn = document.getElementById('search-open');
  const input = document.getElementById('search-input') as HTMLInputElement | null;
  const results = document.getElementById('search-results');
  if (!overlay || !input || !results) return;

  const open = async (): Promise<void> => {
    overlay.classList.remove('hidden');
    overlay.classList.add('flex');
    input.value = '';
    activeIndex = 0;
    document.body.style.overflow = 'hidden';
    input.focus();
    await loadIndex();
    search('');
    render(results, '');
  };

  const close = (): void => {
    overlay.classList.add('hidden');
    overlay.classList.remove('flex');
    document.body.style.overflow = '';
  };

  openBtn?.addEventListener('click', open);

  input.addEventListener('input', () => {
    activeIndex = 0;
    search(input.value);
    render(results, input.value);
  });

  input.addEventListener('keydown', (e) => {
    const max = Math.min(filtered.length, 30);
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      activeIndex = Math.min(activeIndex + 1, max - 1);
      render(results, input.value);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      activeIndex = Math.max(activeIndex - 1, 0);
      render(results, input.value);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const target = filtered[activeIndex];
      if (target) window.location.href = urlFor(target);
    }
  });

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) close();
  });

  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      if (overlay.classList.contains('hidden')) void open();
      else close();
    } else if (e.key === 'Escape' && !overlay.classList.contains('hidden')) {
      close();
    }
  });
}
