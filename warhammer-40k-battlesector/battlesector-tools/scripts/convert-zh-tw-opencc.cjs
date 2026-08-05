#!/usr/bin/env node
/**
 * Convert zh-TW locale using OpenCC (Simplified → Traditional Chinese)
 *
 * Background:
 *   The game does not have official Traditional Chinese localization.
 *   OpenCC is the correct tool to convert Simplified Chinese (zh-CN) to
 *   Traditional Chinese (zh-TW) for the battlesector-tools website.
 *
 * This script:
 *   - Loads i18n.json
 *   - Converts ALL zh-CN text to zh-TW using OpenCC
 *   - Updates unitNames, weaponNames, factionNames, roleNames
 *
 * Usage:
 *   node scripts/convert-zh-tw-opencc.cjs
 *
 * Prerequisites:
 *   - opencc-js must be installed: pnpm add -D opencc-js
 */

const fs = require('fs');
const path = require('path');
const OpenCC = require('opencc-js');

const PROJECT_ROOT = path.join(__dirname, '..');
const I18N_PATH = path.join(PROJECT_ROOT, 'src', 'data', 'i18n.json');

/**
 * Convert Simplified Chinese to Traditional Chinese using OpenCC
 */
function main() {
  console.log('=== Converting zh-TW locale using OpenCC ===\n');

  // Initialize OpenCC converter (Simplified → Traditional)
  console.log('1. Initializing OpenCC converter (s2t)...');
  const converter = OpenCC.Converter({ from: 'cn', to: 'tw' });

  // Load i18n.json
  console.log('2. Loading i18n.json...');
  const i18n = JSON.parse(fs.readFileSync(I18N_PATH, 'utf8'));

  // Convert unit names
  console.log('\n3. Converting unit names...');
  let unitsConverted = 0;
  let unitsUnchanged = 0;

  for (const [unitId, simplifiedName] of Object.entries(i18n.unitNames['zh-CN'])) {
    const traditionalName = converter(simplifiedName);
    const oldName = i18n.unitNames['zh-TW'][unitId];

    if (oldName !== traditionalName) {
      if (oldName) {
        console.log(`  [${unitId}] ${oldName} → ${traditionalName}`);
      }
      i18n.unitNames['zh-TW'][unitId] = traditionalName;
      unitsConverted++;
    } else {
      unitsUnchanged++;
    }
  }

  // Convert weapon names
  console.log('\n4. Converting weapon names...');
  let weaponsConverted = 0;
  let weaponsUnchanged = 0;

  for (const [weaponId, simplifiedName] of Object.entries(i18n.weaponNames['zh-CN'])) {
    const traditionalName = converter(simplifiedName);
    const oldName = i18n.weaponNames['zh-TW'][weaponId];

    if (oldName !== traditionalName) {
      if (oldName) {
        console.log(`  [${weaponId}] ${oldName} → ${traditionalName}`);
      }
      i18n.weaponNames['zh-TW'][weaponId] = traditionalName;
      weaponsConverted++;
    } else {
      weaponsUnchanged++;
    }
  }

  // Convert faction names
  console.log('\n5. Converting faction names...');
  let factionsConverted = 0;

  for (const [factionId, simplifiedName] of Object.entries(i18n.factionNames['zh-CN'])) {
    const traditionalName = converter(simplifiedName);
    const oldName = i18n.factionNames['zh-TW'][factionId];

    if (oldName !== traditionalName) {
      console.log(`  [${factionId}] ${oldName} → ${traditionalName}`);
      i18n.factionNames['zh-TW'][factionId] = traditionalName;
      factionsConverted++;
    }
  }

  // Convert role names
  console.log('\n6. Converting role names...');
  let rolesConverted = 0;

  for (const [roleId, simplifiedName] of Object.entries(i18n.roleNames['zh-CN'])) {
    const traditionalName = converter(simplifiedName);
    const oldName = i18n.roleNames['zh-TW'][roleId];

    if (oldName !== traditionalName) {
      console.log(`  [${roleId}] ${oldName} → ${traditionalName}`);
      i18n.roleNames['zh-TW'][roleId] = traditionalName;
      rolesConverted++;
    }
  }

  // Save updated i18n.json
  console.log('\n7. Writing updated i18n.json...');
  fs.writeFileSync(I18N_PATH, JSON.stringify(i18n, null, 2) + '\n', 'utf8');

  console.log('\n=== Summary ===');
  console.log(`Units converted: ${unitsConverted}`);
  console.log(`Units unchanged: ${unitsUnchanged}`);
  console.log(`Weapons converted: ${weaponsConverted}`);
  console.log(`Weapons unchanged: ${weaponsUnchanged}`);
  console.log(`Factions converted: ${factionsConverted}`);
  console.log(`Roles converted: ${rolesConverted}`);
  console.log('\n✓ i18n.json updated successfully with OpenCC!');

  if (unitsConverted > 0 || weaponsConverted > 0 || factionsConverted > 0 || rolesConverted > 0) {
    console.log('\nNext steps:');
    console.log('1. Review the changes: git diff src/data/i18n.json');
    console.log('2. Test the site: pnpm dev');
    console.log('3. Commit the changes: git add src/data/i18n.json && git commit');
  }
}

main();
