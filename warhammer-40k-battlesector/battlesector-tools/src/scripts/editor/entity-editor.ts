/**
 * Generic client for the unit and weapon editors. Both share the same markup
 * contract so a single implementation drives them:
 *
 *   [data-editor-row][data-editor-target][data-editor-id][data-search]
 *     ...inputs carrying [data-field="<jsonKey>"]
 *     optional icon input [data-field="portrait"|"icon"] + [data-open-icon-picker]
 *     optional notes textarea [data-field="notes"] + [data-note-count]
 *
 * Edits auto-save (debounced) to the repo through the dev middleware.
 */
import { type EditorTarget, createSaver, showToast } from './core.ts';
import { initIconPicker } from './icon-picker.ts';

const NOTE_WORD_LIMIT = 100;

/** Read a data-* attribute via a variable key (satisfies strict TS + Biome). */
function ds(el: HTMLElement, key: string): string | undefined {
  return el.dataset[key];
}

function collectPatch(row: HTMLElement): Record<string, unknown> {
  const patch: Record<string, unknown> = {};
  const fields = row.querySelectorAll<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>(
    '[data-field]',
  );
  for (const el of fields) {
    const key = ds(el, 'field');
    if (!key) continue;
    if (el instanceof HTMLInputElement && el.type === 'checkbox') {
      patch[key] = el.checked;
    } else {
      patch[key] = el.value;
    }
  }
  return patch;
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
  const rows = Array.from(document.querySelectorAll<HTMLElement>('[data-editor-row]'));
  if (rows.length === 0) return;

  const rowById = new Map<string, HTMLElement>();
  for (const row of rows) {
    const id = ds(row, 'editorId');
    if (id) rowById.set(id, row);
    updateNoteCount(row);
  }

  // Target is uniform per page; read it from the first row.
  const target = ((rows[0] ? ds(rows[0], 'editorTarget') : undefined) ?? 'unit') as EditorTarget;

  const saver = createSaver(
    target,
    (id) => {
      const row = rowById.get(id);
      return row ? collectPatch(row) : null;
    },
    {
      onStatus: (id) => {
        const row = rowById.get(id);
        if (row) updateIconPreview(row);
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
    if (el.matches('[data-field="notes"]')) updateNoteCount(rowById.get(id) ?? el);
    saver.schedule(id);
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

  // Icon picker wiring: on pick, update preview + save immediately.
  initIconPicker((input) => {
    const row = input.closest<HTMLElement>('[data-editor-row]');
    const id = row ? ds(row, 'editorId') : undefined;
    if (!id) return;
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

  showToast('Editor ready — edits save to repo', 'info');
}
