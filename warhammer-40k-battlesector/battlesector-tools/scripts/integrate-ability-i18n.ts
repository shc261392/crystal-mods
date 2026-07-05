/**
 * Semi-automated i18n integration helper for unit abilities.
 *
 * Purpose:
 *   Use English ability text from ability-overrides.source.json to locate
 *   corresponding localization entries in game data, then extract all available
 *   translations and generate i18n-ready data structures.
 *
 * Workflow:
 *   1. Load curated English abilities from ability-overrides.source.json
 *   2. Search for matching text in game text_repository files
 *   3. Extract translations from all available locales
 *   4. Generate ability-i18n.json with structure compatible with existing i18n system
 *   5. Provide manual review recommendations for fuzzy matches
 *
 * Data sources (in priority order):
 *   - Game extracted text: .copilot_workspace/battlesector-data/extracted_text_assets/
 *   - TC localization: ../tc-localization/translation/zh-TW/source/zh-TW/
 *   - Manual overrides (when automated matching fails)
 *
 * Usage:
 *   pnpm run integrate:ability-i18n
 *   pnpm run integrate:ability-i18n --dry-run  (preview only)
 *   pnpm run integrate:ability-i18n --manual   (interactive mode for fuzzy matches)
 */

import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.join(scriptDir, '..');
const workspaceRoot = path.join(projectRoot, '..', '..');

interface AbilityOverride {
  title?: string;
  icon?: string;
  description?: string;
  kind?: 'active' | 'passive';
  actionPoints?: number;
  cooldown?: number;
}

interface AbilitySource {
  generatedAt?: string;
  storageKey?: string;
  entries: Record<string, AbilityOverride>;
}

interface AbilityI18n {
  abilityId: number;
  textId?: number | undefined;
  locales: Record<
    string,
    {
      title?: string;
      description?: string;
    }
  >;
  confidence: 'exact' | 'fuzzy' | 'manual';
  notes?: string | undefined;
}

// Locale code mappings (game internal to website)
const LOCALE_MAP: Record<string, string> = {
  '': 'en', // no suffix = English
  _chinese: 'zh-CN',
  _french: 'fr',
  _german: 'de',
  _korean: 'ko',
  _polish: 'pl',
  _portuguese: 'pt-BR',
  _russian: 'ru',
  _spanish: 'es',
};

const TC_LOCALE = 'zh-TW'; // Traditional Chinese from tc-localization mod

const TEXT_REPOSITORY_BASES = [
  'units',
  'units-external',
  'barks',
  'barks-external',
  'campaign',
  'campaign-external',
  'default',
  'default-external',
];

// Paths
const ABILITY_SOURCE = path.join(projectRoot, 'src', 'data', 'ability-overrides.source.json');
const EXTRACTED_TEXT_ROOT = path.join(
  workspaceRoot,
  '.copilot_workspace',
  'battlesector-data',
  'extracted_text_assets',
);
const TC_MOD_ROOT = path.join(
  workspaceRoot,
  'warhammer-40k-battlesector',
  'tc-localization',
  'translation',
  'zh-TW',
  'source',
  'zh-TW',
);

const OUTPUT_PATH = path.join(projectRoot, 'src', 'data', 'ability-i18n.json');
const REVIEW_PATH = path.join(projectRoot, '.copilot_workspace', 'ability-i18n-review.json');

// CLI flags
const args = process.argv.slice(2);
const isDryRun = args.includes('--dry-run');

/**
 * Parse text_repository file format:
 * <id> <text>
 * Where <id> is numeric and <text> is the rest of the line
 */
function parseTextRepository(filePath: string): Map<number, string> {
  const map = new Map<number, string>();
  if (!existsSync(filePath)) return map;

  try {
    const content = readFileSync(filePath, 'utf8');
    for (const line of content.split('\n')) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;

      const spaceIdx = trimmed.indexOf(' ');
      if (spaceIdx === -1) continue;

      const idStr = trimmed.slice(0, spaceIdx);
      const text = trimmed.slice(spaceIdx + 1).trim();
      const id = Number(idStr);

      if (Number.isNaN(id) || id < 0) continue;
      map.set(id, text);
    }
  } catch (err) {
    console.warn(`Warning: Failed to parse ${filePath}: ${err}`);
  }

  return map;
}

/**
 * Load all text repositories for a given locale suffix
 */
function loadLocaleTextMaps(localeSuffix: string): Map<number, string> {
  const merged = new Map<number, string>();

  for (const baseName of TEXT_REPOSITORY_BASES) {
    const filename = `text_repository-${baseName}${localeSuffix}.txt`;
    const filePath = path.join(EXTRACTED_TEXT_ROOT, filename);
    const entries = parseTextRepository(filePath);

    for (const [id, text] of entries) {
      merged.set(id, text);
    }
  }

  return merged;
}

/**
 * Load Traditional Chinese from tc-localization mod
 */
