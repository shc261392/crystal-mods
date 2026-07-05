/**
 * Removes local-only pages from the production build output before deploy.
 *
 * The Editor Suite is a curation tool for building ground-truth data locally;
 * it must never ship to production. This strips its built output from `dist/`
 * after `astro build` and before `wrangler deploy`.
 *
 * Run automatically as part of `pnpm deploy`.
 */
import { rmSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const dist = path.join(scriptDir, '..', 'dist');

// Directory-format output (default) and file-format fallback.
const localOnly = ['editor', 'editor/index.html', 'editor.html'];

for (const rel of localOnly) {
  const target = path.join(dist, rel);
  rmSync(target, { recursive: true, force: true });
  console.log(`Stripped local-only path from dist: ${rel}`);
}
