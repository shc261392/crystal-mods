/**
 * Vortex Game Extension — Warhammer 40,000: Battlesector
 *
 * Steam App ID : 1295500
 * GOG App ID   : 1248481392
 * Nexus domain : warhammer40kbattlesector
 * Main exe     : Warhammer 40K Battlesector.exe
 *
 * Supported mod types
 * -------------------
 *  Generic replacement mods: files packaged with their full deployment paths
 *  relative to the game root. The extension deploys them as-is.
 *
 *  Examples:
 *    - Data files: Warhammer 40K Battlesector_Data/sharedassets1.assets
 *    - Bundles: Warhammer 40K Battlesector_Data/*.bundle
 *    - Catalogs: Warhammer 40K Battlesector_Data/catalog.bin
 *
 *  The extension deploys files to the paths they specify, with optional
 *  wrapper folder stripping for convenience.
 *
 *  Backup/restore of overwritten game files (e.g. sharedassets1.assets) is
 *  handled automatically by Vortex's linking deployment: the original file is
 *  renamed to `<file>.vortex_backup` on deploy and renamed back on purge. The
 *  extension therefore does NOT implement its own backup.
 */

'use strict';

const path = require('path');
const { fs, util } = require('vortex-api');

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const GAME_ID = 'warhammer40kbattlesector';
const STEAM_APP_ID = '1295500';
const GOG_APP_ID = '1248481392';
const GAME_NAME = 'Warhammer 40,000: Battlesector';
const GAME_EXE = 'Warhammer 40K Battlesector.exe';
const DATA_DIR = 'Warhammer 40K Battlesector_Data';
const SHARED_ASSETS = 'sharedassets1.assets';

/**
 * Known first-level game directories used to detect game-root-relative
 * archives (layout already correct, no stripping needed).
 *
 * Includes BepInEx directories so combined mods that ship the BepInEx runtime
 * modding framework (winhttp.dll + BepInEx/ + dotnet/) alongside asset files
 * deploy correctly to the game root. BepInEx generates interop/config/cache/log
 * files itself at runtime; those are not part of the mod and are left untouched.
 */
const ROOT_GAME_DIRS = [
  'BepInEx',
  'D3D12',
  'dotnet',
  'Launcher',
  'Manuals',
  'Wallpapers',
  'Warhammer 40K Battlesector_Data',
];

/**
 * Loose root-level files that also indicate a game-root-relative archive
 * (e.g. the BepInEx UnityDoorstop proxy shipped at the game root).
 */
const ROOT_GAME_FILES = ['winhttp.dll', 'doorstop_config.ini', '.doorstop_version'];

// ---------------------------------------------------------------------------
// Game discovery
// ---------------------------------------------------------------------------

function findGame() {
  return util.GameStoreHelper.findByAppId([STEAM_APP_ID, GOG_APP_ID]).then((game) => game.gamePath);
}

// ---------------------------------------------------------------------------
// Setup / prepare
// ---------------------------------------------------------------------------

/**
 * Ensures the game directory is writable so Vortex can deploy mods.
 * Vortex auto-creates subdirectories during deployment and automatically
 * backs up any overwritten original files as `<file>.vortex_backup`,
 * restoring them on purge — so no manual backup is required here.
 *
 * @param {object} discovery  IDiscoveryResult — contains `.path`
 */
function prepareForModding(discovery) {
  return fs.ensureDirWritableAsync(discovery.path);
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
 * Handles two archive layouts:
 *
 *   A) Game-root-relative (files start with known game directories):
 *        Warhammer 40K Battlesector_Data/sharedassets1.assets  →  Warhammer 40K Battlesector_Data/sharedassets1.assets
 *        Warhammer 40K Battlesector_Data/catalog.bin           →  Warhammer 40K Battlesector_Data/catalog.bin
 *
 *   B) Wrapped in a single top-level folder (auto-strips wrapper):
 *        wh40k-battlesector-tc-v1.0/Warhammer 40K Battlesector_Data/sharedassets1.assets
 *        → Warhammer 40K Battlesector_Data/sharedassets1.assets
 *
 * @param {string[]} files  Archive file list.
 */
function installModContent(files) {
  // Normalize all paths to forward slashes (Vortex internal format)
  const normalized = files.map((f) => f.replace(/\\/g, '/')).filter((f) => !f.endsWith('/'));

  // Helper: Check if path starts with a known game directory (case-insensitive)
  // or is a known root-level game file (e.g. the BepInEx doorstop proxy).
  const startsWithGameDir = (filePath) =>
    ROOT_GAME_DIRS.some((dir) => filePath.toLowerCase().startsWith(`${dir.toLowerCase()}/`)) ||
    ROOT_GAME_FILES.some((f) => filePath.toLowerCase() === f.toLowerCase());

  // Layout A — Files already start with game root directories
  if (normalized.some(startsWithGameDir)) {
    return Promise.resolve({
      instructions: normalized.map((source) => ({
        type: 'copy',
        source,
        destination: source,
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
          destination: relative,
        };
      }),
    });
  }

  // Fallback — Deploy files as-is (forward slashes for consistency)
  return Promise.resolve({
    instructions: normalized.map((source) => ({
      type: 'copy',
      source,
      destination: source,
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
    requiredFiles: [GAME_EXE, path.join(DATA_DIR, SHARED_ASSETS)],
    setup: prepareForModding,
    environment: {
      SteamAPPId: STEAM_APP_ID,
    },
    details: {
      steamAppId: parseInt(STEAM_APP_ID, 10),
      gogAppId: GOG_APP_ID,
      nexusPageId: GAME_ID,
    },
  });

  // Generic mod installer — handles all replacement mods by deploying
  // files to their specified paths.
  context.registerInstaller('battlesector-mod', 20, testModContent, installModContent);

  return true;
}

module.exports = { default: main };
