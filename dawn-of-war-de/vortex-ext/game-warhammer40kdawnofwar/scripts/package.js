#!/usr/bin/env node
/*
 * Build a Nexus-compliant Vortex extension archive for DoW DE.
 *
 * Output: vortex-ext/dist/game-warhammer40kdawnofwar-<version>.zip
 */
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const here = path.resolve(__dirname, '..');
const repoRoot = path.resolve(__dirname, '..', '..', '..');
const info = JSON.parse(fs.readFileSync(path.join(here, 'info.json'), 'utf8'));
const version = info.version;
const slug = 'game-warhammer40kdawnofwar';

const distDir = path.resolve(here, '..', '..', 'vortex-ext', 'dist');
fs.mkdirSync(distDir, { recursive: true });

const out = path.join(distDir, `${slug}-${version}.zip`);
try {
  fs.unlinkSync(out);
} catch (e) {
  /* not present */
}

const files = ['info.json', 'index.js', 'gameart.jpg', 'DESCRIPTION.md'];
for (const f of files) {
  if (!fs.existsSync(path.join(here, f))) {
    if (f === 'DESCRIPTION.md') continue; // DESCRIPTION is optional
    console.error(`MISSING required file: ${f}`);
    process.exit(1);
  }
}

execSync(
  `zip -j "${out}" ${files
    .filter((f) => fs.existsSync(path.join(here, f)))
    .map((f) => `"${path.join(here, f)}"`)
    .join(' ')}`,
  {
    stdio: 'inherit',
  },
);

// Verify flat layout
const listing = execSync(`unzip -l "${out}"`, { encoding: 'utf8' });
if (/\//.test(listing.replace(/^.*Archive:.*$/m, ''))) {
  console.error('Archive contains nested folders — fix packaging script.');
  process.exit(1);
}
console.log(`\nWrote ${path.relative(repoRoot, out)}`);
