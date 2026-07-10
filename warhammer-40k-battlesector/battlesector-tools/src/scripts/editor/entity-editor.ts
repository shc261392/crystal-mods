/**
 * LOCAL-FIRST EDITOR
 *
 * Architecture (per user's teaching):
 * 1. localStorage is the SOURCE OF TRUTH
 * 2. Server JSON is FALLBACK when localStorage empty
 * 3. All reads from localStorage
 * 4. All writes update BOTH (localStorage immediately + server async)
 * 5. If save fails: show error, localStorage still valid
 */
import { type EditorTarget, createSaver, showToast } from './core.ts';
import { initIconPicker } from './icon-picker.ts';
import { migrateStorage } from './migrate-storage.ts';

const NOTE_WORD_LIMIT = 100;

/** Storage key for entity data: bs-editor-data:weapon */
function storageKey(target: EditorTarget): string {
  return `bs-editor-data:${target}`;
}

/** Read a data-* attribute via a variable key (satisfies strict TS + Biome). */
function ds(el: HTMLElement, key: string): string | undefined {
  return el.dataset[key];
}

/** Load all entities from localStorage. Returns null if not initialized. */
function loadFromStorage(target: EditorTarget): Record<string, Record<string, unknown>> | null {
  try {
    const raw = localStorage.getItem(storageKey(target));
    if (!raw) return null;
    return JSON.parse(raw) as Record<string, Record<string, unknown>>;
  } catch (err) {
    console.error('Failed to load from localStorage:', err);
    showToast('Error loading data from browser storage', 'error');
    return null;
  }
}

/** Save all entities to localStorage. */
function saveToStorage(target: EditorTarget, data: Record<string, Record<string, unknown>>): void {
  try {
    localStorage.setItem(storageKey(target), JSON.stringify(data));
  } catch (err) {
    console.error('Failed to save to localStorage:', err);
    showToast('CRITICAL: Storage save failed - your changes may be lost!', 'error');
  }
}

/** Extract entity data from server-rendered HTML rows. */
function extractServerData(rows: HTMLElement[]): Record<string, Record<string, unknown>> {
  const data: Record<string, Record<string, unknown>> = {};
  for (const row of rows) {
    const id = ds(row, 'editorId');
    if (!id) continue;
    const entity: Record<string, unknown> = { id: Number(id) || id };
    const fields = row.querySelectorAll<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>(
      '[data-field]',
    );
    for (const el of fields) {
      const key = ds(el, 'field');
      if (!key) continue;
      if (el instanceof HTMLInputElement && el.type === 'checkbox') {
        entity[key] = el.checked;
      } else {
        entity[key] = el.value;
      }
    }
    data[id] = entity;
  }
  return data;
}

/** Populate row inputs from entity data. */
function populateRow(row: HTMLElement, entity: Record<string, unknown>): void {
  const fields = row.querySelectorAll<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>(
    '[data-field]',
  );
  for (const el of fields) {
    const key = ds(el, 'field');
    if (!key || !(key in entity)) continue;
    const value = entity[key];
    if (el instanceof HTMLInputElement && el.type === 'checkbox') {
      el.checked = Boolean(value);
    } else {
      el.value = String(value ?? '');
    }
  }
}

function countWords(value: string): number {
  return value.trim().split(/\s+/).filter(Boolean).length;
}

function updateNoteCount(row: HTMLElement): void {
  const textarea = row.querySelector<HTMLTextAreaElement>('[data-field="notes"]');
  const counter = row.querySelector<HTMLElement>('[data-note-count]');
  if (!textarea || !counter) return;
  const words = countWords(textarea.value);
  counter.textContent = `${words} / ${NOTE_WORD_LIMIT} words`;
  counter.classList.toggle('text-[var(--color-blood)]', words > NOTE_WORD_LIMIT);
}

function updateIconPreview(row: HTMLElement): void {
  const input = row.querySelector<HTMLInputElement>('[data-field="portrait"],[data-field="icon"]');
  const img = row.querySelector<HTMLImageElement>('[data-icon-preview]');
  const empty = row.querySelector<HTMLElement>('[data-icon-empty]');
  if (!input || !img || !empty) return;
  const val = input.value.trim();
  if (val.length > 0) {
    img.src = val.startsWith('/') || val.startsWith('http') ? val : '';
    img.classList.toggle('hidden', img.src === '');
    empty.classList.toggle('hidden', img.src !== '');
  } else {
    img.classList.add('hidden');
    empty.classList.remove('hidden');
  }
}

