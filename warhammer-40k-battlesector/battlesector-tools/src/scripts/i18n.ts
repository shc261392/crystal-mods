import i18nData from '../data/i18n.json';
import type { I18nBundle } from '../lib/types';

const i18n = i18nData as I18nBundle;
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
  history.replaceState(null, '', `${url.pathname}${url.search}${url.hash}`);
}

export function setLocale(locale: string): void {
  if (!hasLocale(locale)) return;
  localStorage.setItem(KEY, locale);
  upsertLangInUrl(locale);
  applyI18n();
  window.dispatchEvent(new CustomEvent('bs:locale-changed', { detail: { locale } }));
}

function getUi(locale: string, key: string): string {
  return i18n.ui[locale]?.[key] ?? i18n.ui[DEFAULT_LOCALE]?.[key] ?? key;
}

export function t(key: string, locale = getLocale()): string {
  return getUi(locale, key);
}

export function unitName(id: number, fallback: string, locale = getLocale()): string {
  return i18n.unitNames[locale]?.[String(id)] ?? fallback;
}

export function weaponName(id: number, fallback: string, locale = getLocale()): string {
  return i18n.weaponNames[locale]?.[String(id)] ?? fallback;
}

export function factionName(id: number, fallback: string, locale = getLocale()): string {
  return i18n.factionNames[locale]?.[String(id)] ?? fallback;
}

export function roleName(id: number, fallback: string, locale = getLocale()): string {
  return i18n.roleNames[locale]?.[String(id)] ?? fallback;
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
}

export function initI18nSelector(select: HTMLSelectElement | null): void {
  if (!select) return;
  const locale = getLocale();
  if (select.value !== locale) select.value = locale;
  select.addEventListener('change', () => setLocale(select.value));
}
