#!/usr/bin/env node
/*
 * Build a Nexus-compliant Vortex extension archive.
 *
 * Output: <repo-root>/dist/game-warhammer40kbattlesector-<version>.zip
 *
 * The archive layout is FLAT (no nested wrapper folder) which is the most
 * common review failure. We enforce that here.
 */
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const here = path.resolve(__dirname, '..');
const info = JSON.parse(fs.readFileSync(path.join(here, 'info.json'), 'utf8'));
const version = info.version;
const slug = 'game-warhammer40kbattlesector';

const repoRoot = path.resolve(here, '..', '..');
const distDir = path.join(repoRoot, 'dist');
fs.mkdirSync(distDir, { recursive: true });

const out = path.join(distDir, `${slug}-${version}.zip`);
try { fs.unlinkSync(out); } catch (e) { /* not present */ }

const files = ['info.json', 'index.js', 'gameart.png', 'README.md'];
for (const f of files) {
  if (!fs.existsSync(path.join(here, f))) {
    if (f === 'README.md') continue; // README is optional
    console.error(`MISSING required file: ${f}`);
    process.exit(1);
  }
}

execSync(`zip -j "${out}" ${files.filter(f => fs.existsSync(path.join(here, f))).map(f => `"${path.join(here, f)}"`).join(' ')}`, {
  stdio: 'inherit',
});

// Verify flat layout — zero directories inside the archive.
const listing = execSync(`unzip -l "${out}"`, { encoding: 'utf8' });
if (/\//.test(listing.replace(/^.*Archive:.*$/m, ''))) {
  // crude check; zip -j strips paths so this should never trip, but better safe
  console.error('Archive contains nested folders — fix packaging script.');
  process.exit(1);
}
console.log(`\nWrote ${path.relative(repoRoot, out)}`);
