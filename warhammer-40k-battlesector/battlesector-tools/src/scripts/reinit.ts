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

// Count client-side (ClientRouter) navigations so a "back" control can tell
// whether the user reached the current page from within the app (precise
// history.back() with scroll restoration) or via a direct/deep-linked visit.
let clientNavCount = 0;
if (typeof document !== 'undefined') {
  document.addEventListener('astro:after-swap', () => {
    clientNavCount += 1;
  });
}

/** True when at least one in-app client navigation has occurred this session. */
export function hasInAppHistory(): boolean {
  return clientNavCount > 0;
}
