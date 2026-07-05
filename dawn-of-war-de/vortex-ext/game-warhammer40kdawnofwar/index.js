/**
 * Vortex Game Extension — Warhammer 40,000: Dawn of War - Definitive Edition
 *
 * Steam App ID : 3556750
 * Nexus domain : warhammer40kdawnofwar
 * Main exe     : W40k.exe
 *
 * Supported mod types
 * -------------------
 *  Generic replacement mods: any files packaged with their full deployment paths
 *  relative to the game root. The extension deploys them as-is.
 *
 *  Examples:
 *    - Localization: Engine/Locale/Chinese/Engine.ucs
 *    - Game data: W40k/, WXP/, DXP2/, DXP3/, DoWDE/
 *    - SGA archives: Engine/Locale/English/EnginLoc.sga
 *    - Tools/editors: Tools/…, Dev/…
 *
 *  The extension simply deploys files to the paths they specify, with optional
 *  wrapper folder stripping for convenience.
 */

'use strict';

const path = require('path');
const { fs, util } = require('vortex-api');

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const GAME_ID = 'warhammer40kdawnofwar';
const STEAM_APP_ID = '3556750';
const GAME_NAME = 'Warhammer 40,000: Dawn of War - Definitive Edition';
const GAME_EXE = 'W40k.exe';

/**
 * Known first-level game directories used to detect game-root-relative
 * archives (layout already correct, no stripping needed).
 */
const ROOT_GAME_DIRS = ['W40k', 'WXP', 'DXP2', 'DXP3', 'DoWDE', 'Engine', 'Dev', 'Tools'];

// ---------------------------------------------------------------------------
// Game discovery
// ---------------------------------------------------------------------------

function findGame() {
  return util.GameStoreHelper.findByAppId([STEAM_APP_ID]).then((game) => game.gamePath);
}

// ---------------------------------------------------------------------------
// Setup / prepare
// ---------------------------------------------------------------------------

/**
 * Ensures the game directory is writable so Vortex can deploy mods.
 * Vortex will auto-create subdirectories during deployment.
 *
 * @param {object} discovery  IDiscoveryResult — contains `.path`
 */
function prepareForModding(discovery) {
  return fs.ensureDirWritableAsync(discovery.path);
}

function hasFomodInstaller(files) {
  return files.some((filePath) => {
    const normalized = filePath.replace(/\\/g, '/');
    return (
      path.basename(normalized).toLowerCase() === 'moduleconfig.xml' &&
      path.basename(path.dirname(normalized)).toLowerCase() === 'fomod'
    );
  });
}

// ---------------------------------------------------------------------------
// Installer: generic mod  (priority 20)
// ---------------------------------------------------------------------------

/**
 * Accepts all mods for this game. The extension handles any file layout
 * by deploying files to their specified paths (with optional wrapper stripping).
 *
 * @param {string[]} files   List of paths inside the archive.
 * @param {string}   gameId  Active game ID.
 */
function testModContent(files, gameId) {
  if (hasFomodInstaller(files)) {
    return Promise.resolve({
      supported: false,
      requiredFiles: [],
    });
  }

  return Promise.resolve({
    supported: gameId === GAME_ID,
    requiredFiles: [],
  });
}

/**
 * Installs mod files by deploying them to their specified paths.
 *
 * Handles two archive layouts:
 *
 *   A) Game-root-relative (files start with known game directories):
 *        Engine/Locale/Chinese/Engine.ucs  →  Engine/Locale/Chinese/Engine.ucs
 *        DXP2/data/attrib/…                →  DXP2/data/attrib/…
 *        W40k/Scenarios/…                  →  W40k/Scenarios/…
 *
 *   B) Wrapped in a single top-level folder (auto-strips wrapper):
 *        wh40k-dow-de-tc-mod-v1.0.3/Engine/Locale/Chinese/Engine.ucs
 *        → Engine/Locale/Chinese/Engine.ucs
 *
 * @param {string[]} files  Archive file list.
 */
function installModContent(files) {
  // Normalize all paths to forward slashes (Vortex internal format)
  const normalized = files.map((f) => f.replace(/\\/g, '/')).filter((f) => !f.endsWith('/'));

  // Helper: Check if path starts with a known game directory (case-insensitive)
  const startsWithGameDir = (filePath) =>
    ROOT_GAME_DIRS.some((dir) => filePath.toLowerCase().startsWith(`${dir.toLowerCase()}/`));

  // Layout A — Files already start with game root directories
  if (normalized.some(startsWithGameDir)) {
    return Promise.resolve({
      instructions: normalized.map((source) => ({
        type: 'copy',
        source,
        destination: path.normalize(source),
      })),
    });
  }

  // Detect potential wrapper folder
  const topLevelDirs = [...new Set(normalized.map((f) => f.split('/')[0]))].filter(Boolean);
  const hasSingleWrapper = topLevelDirs.length === 1;
  const hasNestedContent = normalized.some((f) => f.includes('/'));

  // Layout B — Single wrapper folder containing actual mod files
  if (hasSingleWrapper && hasNestedContent) {
    const wrapper = topLevelDirs[0];

    return Promise.resolve({
      instructions: normalized.map((source) => {
        // Strip the wrapper folder using path.posix.relative
        const relative = path.posix.relative(wrapper, source);
        return {
          type: 'copy',
          source,
          destination: path.normalize(relative),
        };
      }),
    });
  }

  // Fallback — Deploy files as-is
  return Promise.resolve({
    instructions: normalized.map((source) => ({
      type: 'copy',
      source,
      destination: path.normalize(source),
    })),
  });
}

// ---------------------------------------------------------------------------
// Main entry point
// ---------------------------------------------------------------------------

function main(context) {
  context.registerGame({
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
    environment: {
      SteamAPPId: STEAM_APP_ID,
    },
    details: {
      steamAppId: STEAM_APP_ID,
      nexusPageId: GAME_ID,
    },
  });

  // Generic mod installer — handles all non-FOMOD replacement mods by deploying
  // files to their specified paths. FOMOD archives are intentionally declined
  // in testModContent() so Vortex can show its built-in installer UI.
  context.registerInstaller('dow-mod', 20, testModContent, installModContent);

  return true;
}

module.exports = { default: main };
