import nameExclusions from '../../data/weapon-name-exclusions.json';
import i18nData from '../data/i18n.json';
import { uiI18n } from '../data/ui-i18n';
import type { I18nBundle } from '../lib/types';

const i18n = i18nData as I18nBundle;
const exclusions = nameExclusions as {
  [locale: string]: { weaponIds?: number[] };
};
const DEFAULT_LOCALE = 'en';
const KEY = 'bs.locale.v1';

function data(el: HTMLElement, key: string): string | undefined {
  return el.dataset[key];
}

function hasLocale(locale: string): boolean {
  return i18n.locales.some((l) => l.code === locale);
}

export function getLocale(): string {
  const fromUrl = new URLSearchParams(location.search).get('lang');
  if (fromUrl && hasLocale(fromUrl)) return fromUrl;
  const stored = localStorage.getItem(KEY);
  if (stored && hasLocale(stored)) return stored;
  return DEFAULT_LOCALE;
}

function upsertLangInUrl(locale: string): void {
  const url = new URL(location.href);
  if (locale === DEFAULT_LOCALE) url.searchParams.delete('lang');
  else url.searchParams.set('lang', locale);
  history.replaceState(history.state, '', `${url.pathname}${url.search}${url.hash}`);
}

export function setLocale(locale: string): void {
  if (!hasLocale(locale)) return;
  localStorage.setItem(KEY, locale);
  upsertLangInUrl(locale);
  applyI18n();
  window.dispatchEvent(new CustomEvent('bs:locale-changed', { detail: { locale } }));
}

function getUi(locale: string, key: string): string {
  return (
    uiI18n[locale]?.[key] ??
    uiI18n[DEFAULT_LOCALE]?.[key] ??
    i18n.ui[locale]?.[key] ??
    i18n.ui[DEFAULT_LOCALE]?.[key] ??
    key
  );
}

function isPlaceholderName(value: string): boolean {
  const v = value.trim();
  const lower = v.toLowerCase();
  if (!v) return true;
  if (lower.includes('unknown') || lower.includes('unused')) return true;
  if (/\{\d+\}/.test(v)) return true;
  return false;
}

export function t(key: string, locale = getLocale()): string {
  return getUi(locale, key);
}

export function tf(
  key: string,
  vars: Record<string, string | number>,
  locale = getLocale(),
): string {
  const template = getUi(locale, key);
  return Object.entries(vars).reduce(
    (out, [name, value]) => out.replaceAll(`{${name}}`, String(value)),
    template,
  );
}

export function unitName(id: number, fallback: string, locale = getLocale()): string {
  const localized = i18n.unitNames[locale]?.[String(id)];
  if (!localized || isPlaceholderName(localized)) return fallback;
  return localized;
}

export function weaponName(id: number, fallback: string, locale = getLocale()): string {
  const blockedWeaponIds = exclusions[locale]?.weaponIds;
  if (blockedWeaponIds?.includes(id)) return fallback;
  const localized = i18n.weaponNames[locale]?.[String(id)];
  if (!localized || isPlaceholderName(localized)) return fallback;
  return localized;
}

export function factionName(id: number, fallback: string, locale = getLocale()): string {
  const localized = i18n.factionNames[locale]?.[String(id)];
  if (!localized || isPlaceholderName(localized)) return fallback;
  return localized;
}

export function roleName(id: number, fallback: string, locale = getLocale()): string {
  const localized = i18n.roleNames[locale]?.[String(id)];
  if (!localized || isPlaceholderName(localized)) return fallback;
  return localized;
}

function applyUi(locale: string): void {
  for (const el of document.querySelectorAll<HTMLElement>('[data-i18n-ui]')) {
    const key = data(el, 'i18nUi');
    if (!key) continue;
    el.textContent = getUi(locale, key);
  }

  for (const el of document.querySelectorAll<HTMLElement>('[data-i18n-ui-placeholder]')) {
    const key = data(el, 'i18nUiPlaceholder');
    if (!key) continue;
    const value = getUi(locale, key);
    if ('placeholder' in el) (el as HTMLInputElement).placeholder = value;
  }

  for (const el of document.querySelectorAll<HTMLElement>('[data-i18n-ui-aria-label]')) {
    const key = data(el, 'i18nUiAriaLabel');
    if (!key) continue;
    el.setAttribute('aria-label', getUi(locale, key));
  }
}

function applyLocaleToInternalLinks(locale: string): void {
  for (const el of document.querySelectorAll<HTMLAnchorElement>('a[href]')) {
    const raw = el.getAttribute('href');
    if (!raw) continue;
    if (
      raw.startsWith('#') ||
      raw.startsWith('mailto:') ||
      raw.startsWith('tel:') ||
      raw.startsWith('javascript:')
    ) {
      continue;
    }
    const url = new URL(raw, location.origin);
    if (url.origin !== location.origin) continue;
    if (locale === DEFAULT_LOCALE) url.searchParams.delete('lang');
    else url.searchParams.set('lang', locale);
    const localized = `${url.pathname}${url.search}${url.hash}`;
    if (el.getAttribute('href') !== localized) {
      el.setAttribute('href', localized);
    }
  }
}

function applyGameData(locale: string): void {
  for (const el of document.querySelectorAll<HTMLElement>('[data-i18n-unit]')) {
    const id = Number(data(el, 'i18nUnit'));
    if (!Number.isFinite(id)) continue;
    const fallback = data(el, 'i18nFallback') ?? el.textContent ?? '';
    el.textContent = unitName(id, fallback, locale);
  }

  for (const el of document.querySelectorAll<HTMLElement>('[data-i18n-weapon]')) {
    const id = Number(data(el, 'i18nWeapon'));
    if (!Number.isFinite(id)) continue;
    const fallback = data(el, 'i18nFallback') ?? el.textContent ?? '';
    el.textContent = weaponName(id, fallback, locale);
  }

  for (const el of document.querySelectorAll<HTMLElement>('[data-i18n-faction]')) {
    const id = Number(data(el, 'i18nFaction'));
    if (!Number.isFinite(id)) continue;
    const fallback = data(el, 'i18nFallback') ?? el.textContent ?? '';
    el.textContent = factionName(id, fallback, locale);
  }

  for (const el of document.querySelectorAll<HTMLElement>('[data-i18n-role]')) {
    const id = Number(data(el, 'i18nRole'));
    if (!Number.isFinite(id)) continue;
    const fallback = data(el, 'i18nFallback') ?? el.textContent ?? '';
    el.textContent = roleName(id, fallback, locale);
  }
}

export function applyI18n(): void {
  const locale = getLocale();
  document.documentElement.lang = locale;
  applyUi(locale);
  applyGameData(locale);
  applyLocaleToInternalLinks(locale);
  document.documentElement.classList.remove('i18n-pending');
}

export function initI18nSelector(select: HTMLSelectElement | null): void {
  if (!select) return;
  const locale = getLocale();
  if (select.value !== locale) select.value = locale;
  select.addEventListener('change', () => setLocale(select.value));
}
