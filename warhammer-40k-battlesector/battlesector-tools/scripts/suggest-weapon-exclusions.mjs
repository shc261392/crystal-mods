import { readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const I18N_PATH = path.join(ROOT, 'src', 'data', 'i18n.json');
const WEAPONS_PATH = path.join(ROOT, 'src', 'data', 'weapons.json');
const OUT_PATH = path.join(ROOT, 'data', 'weapon-name-exclusions.suggestions.json');

const locale = process.argv[2] ?? 'zh-TW';

const i18n = JSON.parse(readFileSync(I18N_PATH, 'utf8'));
const weapons = JSON.parse(readFileSync(WEAPONS_PATH, 'utf8'));

const names = i18n.weaponNames?.[locale] ?? {};

const phraseKeywords = [
  'AI',
  '部隊',
  '比賽',
  '控制區',
  '進攻方',
  '防守方',
  '刪除',
  '使用者名稱',
  '地圖',
  '腐化',
  'support@',
  '<br>',
  '<b>',
];

const looksSuspicious = (s) => {
  if (!s || typeof s !== 'string') return true;
  if (phraseKeywords.some((k) => s.includes(k))) return true;
  if (/\{\d+\}/.test(s)) return true;
  if (/[。!?]/.test(s) && s.length > 12) return true;
  if ((s.includes('.') || s.includes(',')) && s.length > 14) return true;
  if (s.length > 40) return true;
  return false;
};

const candidates = [];
for (const w of weapons) {
  const localized = (names[String(w.id)] ?? '').trim();
  if (!looksSuspicious(localized)) continue;
  candidates.push({
    id: w.id,
    nameId: w.nameId,
    canonicalName: w.name,
    localized,
  });
}

candidates.sort((a, b) => a.id - b.id);

const result = {
  locale,
  generatedAt: new Date().toISOString(),
  candidateCount: candidates.length,
  candidates,
};

writeFileSync(OUT_PATH, `${JSON.stringify(result, null, 2)}\n`, 'utf8');

console.log(`Wrote ${OUT_PATH}`);
console.log(`Locale: ${locale}`);
console.log(`Candidates: ${candidates.length}`);
