/**
 * ClientRouter (View Transitions) helpers.
 *
 * With `<ClientRouter />`, page `<script>` modules run once but page content is
 * swapped on client navigation, so per-page initializers must re-run on the
 * `astro:page-load` event. Global (document/window) listeners added inside an
 * initializer would otherwise stack up on every navigation.
 *
 * `pageSignal(key)` returns a fresh AbortSignal for the current run and aborts
 * the previous run for that key — so passing `{ signal }` to any global
 * listener automatically removes the stale one from the previous page. Element-
 * scoped listeners are GC'd with their (replaced) nodes and need no signal.
 */
const controllers = new Map<string, AbortController>();

export function pageSignal(key: string): AbortSignal {
  controllers.get(key)?.abort();
  const ac = new AbortController();
  controllers.set(key, ac);
  return ac.signal;
}

/** Register an initializer to run on initial load and every client navigation. */
export function onPageLoad(init: () => void): void {
  document.addEventListener('astro:page-load', init);
}

// Track the path we navigated FROM, so a "back" control can decide whether the
// previous history entry is the list it should return to (precise history.back()
// with scroll restoration) or whether it should navigate to the list directly.
let previousPath = '';
if (typeof document !== 'undefined') {
  document.addEventListener('astro:before-preparation', () => {
    // Fires on the page being left, while its URL is still current.
    previousPath = location.pathname;
  });
}

/** The pathname of the page navigated away from most recently (in-app). */
export function getPreviousPath(): string {
  return previousPath;
}