export function initEntityEditor(): void {
  // Clean up obsolete draft keys from old architecture
  migrateStorage();

  const rows = Array.from(document.querySelectorAll<HTMLElement>('[data-editor-row]'));
  if (rows.length === 0) return;

  const editorList = document.getElementById('editor-list');

  const rowById = new Map<string, HTMLElement>();
  for (const row of rows) {
    const id = ds(row, 'editorId');
    if (id) rowById.set(id, row);
  }

  // Target is uniform per page; read it from the first row.
  const target = ((rows[0] ? ds(rows[0], 'editorTarget') : undefined) ?? 'unit') as EditorTarget;

  // LOCAL-FIRST: Load from localStorage first, fallback to server JSON
  let data = loadFromStorage(target);
  if (!data) {
    // First load: extract from SSR HTML, save to localStorage
    data = extractServerData(rows);
    console.log(`[editor] First load: extracted ${Object.keys(data).length} entities from server`);
    saveToStorage(target, data);
    showToast('Data loaded from server and cached locally', 'info');
  } else {
    // Subsequent load: populate rows from localStorage (SSR values are stale)
    console.log(`[editor] Loading ${Object.keys(data).length} entities from localStorage`);
    for (const [id, row] of rowById) {
      if (data[id]) {
        populateRow(row, data[id]);
      }
    }
    showToast('Loaded from local cache', 'info');
  }

  // Show editor list after data loaded (prevents SSR flash)
  if (editorList) editorList.style.display = '';

  // Update UI indicators (note: icon previews already correct from SSR)
  for (const row of rows) {
    updateNoteCount(row);
  }

  const saver = createSaver(
    target,
    (id) => {
      // Read from localStorage, not DOM
      return data[id] ?? null;
    },
    {
      onStatus: (id, result) => {
        const row = rowById.get(id);
        if (row) updateIconPreview(row);

        // Show errors
        if (!result.ok) {
          showToast(result.message ?? 'Server sync failed - data safe in local storage', 'error');
        }
      },
    },
  );

  const rowIdFrom = (el: HTMLElement): string | null => {
    const row = el.closest<HTMLElement>('[data-editor-row]');
    return row ? (ds(row, 'editorId') ?? null) : null;
  };

  const container = document.getElementById('editor-list') ?? document.body;

  container.addEventListener('input', (event) => {
    const el = (event.target as HTMLElement).closest<HTMLElement>('[data-field]');
    if (!el) return;
    const id = rowIdFrom(el);
    if (!id) return;
    const field = ds(el, 'field');

    if (
      field &&
      (el instanceof HTMLInputElement ||
        el instanceof HTMLTextAreaElement ||
        el instanceof HTMLSelectElement)
    ) {
      // LOCAL-FIRST: Update localStorage IMMEDIATELY
      if (!data[id]) data[id] = { id };
      if (el instanceof HTMLInputElement && el.type === 'checkbox') {
        data[id][field] = el.checked;
      } else {
        data[id][field] = el.value;
      }
      console.log(`[editor] Updated localStorage: ${id}.${field} =`, data[id][field]);
      saveToStorage(target, data);

      // Schedule async server sync
      saver.schedule(id);
    }

    const row = rowById.get(id);
    if (el.matches('[data-field="notes"]') && row) updateNoteCount(row);
  });

  container.addEventListener('change', (event) => {
    const el = (event.target as HTMLElement).closest<HTMLElement>('[data-field]');
    if (!el) return;
    const id = rowIdFrom(el);
    if (id) saver.flush(id);
  });

  container.addEventListener('focusout', (event) => {
    const el = (event.target as HTMLElement).closest<HTMLElement>('[data-field]');
    if (!el) return;
    const id = rowIdFrom(el);
    if (id) saver.flush(id);
  });

  // Icon picker wiring: on pick, update localStorage + save immediately.
  initIconPicker((input) => {
    const row = input.closest<HTMLElement>('[data-editor-row]');
    const id = row ? ds(row, 'editorId') : undefined;
    if (!id) return;

    const field = ds(input, 'field');
    if (field) {
      // Update localStorage immediately
      if (!data[id]) data[id] = { id };
      data[id][field] = input.value;
      saveToStorage(target, data);
    }

    if (row) updateIconPreview(row);
    saver.flush(id);
  });

  // Client-side search filter.
  const search = document.getElementById('editor-search') as HTMLInputElement | null;
  const count = document.getElementById('editor-count');
  const applyFilter = (): void => {
    const q = search?.value.trim().toLowerCase() ?? '';
    let visible = 0;
    for (const row of rows) {
      const hay = ds(row, 'search') ?? '';
      const show = q.length === 0 || hay.includes(q);
      row.classList.toggle('hidden', !show);
      if (show) visible += 1;
    }
    if (count) count.textContent = `${visible} / ${rows.length}`;
  };
  search?.addEventListener('input', applyFilter);
  applyFilter();

  // Warn before navigating away if data in localStorage (might not be synced to server yet)
  window.addEventListener('beforeunload', (e) => {
    // Check if there are any pending saves (in debounce queue or in-flight)
    if (saver.hasPending()) {
      e.preventDefault();
      e.returnValue = 'Changes are being saved, please wait...';
    }
  });
}
