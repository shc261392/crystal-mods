/**
 * Vortex Game Extension — Black Book
 *
 * Steam App ID : 1138660
 * Nexus domain : blackbook
 * Main exe     : Black Book.exe
 * Data dir     : Black Book_Data
 * Engine       : Unity 2018.4.31f1 (Mono, x64)
 *
 * Supported mod types
 * -------------------
 *  Generic replacement mods: files packaged with their full deployment paths
 *  relative to the game root. The extension deploys them as-is.
 *
 *  Examples:
 *    - Localization data:
 *        Black Book_Data/StreamingAssets/Config/<dir>/config_zh.yaml
 *    - BepInEx plugins:
 *        BepInEx/plugins/BlackBookTcFont.dll
 *        BepInEx/plugins/BlackBookTcFont/{opencc_st.tsv,opencc_tw.tsv,tcserif}
 *    - BepInEx framework (root-level loader files):
 *        winhttp.dll, doorstop_config.ini, .doorstop_version
 *
 *  The extension deploys files to the paths they specify, with optional
 *  wrapper folder stripping for convenience.
 *
 *  Backup/restore of overwritten game files (e.g. the Simplified Chinese
 *  config_zh.yaml files) is handled automatically by Vortex's linking
 *  deployment: the original file is renamed to `<file>.vortex_backup` on deploy
 *  and renamed back on purge. The extension therefore does NOT implement its
 *  own backup.
 *
 *  Registers both store builds: Steam (App ID 1138660) and GOG
 *  (product id 2098791460). Both ids come from the repo's metadata.jsonc, which
 *  is generated from PCGamingWiki — the repository's designated source of truth
 *  for store IDs. Windows only.
 */

'use strict';

const path = require('path');
const { fs, util } = require('vortex-api');

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const GAME_ID = 'black-book';
const STEAM_APP_ID = '1138660';
// From metadata.jsonc (PCGamingWiki). The id list there also carries two DLC ids.
const GOG_ID = '2098791460';
// The game's URL slug on nexusmods.com — distinct from GAME_ID (the internal
// Vortex id). Used so Vortex can resolve Nexus mod-page URLs and nxm:// links.
const NEXUS_DOMAIN = 'blackbook';
const GAME_NAME = 'Black Book';
const GAME_EXE = 'Black Book.exe';
const DATA_DIR = 'Black Book_Data';

/**
 * Known first-level game directories used to detect game-root-relative
 * archives (layout already correct, no stripping needed).
 *
 * Includes BepInEx so plugin mods that ship the modding runtime
 * (winhttp.dll + BepInEx/) alongside game data deploy correctly to the game
 * root. BepInEx generates its own config/cache/log files at runtime; those are
 * not part of any mod and are left untouched.
 */
const ROOT_GAME_DIRS = ['Black Book_Data', 'BepInEx'];

/**
 * Loose root-level files that also indicate a game-root-relative archive
 * (e.g. the BepInEx UnityDoorstop proxy shipped at the game root).
 */
const ROOT_GAME_FILES = ['winhttp.dll', 'doorstop_config.ini', '.doorstop_version'];

// ---------------------------------------------------------------------------
// Game discovery
// ---------------------------------------------------------------------------

function findGame() {
  // findByAppId resolves Steam App IDs and GOG product ids alike.
  return util.GameStoreHelper.findByAppId([STEAM_APP_ID, GOG_ID]).then((game) => game.gamePath);
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
 * Handles three archive layouts:
 *
 *   A) Game-root-relative (files start with known game directories or are
 *      known root-level loader files):
 *        Black Book_Data/StreamingAssets/Config/…/config_zh.yaml
 *          → Black Book_Data/StreamingAssets/Config/…/config_zh.yaml
 *        BepInEx/plugins/BlackBookTcFont.dll
 *          → BepInEx/plugins/BlackBookTcFont.dll
 *        winhttp.dll → winhttp.dll
 *
 *   B) Wrapped in a single top-level folder (auto-strips wrapper):
 *        tc-localization-v1.3.0/Black Book_Data/StreamingAssets/…/config_zh.yaml
 *        → Black Book_Data/StreamingAssets/…/config_zh.yaml
 *
 *   C) Fallback — deploy files as-is (forward slashes for consistency).
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

  // Layout C — Deploy files as-is (forward slashes for consistency)
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
    requiredFiles: [GAME_EXE],
    setup: prepareForModding,
    environment: {
      SteamAPPId: STEAM_APP_ID,
    },
    details: {
      steamAppId: parseInt(STEAM_APP_ID, 10),
      gogAppId: parseInt(GOG_ID, 10),
      nexusPageId: NEXUS_DOMAIN,
    },
  });

  // Generic mod installer — handles all replacement mods (localization data,
  // BepInEx plugins and the BepInEx framework) by deploying files to their
  // specified paths, with single-wrapper-folder stripping.
  context.registerInstaller('black-book-mod', 20, testModContent, installModContent);

  return true;
}

module.exports = { default: main };
