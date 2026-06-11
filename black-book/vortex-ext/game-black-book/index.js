/**
 * Vortex Game Extension — Black Book
 *
 * Steam App ID      : 1138660
 * Nexus domain      : blackbook
 * Main exe          : Black Book.exe
 * Engine            : Unity 2018.4 (Mono)
 *
 * Supported mod types
 * -------------------
 *  1. Localization mods: Unity asset replacement in Black Book_Data/
 *     - Replaces localization .asset files (string tables, text assets)
 *     - Routed to: Black Book_Data/resources/ or streamingassets/
 *     Examples:
 *       - Black Book_Data/resources/LocalizationZhTW.asset
 *       - Black Book_Data/StreamingAssets/Text_zh-TW.uasset
 *
 *  2. Font mods: deployed to Black Book_Data/Resources/Fonts/
 *     Examples:
 *       - Black Book_Data/Resources/Fonts/NotoSansTC.asset
 *
 *  3. General mods: any files with full deployment paths relative to game root
 *
 * This extension intelligently routes files to their correct destinations based
 * on path patterns, with optional wrapper folder stripping for user convenience.
 */

'use strict';

const path = require('path');
const { fs, util } = require('vortex-api');

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const GAME_ID = 'black-book';
const STEAM_APP_ID = '1138660';
const GAME_NAME = 'Black Book';
const GAME_EXE = 'Black Book.exe';

/**
 * Known first-level game directories to detect mods packaged with game-root-relative
 * paths. Helps determine if a single wrapper folder should be stripped.
 */
const ROOT_GAME_DIRS = [
  'Black Book_Data',
  'AutoTranslator',
  'BepInEx',
  'Fonts',
  'Mods',
  'ReiPatcher',
];

// ---------------------------------------------------------------------------
// Game Discovery
// ---------------------------------------------------------------------------

/**
 * Discovers the game by Steam App ID.
 * Supports Windows native and Proton/Linux.
 */
function findGame() {
  return util.GameStoreHelper.findByAppId([STEAM_APP_ID])
    .then((game) => game.gamePath)
    .catch(() => {
      throw new util.NotFound(`Black Book (App ID ${STEAM_APP_ID}) not found in Steam`);
    });
}

// ---------------------------------------------------------------------------
// Setup / Prepare
// ---------------------------------------------------------------------------

/**
 * Ensures key game directories exist so mods can be deployed to them.
 */
function prepareForModding(discovery) {
  const baseGamePath = discovery.path;
  const dirsToCreate = [
    path.join(baseGamePath, 'Black Book_Data', 'resources'),
    path.join(baseGamePath, 'Black Book_Data', 'StreamingAssets'),
    path.join(baseGamePath, 'Black Book_Data', 'Resources', 'Fonts'),
  ];

  return Promise.all(dirsToCreate.map((dir) => fs.ensureDirWritableAsync(dir)));
}

// ---------------------------------------------------------------------------
// Installer: Localization Mod (priority 25)
// Handles Unity asset replacement for localized strings
// ---------------------------------------------------------------------------

/**
 * Tests if this is a localization mod (files in localization asset paths).
 * Looks for .asset files, locale-specific naming, or Black Book_Data/ paths.
 */
function testLocalizationModContent(files) {
  const isLocMod = files.some(
    (f) =>
      (f.includes('zh-TW') || f.includes('zh_TW') || f.includes('localization')) &&
      (f.endsWith('.asset') || f.includes('Black Book_Data')),
  );

  return Promise.resolve({
    supported: isLocMod,
    requiredFiles: [],
  });
}

/**
 * Installs localization mod files to Black Book_Data/resources/ or StreamingAssets/.
 * Routes asset files to appropriate locations with optional wrapper stripping.
 */
function installLocalizationModContent(files, gameId, modPath) {
  const locFiles = files.filter(
    (f) =>
      (f.includes('zh-TW') || f.includes('zh_TW') || f.includes('localization')) &&
      (f.endsWith('.asset') || f.includes('Black Book_Data')),
  );

  if (locFiles.length === 0) {
    return Promise.resolve();
  }

  const commonPrefix = getCommonPrefix(locFiles);
  const stripCount = shouldStripWrapper(commonPrefix, locFiles) ? 1 : 0;

  const instructions = locFiles.map((file) => {
    let destPath = stripCount > 0 ? file.split('/').slice(stripCount).join('/') : file;

    // Ensure files are routed to Black Book_Data/ if not already
    if (!destPath.startsWith('Black Book_Data')) {
      const filename = path.basename(destPath);
      destPath = path.join('Black Book_Data', 'resources', filename);
    }

    return {
      type: 'copy',
      source: file,
      destination: destPath,
    };
  });

  return Promise.resolve({ instructions });
}

