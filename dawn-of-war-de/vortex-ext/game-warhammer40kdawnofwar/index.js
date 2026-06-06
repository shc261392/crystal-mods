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
 *    - Locale mods: Engine/Locale/Chinese/Engine.ucs
 *    - SGA archives: Engine/Locale/English/EnginLoc.sga
 *    - Game data: W40k/data/…
 *    - Tool/editor files: Tools/…
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
 * Ensures key game directories exist so that Vortex can deploy mod files to them.
 *
 * @param {object} discovery  IDiscoveryResult — contains `.path`
 */
function prepareForModding(discovery) {
  return fs.ensureDirWritableAsync(path.join(discovery.path, 'Engine', 'Locale'));
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
  return Promise.resolve({
    supported: gameId === GAME_ID,
    requiredFiles: [],
  });
}

/**
 * Installs mod files by deploying them to their specified paths.
 *
 * Two archive layouts are handled:
 *
 *   A) Already game-root-relative (starts with a known game subfolder):
 *        Engine/Locale/Chinese/Engine.ucs  →  Engine/Locale/Chinese/Engine.ucs
 *        W40k/data/…                       →  W40k/data/…
 *
 *   B) Wrapped in a single top-level folder (auto-strip):
 *        wh40k-dow-de-tc-mod-v1.0.3/Engine/Locale/Chinese/Engine.ucs
 *        → Engine/Locale/Chinese/Engine.ucs
 *
 * @param {string[]} files  Archive file list.
 */
function installModContent(files) {
  const norm = files.map((f) => f.replace(/\\/g, '/'));
  const fileEntries = norm.filter((f) => !f.endsWith('/'));

  // Layout A — archive paths already start with a known game directory or full path
  if (fileEntries.some((f) => ROOT_GAME_DIRS.some((dir) => f.startsWith(dir + '/')))) {
    return Promise.resolve({
      instructions: fileEntries.map((f) => ({
        type: 'copy',
        source: f,
        destination: path.normalize(f),
      })),
    });
  }

  // Layout B — detect single wrapper folder and strip it
  const topDirs = [...new Set(fileEntries.map((f) => f.split('/')[0]))].filter(Boolean);
  if (topDirs.length === 1) {
    const wrapper = topDirs[0];
    const prefixLen = wrapper.length + 1;
    const stripped = fileEntries.map((f) => f.substring(prefixLen));

    return Promise.resolve({
      instructions: fileEntries.map((f, i) => ({
        type: 'copy',
        source: f,
        destination: path.normalize(stripped[i]),
      })),
    });
  }

  // Fallback — deploy files as-is to root
  return Promise.resolve({
    instructions: fileEntries.map((f) => ({
      type: 'copy',
      source: f,
      destination: path.normalize(f),
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

  // Generic mod installer — handles all mod types by deploying to specified paths
  context.registerInstaller('dow-mod', 20, testModContent, installModContent);

  return true;
}

module.exports = { default: main };
