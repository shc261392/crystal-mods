#!/usr/bin/env node
/**
 * Update zh-TW locale in i18n.json with Traditional Chinese from tc-localization mod
 * 
 * Background:
 *   During the v1.7.4 migration, the game's bundled Chinese switched from Traditional
 *   to Simplified. The zh-TW locale in battlesector-tools should use Traditional Chinese
 *   from the tc-localization mod, but it was incorrectly using Simplified Chinese (zh-CN).
 * 
 * This script:
 *   - Reads the Traditional Chinese translations from tc-localization/translation/zh-TW/patched/units.txt
 *   - Matches unit/weapon nameIds to their Traditional Chinese names
 *   - Updates the zh-TW section in src/data/i18n.json
 * 
 * Usage:
 *   node scripts/update-zh-tw-locale.cjs
 * 
 * Prerequisites:
 *   - tc-localization mod must be in ../tc-localization/ (relative to battlesector-tools)
 *   - tc-localization must have translation/zh-TW/patched/units.txt
 */

const fs = require('fs');
const path = require('path');

const PROJECT_ROOT = path.join(__dirname, '..');
const I18N_PATH = path.join(PROJECT_ROOT, 'src', 'data', 'i18n.json');
const UNITS_JSON_PATH = path.join(PROJECT_ROOT, 'src', 'data', 'units.json');
const WEAPONS_JSON_PATH = path.join(PROJECT_ROOT, 'src', 'data', 'weapons.json');
const TC_UNITS_PATH = path.join(PROJECT_ROOT, '..', 'tc-localization', 'translation', 'zh-TW', 'patched', 'units.txt');

/**
 * Parse TC localization file format: <id>|<text>|<optional>
 * @param {string} filePath
 * @returns {Map<number, string>} Map from text ID to Traditional Chinese text
 */
function parseTCFile(filePath) {
  const map = new Map();
  
  if (!fs.existsSync(filePath)) {
    console.error(`ERROR: TC file not found: ${filePath}`);
    console.error('Make sure tc-localization mod is in the correct location.');
    return map;
  }

  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');
  
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#') || trimmed.startsWith('//')) continue;
    
    // Format: <id>|<text>|<optional>
    const parts = trimmed.split('|');
    if (parts.length < 2) continue;
    
    const id = parseInt(parts[0], 10);
    const text = parts[1].trim();
    
    if (isNaN(id) || !text) continue;
    
    map.set(id, text);
  }
  
  console.log(`Loaded ${map.size} Traditional Chinese entries from ${path.basename(filePath)}`);
  return map;
}

/**
 * Main update function
 */
function main() {
  console.log('=== Updating zh-TW locale with Traditional Chinese ===\n');
  
  // Load i18n.json
  console.log('1. Loading i18n.json...');
  const i18n = JSON.parse(fs.readFileSync(I18N_PATH, 'utf8'));
  
  // Load units and weapons
  console.log('2. Loading units.json and weapons.json...');
  const units = JSON.parse(fs.readFileSync(UNITS_JSON_PATH, 'utf8'));
  const weapons = JSON.parse(fs.readFileSync(WEAPONS_JSON_PATH, 'utf8'));
  
  // Load Traditional Chinese translations
  console.log('3. Loading Traditional Chinese from tc-localization...');
  const tcMap = parseTCFile(TC_UNITS_PATH);
  
  if (tcMap.size === 0) {
    console.error('ERROR: No Traditional Chinese translations found!');
    process.exit(1);
  }
  
  // Update unit names
  console.log('\n4. Updating unit names...');
  let unitsUpdated = 0;
  let unitsSkipped = 0;
  let unitsMissing = 0;
  
  for (const unit of units) {
    const nameId = unit.nameId;
    const tcName = tcMap.get(nameId);
    
    if (tcName) {
      const oldName = i18n.unitNames['zh-TW'][String(unit.id)];
      if (oldName !== tcName) {
        i18n.unitNames['zh-TW'][String(unit.id)] = tcName;
        unitsUpdated++;
      } else {
        unitsSkipped++;
      }
    } else {
      unitsMissing++;
    }
  }
  
  // Update weapon names
  console.log('5. Updating weapon names...');
  let weaponsUpdated = 0;
  let weaponsSkipped = 0;
  let weaponsMissing = 0;
  
  for (const weapon of weapons) {
    const nameId = weapon.nameId;
    const tcName = tcMap.get(nameId);
    
    if (tcName) {
      const oldName = i18n.weaponNames['zh-TW'][String(weapon.id)];
      if (oldName !== tcName) {
        i18n.weaponNames['zh-TW'][String(weapon.id)] = tcName;
        weaponsUpdated++;
      } else {
        weaponsSkipped++;
      }
    } else {
      weaponsMissing++;
    }
  }
  
  // Save updated i18n.json
  console.log('\n6. Writing updated i18n.json...');
  fs.writeFileSync(I18N_PATH, JSON.stringify(i18n, null, 2) + '\n', 'utf8');
  
  console.log('\n=== Summary ===');
  console.log(`Units updated: ${unitsUpdated}`);
  console.log(`Units unchanged: ${unitsSkipped}`);
  console.log(`Units missing TC: ${unitsMissing} (likely DLC content)`);
  console.log(`Weapons updated: ${weaponsUpdated}`);
  console.log(`Weapons unchanged: ${weaponsSkipped}`);
  console.log(`Weapons missing TC: ${weaponsMissing} (likely DLC content)`);
  console.log('\n✓ i18n.json updated successfully!');
  
  if (unitsUpdated > 0 || weaponsUpdated > 0) {
    console.log('\nNext steps:');
    console.log('1. Review the changes: git diff src/data/i18n.json');
    console.log('2. Test the site: pnpm dev');
    console.log('3. Commit the changes: git add src/data/i18n.json && git commit');
  }
}

main();
