// Behaviour for the weapon detail page: copy link functionality
import { t } from './i18n';

function toast(message: string): void {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = message;
  el.classList.remove('hidden');
  window.setTimeout(() => el.classList.add('hidden'), 1800);
}

export function initWeaponDetail(): void {
  const copyBtn = document.getElementById('copy-link');
  copyBtn?.addEventListener('click', async () => {
    const path = copyBtn.getAttribute('data-url') ?? location.pathname;
    const url = `${location.origin}${path}`;
    try {
      await navigator.clipboard.writeText(url);
      toast(t('toast.linkCopiedClipboard'));
    } catch {
      toast(url);
    }
  });
}
