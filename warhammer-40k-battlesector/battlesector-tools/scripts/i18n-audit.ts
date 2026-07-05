import { readFileSync, readdirSync, statSync } from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const SRC_DIR = path.join(ROOT, 'src');
const UI_I18N_PATH = path.join(SRC_DIR, 'data', 'ui-i18n.ts');

const bannedCopy: string[] = [
  'Filtering is instant',
  'Filter instantly',
  'no page reloads',
  'fast, mobile-friendly app',
];

function walk(dir: string, out: string[] = []): string[] {
  for (const entry of readdirSync(dir)) {
    const p = path.join(dir, entry);
    const s = statSync(p);
    if (s.isDirectory()) {
      if (entry === 'node_modules' || entry === 'dist' || entry.startsWith('.')) continue;
      walk(p, out);
    } else if (p.endsWith('.ts') || p.endsWith('.astro')) {
      out.push(p);
    }
  }
  return out;
}

function parseUiLocaleKeys(source: string): Map<string, Set<string>> {
  const byLocale = new Map<string, Set<string>>();
  let currentLocale: string | null = null;
  for (const line of source.split('\n')) {
    const localeMatch = line.match(/^\s{2}(?:'([^']+)'|([A-Za-z0-9-]+)):\s*\{$/);
    if (localeMatch) {
      currentLocale = localeMatch[1] ?? localeMatch[2] ?? null;
      if (currentLocale) byLocale.set(currentLocale, new Set());
      continue;
    }
    if (currentLocale && /^\s{2}\},?$/.test(line)) {
      currentLocale = null;
      continue;
    }
    if (!currentLocale) continue;
    const keyMatch = line.match(/^\s{4}'([^']+)':/);
    if (keyMatch?.[1]) byLocale.get(currentLocale)?.add(keyMatch[1]);
  }
  return byLocale;
}

function extractReferencedKeys(content: string): Set<string> {
  const keys = new Set<string>();

  for (const m of content.matchAll(/data-i18n-ui(?:-placeholder|-aria-label)?="([^"]+)"/g)) {
    if (m[1]) keys.add(m[1]);
  }

  for (const m of content.matchAll(/data-i18n-ui=\{([^}]+)\}/g)) {
    if (!m[1]) continue;
    for (const q of m[1].matchAll(/'([^']+)'/g)) {
      if (q[1]) keys.add(q[1]);
    }
  }

  for (const m of content.matchAll(/(?:\bt|\btf)\(\s*'([^']+)'/g)) {
    if (m[1]) keys.add(m[1]);
  }

  return keys;
}

function relative(p: string): string {
  return path.relative(ROOT, p).replaceAll('\\', '/');
}

interface LocaleReport {
  locale: string;
  used: number;
  covered: number;
  coveragePct: number;
  unresolved: string[];
}

const uiSource = readFileSync(UI_I18N_PATH, 'utf8');
const keysByLocale = parseUiLocaleKeys(uiSource);
const enKeys = keysByLocale.get('en') ?? new Set<string>();

const files = walk(SRC_DIR);
const usedKeys = new Set<string>();
const bannedHits: { file: string; phrase: string }[] = [];
for (const file of files) {
  const content = readFileSync(file, 'utf8');
  for (const key of extractReferencedKeys(content)) usedKeys.add(key);
  for (const phrase of bannedCopy) {
    if (content.includes(phrase)) bannedHits.push({ file: relative(file), phrase });
  }
}

const locales = [...keysByLocale.keys()].sort();
const missingInEn = [...usedKeys].filter((k) => !enKeys.has(k));

const localeReports: LocaleReport[] = locales.map((locale) => {
  const localeKeys = keysByLocale.get(locale) ?? new Set<string>();
  const unresolved = [...usedKeys].filter((k) => !localeKeys.has(k) && !enKeys.has(k));
  const covered = usedKeys.size - unresolved.length;
  return {
    locale,
    used: usedKeys.size,
    covered,
    coveragePct: Number(((covered / Math.max(1, usedKeys.size)) * 100).toFixed(2)),
    unresolved,
  };
});

const unresolvedTotal = localeReports.reduce((n, r) => n + r.unresolved.length, 0);
const summary = {
  filesScanned: files.length,
  referencedUiKeys: usedKeys.size,
  locales: locales.length,
  missingInEn: missingInEn.length,
  unresolvedTotal,
  coveragePct: Number(
    (
      (localeReports.reduce((n, r) => n + r.covered, 0) /
        Math.max(1, usedKeys.size * locales.length)) *
      100
    ).toFixed(2),
  ),
};

console.log('i18n audit summary');
console.log(JSON.stringify(summary, null, 2));

if (missingInEn.length) {
  console.log('\nMissing in en locale:');
  for (const key of missingInEn) console.log(`- ${key}`);
}

for (const report of localeReports) {
  if (report.unresolved.length === 0) continue;
  console.log(`\nUnresolved keys for ${report.locale}:`);
  for (const key of report.unresolved) console.log(`- ${key}`);
}

if (bannedHits.length) {
  console.log('\nDisallowed marketing copy detected:');
  for (const hit of bannedHits) console.log(`- ${hit.file}: "${hit.phrase}"`);
}

if (summary.coveragePct < 100 || missingInEn.length > 0 || bannedHits.length > 0) {
  process.exit(1);
}
