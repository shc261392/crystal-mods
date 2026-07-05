/**
 * Shared client core for the local editor suite (units, weapons, abilities).
 *
 * All three editors persist through the dev-only middleware at
 * `POST /__editor/save`, which writes directly into the git-tracked JSON under
 * `src/data/`. There is no export/import — every save is the source of truth.
 */

export type EditorTarget = 'unit' | 'weapon' | 'ability';

export interface SaveResult {
  ok: boolean;
  changed?: string[];
  message?: string;
}

const SAVE_ROUTE = '/__editor/save';

/** Post a single patch to the repo. Resolves with the middleware result. */
export async function postSave(
  target: EditorTarget,
  id: string | number,
  patch: Record<string, unknown>,
): Promise<SaveResult> {
  try {
    const res = await fetch(SAVE_ROUTE, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ target, id, patch }),
    });
    const data = (await res.json()) as SaveResult;
    return data;
  } catch (err) {
    return { ok: false, message: err instanceof Error ? err.message : String(err) };
  }
}

type ToastKind = 'ok' | 'error' | 'info';

let toastHost: HTMLElement | null = null;

function ensureToastHost(): HTMLElement {
  if (toastHost) return toastHost;
  const host = document.createElement('div');
  host.id = 'editor-toast-host';
  host.className = 'fixed z-[200] bottom-4 right-4 flex flex-col gap-2 items-end';
  document.body.appendChild(host);
  toastHost = host;
  return host;
}

/** Small transient status toast (bottom-right). */
export function showToast(message: string, kind: ToastKind = 'ok'): void {
  const host = ensureToastHost();
  const el = document.createElement('div');
  const color =
    kind === 'error'
      ? 'var(--color-blood)'
      : kind === 'info'
        ? 'var(--color-plasma)'
        : 'var(--color-toxin)';
  el.className =
    'surface px-3.5 py-2 text-sm font-semibold shadow-lg border-l-4 transition-opacity duration-300';
  el.style.borderLeftColor = color;
  el.textContent = message;
  host.appendChild(el);
  window.setTimeout(() => {
    el.style.opacity = '0';
    window.setTimeout(() => el.remove(), 320);
  }, 1800);
}

/**
 * Per-id debounced saver. Coalesces rapid edits, exposes an immediate flush for
 * blur/change events, and reports status through the optional callback.
 */
export function createSaver(
  target: EditorTarget,
  collect: (id: string) => Record<string, unknown> | null,
  opts: { debounceMs?: number; onStatus?: (id: string, result: SaveResult) => void } = {},
) {
  const debounceMs = opts.debounceMs ?? 350;
  const timers = new Map<string, ReturnType<typeof setTimeout>>();

  const run = async (id: string): Promise<void> => {
    const patch = collect(id);
    if (!patch) return;
    const result = await postSave(target, id, patch);
    opts.onStatus?.(id, result);
    if (result.ok) {
      showToast('Saved to repo');
    } else {
      showToast(result.message ?? 'Save failed', 'error');
    }
  };

  const schedule = (id: string): void => {
    const existing = timers.get(id);
    if (existing) clearTimeout(existing);
    timers.set(
      id,
      setTimeout(() => {
        timers.delete(id);
        void run(id);
      }, debounceMs),
    );
  };

  const flush = (id: string): void => {
    const existing = timers.get(id);
    if (existing) {
      clearTimeout(existing);
      timers.delete(id);
    }
    void run(id);
  };

  return { schedule, flush };
}
