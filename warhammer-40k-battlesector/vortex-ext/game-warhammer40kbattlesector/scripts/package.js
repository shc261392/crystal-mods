#!/usr/bin/env node
/*
 * Build a Nexus-compliant Vortex extension archive.
 *
 * Output: vortex-ext/dist/game-warhammer40kbattlesector-<version>.zip
 *
 * The archive layout is FLAT (no nested wrapper folder) which is the most
 * common review failure. We enforce that here.
 *
 * Deterministic (AGENTS.md rule 15): the files are staged with a fixed
 * 1980-01-01 mtime before zipping with `zip -jX`, so repeated runs on the same
 * commit produce a byte-identical archive.
 */
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const here = path.resolve(__dirname, '..');
const repoRoot = path.resolve(__dirname, '..', '..', '..');
const info = JSON.parse(fs.readFileSync(path.join(here, 'info.json'), 'utf8'));
const version = info.version;
const slug = 'game-warhammer40kbattlesector';

const distDir = path.resolve(here, '..', '..', 'vortex-ext', 'dist');
fs.mkdirSync(distDir, { recursive: true });

const out = path.join(distDir, `${slug}-${version}.zip`);
try {
  fs.unlinkSync(out);
} catch (e) {
  /* not present */
}

const files = ['info.json', 'index.js', 'gameart.jpg', 'warpstorm.png', 'README.md'];
for (const f of files) {
  if (!fs.existsSync(path.join(here, f))) {
    if (f === 'README.md') continue; // README is optional
    console.error(`MISSING required file: ${f}`);
    process.exit(1);
  }
}
const shipped = files.filter((f) => fs.existsSync(path.join(here, f)));

// Deterministic staging: fixed 1980-01-01 mtime, copied under dist/ (gitignored).
const stage = path.join(distDir, `.stage-${slug}`);
fs.rmSync(stage, { recursive: true, force: true });
fs.mkdirSync(stage, { recursive: true });
const fixed = new Date(1980, 0, 1, 0, 0, 0); // local midnight, TZ-independent zip time
const staged = shipped.map((f) => {
  const dest = path.join(stage, f);
  fs.copyFileSync(path.join(here, f), dest);
  fs.utimesSync(dest, fixed, fixed);
  return dest;
});

try {
  execSync(`zip -jX "${out}" ${staged.map((f) => `"${f}"`).join(' ')}`, {
    stdio: 'inherit',
  });
} finally {
  fs.rmSync(stage, { recursive: true, force: true });
}

// Verify flat layout — zero directories inside the archive.
const listing = execSync(`unzip -l "${out}"`, { encoding: 'utf8' });
if (/\//.test(listing.replace(/^.*Archive:.*$/m, ''))) {
  // crude check; zip -j strips paths so this should never trip, but better safe
  console.error('Archive contains nested folders — fix packaging script.');
  process.exit(1);
}
console.log(`\nWrote ${path.relative(repoRoot, out)}`);
