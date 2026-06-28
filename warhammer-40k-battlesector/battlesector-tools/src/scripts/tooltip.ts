let initialized = false;

function ensureTooltipRoot(): HTMLDivElement {
  let root = document.getElementById('ui-tooltip') as HTMLDivElement | null;
  if (root) return root;
  root = document.createElement('div');
  root.id = 'ui-tooltip';
  root.className = 'ui-tooltip hidden';
  root.setAttribute('role', 'tooltip');
  document.body.appendChild(root);
  return root;
}

export function initTooltips(): void {
  if (initialized) return;
  initialized = true;

  const root = ensureTooltipRoot();
  let activeEl: HTMLElement | null = null;
  let showTimer: number | null = null;

  const hide = (): void => {
    if (showTimer !== null) {
      window.clearTimeout(showTimer);
      showTimer = null;
    }
    root.classList.add('hidden');
    activeEl = null;
  };

  const position = (target: HTMLElement): void => {
    const gap = 10;
    const rect = target.getBoundingClientRect();
    const tipRect = root.getBoundingClientRect();
    const vw = window.innerWidth;

    let left = rect.left + rect.width / 2 - tipRect.width / 2;
    left = Math.max(8, Math.min(left, vw - tipRect.width - 8));

    let top = rect.top - tipRect.height - gap;
    if (top < 8) top = rect.bottom + gap;

    root.style.left = `${left + window.scrollX}px`;
    root.style.top = `${top + window.scrollY}px`;
  };

  const show = (target: HTMLElement): void => {
    const text = target.getAttribute('data-tooltip')?.trim();
    if (!text) return;
    root.textContent = text;
    root.classList.remove('hidden');
    position(target);
    activeEl = target;
  };

  const onEnter = (event: Event): void => {
    const target = (event.target as HTMLElement).closest<HTMLElement>(
      '.tooltip-target[data-tooltip]',
    );
    if (!target) return;
    if (showTimer !== null) window.clearTimeout(showTimer);
    showTimer = window.setTimeout(() => show(target), 300);
  };

  const onLeave = (event: Event): void => {
    const from = (event.target as HTMLElement).closest<HTMLElement>(
      '.tooltip-target[data-tooltip]',
    );
    if (!from) return;
    const to = event instanceof MouseEvent ? (event.relatedTarget as Node | null) : null;
    if (to && from.contains(to)) return;
    hide();
  };

  document.addEventListener('mouseover', onEnter);
  document.addEventListener('mouseout', onLeave);

  document.addEventListener('focusin', (event) => {
    const target = (event.target as HTMLElement).closest<HTMLElement>(
      '.tooltip-target[data-tooltip]',
    );
    if (!target) return;
    if (showTimer !== null) window.clearTimeout(showTimer);
    show(target);
  });

  document.addEventListener('focusout', (event) => {
    const target = (event.target as HTMLElement).closest<HTMLElement>(
      '.tooltip-target[data-tooltip]',
    );
    if (!target) return;
    hide();
  });

  window.addEventListener(
    'scroll',
    () => {
      if (activeEl && !root.classList.contains('hidden')) position(activeEl);
    },
    { passive: true },
  );

  window.addEventListener('resize', () => {
    if (activeEl && !root.classList.contains('hidden')) position(activeEl);
  });
}