// ---------------------------------------------------------------------------
// Installer: Font Mod (priority 20)
// Handles font assets and related files
// ---------------------------------------------------------------------------

/**
 * Tests if this is a font mod (contains Fonts/ or font-related files).
 */
function testFontModContent(files) {
  const isFontMod = files.some(
    (f) => f.match(/^Fonts\//i) || f.match(/\.asset$/i) || f.match(/\.ttf$|\.otf$|\.fnt$/i),
  );

  return Promise.resolve({
    supported: isFontMod,
    requiredFiles: [],
  });
}

/**
 * Installs font mod files to Black Book_Data/Resources/Fonts/.
 */
function installFontModContent(files, gameId, modPath) {
  const fontFiles = files.filter(
    (f) => f.match(/^Fonts\//i) || f.match(/\.asset$/i) || f.match(/\.ttf$|\.otf$|\.fnt$/i),
  );

  const instructions = fontFiles.map((file) => {
    let destPath;
    if (file.startsWith('Fonts/')) {
      // Keep Fonts/ structure; route to game folder
      destPath = file;
    } else if (file.match(/\.asset$/i)) {
      // Route .asset files to Black Book_Data/Resources/Fonts/
      destPath = path.join('Black Book_Data', 'Resources', 'Fonts', path.basename(file));
    } else {
      // Route other font files to Fonts/
      destPath = path.join('Fonts', path.basename(file));
    }

    return {
      type: 'copy',
      source: file,
      destination: destPath,
    };
  });

  return Promise.resolve({ instructions });
}

// ---------------------------------------------------------------------------
// Installer: Generic Mod (priority 10)
// Fallback for any files packaged with correct game-root-relative paths
// ---------------------------------------------------------------------------

/**
 * Accepts all mods; serves as fallback installer.
 */
function testGenericModContent(files, gameId) {
  return Promise.resolve({
    supported: gameId === GAME_ID,
    requiredFiles: [],
  });
}

/**
 * Installs generic mods with optional wrapper stripping.
 */
function installGenericModContent(files, gameId, modPath) {
  const instructions = files
    .filter((f) => !f.endsWith('/'))
    .map((file) => {
      // Strip one wrapper folder if all files share the same top-level prefix
      const commonPrefix = getCommonPrefix(files);
      const stripCount = shouldStripWrapper(commonPrefix, files) ? 1 : 0;

      const destPath = stripCount > 0 ? file.split('/').slice(stripCount).join('/') : file;

      return {
        type: 'copy',
        source: file,
        destination: destPath,
      };
    });

  return Promise.resolve({ instructions });
}

// ---------------------------------------------------------------------------
// Utility Functions
// ---------------------------------------------------------------------------

/**
 * Finds the common path prefix of all files.
 */
function getCommonPrefix(files) {
  if (files.length === 0) return '';

  const parts = files[0].split('/');
  for (let i = 0; i < parts.length; i++) {
    if (!files.every((f) => f.split('/')[i] === parts[i])) {
      return parts.slice(0, i).join('/');
    }
  }

  return parts.join('/');
}

/**
 * Determines if a single wrapper folder should be stripped.
 * Strips if:
 *   - Prefix is one level deep (e.g., "black-book-tc-mod")
 *   - All files are nested under it
 *   - The prefix does NOT match a known game directory
 */
function shouldStripWrapper(prefix, files) {
  if (!prefix || prefix.split('/').length !== 1) {
    return false; // Multi-level or empty prefix
  }

  if (ROOT_GAME_DIRS.some((dir) => dir.toLowerCase() === prefix.toLowerCase())) {
    return false; // Prefix is a known game directory
  }

  // Strip if all files are under the prefix
  return files.every((f) => f.startsWith(prefix + '/'));
}

// ---------------------------------------------------------------------------
// Module Export
// ---------------------------------------------------------------------------

module.exports = function setup(context) {
  const { registerGame, registerModType, registerInstaller } = context.api;

  // Register the game
  registerGame({
    id: GAME_ID,
    name: GAME_NAME,
    mergeMods: true,
    queryPath: findGame,
    supportedTools: [],
    queryModPath: () => '.',
    logo: 'gameart.jpg',
    executable: () => GAME_EXE,
    requiredFiles: [GAME_EXE],
    setup: prepareForModding,
  });

  // Register installer: Localization mod (priority 25, runs first)
  registerInstaller(
    'black-book-localization-installer',
    25,
    testLocalizationModContent,
    installLocalizationModContent,
  );

  // Register installer: Font mod (priority 20)
  registerInstaller('black-book-font-installer', 20, testFontModContent, installFontModContent);

  // Register installer: Generic mod (priority 10, fallback)
  registerInstaller(
    'black-book-generic-installer',
    10,
    testGenericModContent,
    installGenericModContent,
  );

  return true;
};
