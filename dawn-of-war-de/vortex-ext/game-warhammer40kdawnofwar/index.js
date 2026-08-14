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
 * Mod type for standalone `.module` mods. Unlike file-replacement mods (which
 * deploy into the game directory), the Relic engine loads authored mods from
 * the user-profile folder:
 *   Windows : %APPDATA%\Relic Entertainment\Dawn of War\mods
 *   Proton  : <lib>/steamapps/compatdata/<appid>/pfx/drive_c/users/steamuser/
 *             AppData/Roaming/Relic Entertainment/Dawn of War/mods
 */
const USERMOD_TYPE = 'dow-de-usermod';
const USERMOD_REL = path.join('Relic Entertainment', 'Dawn of War', 'mods');

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

/**
 * Resolve the user-profile "mods" folder where the engine auto-loads authored
 * `.module` mods. Returns undefined if it cannot be determined.
 *
 * @param {string|undefined} gamePath  Discovered game install path.
 */
function resolveUserModsFolder(gamePath) {
  if (process.platform === 'win32') {
    const appData =
      process.env.APPDATA ||
      (process.env.USERPROFILE
        ? path.join(process.env.USERPROFILE, 'AppData', 'Roaming')
        : undefined);
    return appData ? path.join(appData, USERMOD_REL) : undefined;
  }

  // Linux / Proton: the mods folder lives inside the Proton prefix.
  // gamePath = <lib>/steamapps/common/Dawn of War Definitive Edition
  if (gamePath) {
    const steamapps = path.resolve(gamePath, '..', '..');
    return path.join(
      steamapps,
      'compatdata',
      STEAM_APP_ID,
      'pfx',
      'drive_c',
      'users',
      'steamuser',
      'AppData',
      'Roaming',
      USERMOD_REL,
    );
  }

  return undefined;
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

/** True if the archive contains a Dawn of War `.module` definition file. */
function hasModuleFile(files) {
  return files.some((f) => f.replace(/\\/g, '/').toLowerCase().endsWith('.module'));
}

// ---------------------------------------------------------------------------
// Installer: standalone .module mod  (priority 15 — before the generic one)
// ---------------------------------------------------------------------------

/**
 * Accepts archives that contain a `.module` file (and are not FOMOD). These are
 * authored Dawn of War mods that must deploy to the user-profile mods folder.
 */
function testUserModContent(files, gameId) {
  return Promise.resolve({
    supported: gameId === GAME_ID && hasModuleFile(files) && !hasFomodInstaller(files),
    requiredFiles: [],
  });
}

/**
 * Deploys a `.module` mod while preserving its own top-level folder, so the
 * result is `mods/<ModName>/<ModName>.module`. Emits `setmodtype` so Vortex
 * deploys it to the user-profile mods folder rather than the game directory.
 *
 * Handles three archive shapes:
 *   - `.module` inside its own folder        → deploy as-is
 *   - `.module` under an extra wrapper folder → strip down to the mod folder
 *   - `.module` loose at the archive root     → wrap under `<ModName>/`
 *
 * @param {string[]} files  Archive file list.
 */
function installUserModContent(files) {
  const normalized = files.map((f) => f.replace(/\\/g, '/')).filter((f) => !f.endsWith('/'));
  const moduleFile = normalized.find((f) => f.toLowerCase().endsWith('.module'));
  const moduleDir = path.posix.dirname(moduleFile);

  let mapDest;
  if (moduleDir === '.') {
    const modName = path.posix.basename(moduleFile, path.posix.extname(moduleFile));
    mapDest = (source) => `${modName}/${source}`;
  } else {
    const modParent = path.posix.dirname(moduleDir);
    mapDest = (source) => (modParent === '.' ? source : path.posix.relative(modParent, source));
  }

  const instructions = normalized.map((source) => ({
    type: 'copy',
    source,
    destination: mapDest(source),
  }));
  instructions.unshift({ type: 'setmodtype', value: USERMOD_TYPE });

  return Promise.resolve({ instructions });
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

  // Standalone .module mods are handled by the dedicated installer above.
  if (hasModuleFile(files)) {
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

  // Mod type: standalone `.module` mods deploy to the user-profile mods folder
  // (%APPDATA%\Relic Entertainment\Dawn of War\mods) instead of the game dir.
  context.registerModType(
    USERMOD_TYPE,
    25,
    (gameId) => gameId === GAME_ID,
    () => {
      const state = context.api.getState();
      const discovery = util.getSafe(
        state,
        ['settings', 'gameMode', 'discovered', GAME_ID],
        undefined,
      );
      return resolveUserModsFolder(discovery?.path);
    },
    () => Promise.resolve(false),
    { name: 'Dawn of War Mod (.module)', mergeMods: true },
  );

  // Installer for standalone `.module` mods — runs before the generic installer.
  context.registerInstaller('dow-de-usermod', 15, testUserModContent, installUserModContent);

  return true;
}

module.exports = { default: main };