function loadTCLocalization(): Map<number, string> {
  const merged = new Map<number, string>();

  // TC mod uses same base names, stored in source/zh-TW/
  for (const baseName of TEXT_REPOSITORY_BASES) {
    const filename = `text_repository-${baseName}.txt`;
    const filePath = path.join(TC_MOD_ROOT, filename);
    const entries = parseTextRepository(filePath);

    for (const [id, text] of entries) {
      merged.set(id, text);
    }
  }

  return merged;
}

/**
 * Normalize text for comparison (remove extra whitespace, normalize line breaks)
 */
function normalizeText(text: string): string {
  return text.trim().replace(/\r\n/g, '\n').replace(/\s+/g, ' ').toLowerCase();
}

/**
 * Calculate similarity score between two strings (0.0 - 1.0)
 * Uses Levenshtein distance normalized by length
 */
function similarityScore(a: string, b: string): number {
  const aNorm = normalizeText(a);
  const bNorm = normalizeText(b);

  if (aNorm === bNorm) return 1.0;

  const maxLen = Math.max(aNorm.length, bNorm.length);
  if (maxLen === 0) return 1.0;

  const distance = levenshteinDistance(aNorm, bNorm);
  return 1.0 - distance / maxLen;
}

function levenshteinDistance(a: string, b: string): number {
  const m = a.length;
  const n = b.length;
  let prev = Array.from({ length: m + 1 }, (_, i) => i);
  let curr = new Array<number>(m + 1).fill(0);

  for (let j = 1; j <= n; j++) {
    curr[0] = j;
    for (let i = 1; i <= m; i++) {
      const cost = a.charAt(i - 1) === b.charAt(j - 1) ? 0 : 1;
      curr[i] = Math.min(
        (prev[i] ?? 0) + 1, // deletion
        (curr[i - 1] ?? 0) + 1, // insertion
        (prev[i - 1] ?? 0) + cost, // substitution
      );
    }
    [prev, curr] = [curr, prev];
  }

  return prev[m] ?? 0;
}

/**
 * Search for ability text in locale map and return best matches
 */
function findTextMatches(
  searchText: string,
  localeMap: Map<number, string>,
  threshold = 0.85,
): Array<{ textId: number; text: string; score: number }> {
  const matches: Array<{ textId: number; text: string; score: number }> = [];

  for (const [textId, text] of localeMap) {
    const score = similarityScore(searchText, text);
    if (score >= threshold) {
      matches.push({ textId, text, score });
    }
  }

  return matches.sort((a, b) => b.score - a.score);
}

/**
 * Main integration workflow
 */
