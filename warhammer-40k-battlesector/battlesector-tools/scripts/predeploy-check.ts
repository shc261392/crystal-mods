/**
 * Pre-deploy validation + versioning.
 *
 * Runs before the production build to:
 *   1. Validate that every tracked data JSON parses and has the expected shape.
 *   2. Regenerate ability UI modules so they always match the source JSON.
 *   3. Compute a content hash over the data + generated modules and, when it
 *      changed, bump src/data/build-meta.json (version + hash + timestamp).
 *
 * Efficient by design: if the content hash is unchanged, build-meta is left
 * untouched so we don't create noisy diffs or redeploy identical content.
 *
 * Exits non-zero on any validation failure so `pnpm deploy` aborts safely.
 */
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { generateAbilityUi } from './generate-ability-ui.ts';
import { generateStatRanks } from './generate-stat-ranks.ts';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.join(scriptDir, '..');
const dataDir = path.join(projectRoot, 'src', 'data');
const libDir = path.join(projectRoot, 'src', 'lib');

const errors: string[] = [];

function readJson<T>(rel: string, dir = dataDir): T | null {
  const full = path.join(dir, rel);
  try {
    return JSON.parse(readFileSync(full, 'utf8')) as T;
  } catch (err) {
    errors.push(`${rel}: ${err instanceof Error ? err.message : String(err)}`);
    return null;
  }
}

function expectArray(rel: string, value: unknown, requiredKeys: string[]): void {
  if (!Array.isArray(value)) {
    errors.push(`${rel}: expected an array`);
    return;
  }
  const first = value[0] as Record<string, unknown> | undefined;
  if (first) {
    for (const key of requiredKeys) {
      if (!(key in first)) errors.push(`${rel}: entries missing "${key}"`);
    }
  }
}

console.log('▸ Validating data JSON…');

const units = readJson<Array<Record<string, unknown>>>('units.json');
if (units) expectArray('units.json', units, ['id', 'name', 'faction']);

const weapons = readJson<Array<Record<string, unknown>>>('weapons.json');
if (weapons) expectArray('weapons.json', weapons, ['id', 'name', 'damage']);

const abilitySource = readJson<{ entries: Record<string, unknown> }>(
  'ability-overrides.source.json',
);
if (
  abilitySource &&
  (typeof abilitySource.entries !== 'object' || abilitySource.entries === null)
) {
  errors.push('ability-overrides.source.json: missing "entries" object');
}

// These just need to parse.
readJson('i18n.json');
readJson('image-urls.json');
readJson('factions.json');
readJson('roles.json');

if (errors.length > 0) {
  console.error('\n✗ Data validation failed:');
  for (const e of errors) console.error(`  - ${e}`);
  process.exit(1);
}
console.log('  ✓ all data files valid');

console.log('▸ Regenerating ability UI modules…');
const genSummary = generateAbilityUi();
console.log(
  `  ✓ ${genSummary.total} abilities (${genSummary.active} active, ${genSummary.passive} passive)`,
);

console.log('▸ Regenerating stat-rank hexagon data…');
const rankSummary = generateStatRanks();
console.log(`  ✓ ${rankSummary.units} unit ranks, ${rankSummary.weapons} weapon ranks`);

console.log('▸ Computing content hash…');
const hashFiles = [
  path.join(dataDir, 'units.json'),
  path.join(dataDir, 'weapons.json'),
  path.join(dataDir, 'ability-overrides.source.json'),
  path.join(dataDir, 'i18n.json'),
  path.join(dataDir, 'image-urls.json'),
  path.join(dataDir, 'unit-ranks.json'),
  path.join(dataDir, 'weapon-ranks.json'),
  path.join(libDir, 'unit-abilities.ts'),
];
const hasher = createHash('sha256');
for (const file of hashFiles) {
  try {
    hasher.update(readFileSync(file));
  } catch {
    // A missing optional file should not crash the hash; skip it.
  }
}
const hash = hasher.digest('hex').slice(0, 8);

const metaPath = path.join(dataDir, 'build-meta.json');
const pkg = readJson<{ version?: string }>('package.json', projectRoot);
const version = pkg?.version ?? '0.0.0';
const prev = readJson<{ hash?: string; version?: string }>('build-meta.json');

if (prev?.hash === hash && prev?.version === version) {
  console.log(`  ✓ content unchanged (${version}+${hash}) — build-meta left as-is`);
} else {
  const meta = { version, hash, builtAt: new Date().toISOString() };
  writeFileSync(metaPath, `${JSON.stringify(meta, null, 2)}\n`, 'utf8');
  console.log(`  ✓ build-meta updated → ${version}+${hash}`);
}

console.log('\n✓ Predeploy checks passed.');