async function main() {
  console.log('=== Ability i18n Integration Helper ===\n');

  // 1. Load source abilities
  console.log('Step 1: Loading curated abilities from source...');
  if (!existsSync(ABILITY_SOURCE)) {
    console.error(`Error: Source file not found: ${ABILITY_SOURCE}`);
    process.exit(1);
  }

  const abilityData = JSON.parse(readFileSync(ABILITY_SOURCE, 'utf8')) as AbilitySource;
  const abilities = Object.entries(abilityData.entries).map(([id, data]) => ({
    id: Number(id),
    ...data,
  }));

  console.log(`Loaded ${abilities.length} abilities.\n`);

  // 2. Load all locale text maps
  console.log('Step 2: Loading game localization data...');
  const localeTextMaps: Record<string, Map<number, string>> = {};

  // Check if extracted text assets exist
  if (!existsSync(EXTRACTED_TEXT_ROOT)) {
    console.warn(
      `Warning: Extracted text assets not found at:\n  ${EXTRACTED_TEXT_ROOT}\nAbility i18n integration requires game data extraction.\nProceeding with limited data...\n`,
    );
  } else {
    for (const [suffix, localeCode] of Object.entries(LOCALE_MAP)) {
      const textMap = loadLocaleTextMaps(suffix);
      if (textMap.size > 0) {
        localeTextMaps[localeCode] = textMap;
        console.log(`  ${localeCode}: ${textMap.size} entries`);
      }
    }
  }

  // Load TC localization
  if (existsSync(TC_MOD_ROOT)) {
    const tcMap = loadTCLocalization();
    if (tcMap.size > 0) {
      localeTextMaps[TC_LOCALE] = tcMap;
      console.log(`  ${TC_LOCALE}: ${tcMap.size} entries`);
    }
  }

  console.log('');

  // 3. Match abilities to text IDs
  console.log('Step 3: Matching abilities to localization entries...');
  const results: AbilityI18n[] = [];
  const needsReview: Array<{
    abilityId: number;
    title: string;
    matches: Array<{ textId: number; text: string; score: number }>;
  }> = [];

  const enKey = 'en';
  const enMap = localeTextMaps[enKey];
  if (!enMap || enMap.size === 0) {
    console.warn('Warning: No English text map available. Cannot perform matching.');
    console.log('Please extract game data first.\n');
    if (!isDryRun) {
      process.exit(1);
    }
    return;
  }

  for (const ability of abilities) {
    if (!ability.description || ability.description.trim().length === 0) {
      console.log(`  [${ability.id}] ${ability.title ?? 'Unknown'}: No description, skipping`);
      continue;
    }

    const abilityTitle = ability.title ?? 'Unknown';

    // Search for description match (may need fuzzy matching).
    const descMatches = findTextMatches(ability.description, enMap, 0.85);

    if (descMatches.length === 0) {
      console.log(`  [${ability.id}] ${abilityTitle}: ❌ No matches found`);
      needsReview.push({
        abilityId: ability.id,
        title: abilityTitle,
        matches: [],
      });
      continue;
    }

    const bestMatch = descMatches[0];
    if (!bestMatch) continue;
    const confidence: 'exact' | 'fuzzy' | 'manual' =
      bestMatch.score === 1.0 ? 'exact' : bestMatch.score >= 0.95 ? 'fuzzy' : 'manual';

    // Extract translations for this text ID
    const translations: Record<string, { title?: string; description?: string }> = {};

    for (const [locale, textMap] of Object.entries(localeTextMaps)) {
      const translatedText = textMap.get(bestMatch.textId);
      if (translatedText && translatedText.trim().length > 0) {
        translations[locale] = {
          description: translatedText,
          // Title translation would need separate matching - simplified for now
        };
      }
    }

    results.push({
      abilityId: ability.id,
      textId: bestMatch.textId,
      locales: translations,
      confidence,
      notes: confidence !== 'exact' ? `Match score: ${bestMatch.score.toFixed(3)}` : undefined,
    });

    const confidenceEmoji = confidence === 'exact' ? '✅' : confidence === 'fuzzy' ? '⚠️' : '❓';
    console.log(
      `  [${ability.id}] ${abilityTitle}: ${confidenceEmoji} textId=${bestMatch.textId}, ` +
        `score=${bestMatch.score.toFixed(3)}, ${Object.keys(translations).length} locales`,
    );

    if (descMatches.length > 1 && confidence !== 'exact') {
      needsReview.push({
        abilityId: ability.id,
        title: abilityTitle,
        matches: descMatches.slice(0, 5), // Top 5 candidates
      });
    }
  }

  console.log('');

  // 4. Generate output
  console.log('Step 4: Generating output files...');

  const output = {
    generatedAt: new Date().toISOString(),
    source: 'ability-overrides.source.json + game text_repository files',
    stats: {
      totalAbilities: abilities.length,
      matched: results.length,
      exact: results.filter((r) => r.confidence === 'exact').length,
      fuzzy: results.filter((r) => r.confidence === 'fuzzy').length,
      manual: results.filter((r) => r.confidence === 'manual').length,
      needsReview: needsReview.length,
    },
    abilities: results,
  };

  if (isDryRun) {
    console.log('\n=== DRY RUN MODE ===');
    console.log('Output preview:');
    console.log(JSON.stringify(output.stats, null, 2));
    console.log(`\nWould write to: ${OUTPUT_PATH}`);
  } else {
    writeFileSync(OUTPUT_PATH, JSON.stringify(output, null, 2), 'utf8');
    console.log(`✅ Generated: ${path.relative(projectRoot, OUTPUT_PATH)}`);
  }

  // 5. Generate review file if needed
  if (needsReview.length > 0) {
    const reviewOutput = {
      generatedAt: new Date().toISOString(),
      instructions:
        'Review these abilities with fuzzy or missing matches. ' +
        'Choose the correct textId or add manual translations to ability-overrides.source.json.',
      needsReview,
    };

    if (!isDryRun) {
      writeFileSync(REVIEW_PATH, JSON.stringify(reviewOutput, null, 2), 'utf8');
      console.log(`⚠️  Generated review file: ${path.relative(projectRoot, REVIEW_PATH)}`);
    }

    console.log(`\n${needsReview.length} abilities need manual review.`);
  }

  // 6. Summary
  console.log('\n=== Summary ===');
  console.log(`Total abilities: ${abilities.length}`);
  console.log(`Matched: ${results.length}`);
  console.log(`  Exact matches: ${output.stats.exact}`);
  console.log(`  Fuzzy matches: ${output.stats.fuzzy}`);
  console.log(`  Manual review needed: ${needsReview.length}`);

  if (results.length > 0) {
    const localesFound = new Set<string>();
    for (const result of results) {
      for (const locale of Object.keys(result.locales)) {
        localesFound.add(locale);
      }
    }
    console.log(`Locales found: ${Array.from(localesFound).sort().join(', ')}`);
  }

  console.log('\nNext steps:');
  if (needsReview.length > 0) {
    console.log(`1. Review ${REVIEW_PATH}`);
    console.log('2. Manually verify fuzzy matches and add textIds to source if needed');
  }
  console.log('3. Integrate ability-i18n.json into the i18n pipeline');
  console.log('4. Update components to use ability localization');

  if (isDryRun) {
    console.log('\n(Dry run complete - no files were written)');
  }
}

main().catch((err) => {
  console.error('Fatal error:', err);
  process.exit(1);
});
