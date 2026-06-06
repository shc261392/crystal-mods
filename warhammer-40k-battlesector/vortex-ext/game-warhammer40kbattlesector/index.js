/*
 * Vortex extension for Warhammer 40,000: Battlesector.
 *
 * - Detects Steam + GOG installs.
 * - Ensures the game data folder is writable.
 * - One-time backup of sharedassets1.assets so users can always revert.
 * - Custom mod type + installer for "asset replacement" mods that ship a
 *   replacement sharedassets1.assets (which is how the WH40K BS modding
 *   community typically distributes localisation / text mods today).
 *
 * Reference: https://github.com/Nexus-Mods/Vortex/wiki/How-to-package-a-game-extension
 */

const path = require('path');
const { fs, util } = require('vortex-api');

const GAME_ID = 'warhammer40kbattlesector';
const STEAM_APP_ID = '1295500';
const GOG_APP_ID = '1248481392';

const GAME_EXE = 'Warhammer 40K Battlesector.exe';
const DATA_DIR = 'Warhammer 40K Battlesector_Data';
const SHARED_ASSETS = 'sharedassets1.assets';
const BACKUP_SUFFIX = '.vortex-backup';

function findGame() {
  return util.GameStoreHelper.findByAppId([STEAM_APP_ID, GOG_APP_ID])
    .then(game => game.gamePath);
}

function dataDirOf(discovery) {
  return path.join(discovery.path, DATA_DIR);
}

async function backupSharedAssets(api, discovery) {
  const target = path.join(dataDirOf(discovery), SHARED_ASSETS);
  const backup = target + BACKUP_SUFFIX;
  try {
    await fs.statAsync(backup);
    return; // already have a backup, never overwrite it
  } catch (err) {
    // backup missing -> create it
  }
  try {
    await fs.statAsync(target);
  } catch (err) {
    // original file missing — nothing to back up; treat as soft failure
    api.sendNotification({
      id: 'wh40k-bs-no-asset',
      type: 'warning',
      message: `${SHARED_ASSETS} not found in game data folder. Re-verify game files via Steam/GOG.`,
      allowSuppress: true,
    });
    return;
  }
  try {
    await fs.copyAsync(target, backup);
    api.sendNotification({
      id: 'wh40k-bs-backup-done',
      type: 'info',
      message: `Backed up ${SHARED_ASSETS} (so you can always revert).`,
      displayMS: 6000,
    });
  } catch (err) {
    api.showErrorNotification(
      `Failed to back up ${SHARED_ASSETS}`,
      err,
      { allowReport: false }
    );
  }
}

async function prepareForModding(api, discovery) {
  await fs.ensureDirWritableAsync(dataDirOf(discovery));
  await backupSharedAssets(api, discovery);
}

// Mod type: a mod is treated as an "asset replacement" mod if it contains
// a sharedassets1.assets at the archive root. We route the file into the
// game's *_Data folder by reporting that path as the mod root.
function getAssetModPath(api) {
  const state = api.store.getState();
  const discovery = util.getSafe(state, ['settings', 'gameMode', 'discovered', GAME_ID], undefined);
  if (!discovery || !discovery.path) {
    return undefined;
  }
  return dataDirOf(discovery);
}

function isAssetReplacementMod(instructions) {
  return Promise.resolve(
    instructions.some(inst =>
      inst.type === 'copy'
      && inst.destination
      && path.basename(inst.destination).toLowerCase() === SHARED_ASSETS
    )
  );
}

function testSharedAssetsArchive(files, gameId) {
  if (gameId !== GAME_ID) {
    return Promise.resolve({ supported: false, requiredFiles: [] });
  }
  const hit = files.find(f =>
    path.basename(f).toLowerCase() === SHARED_ASSETS
  );
  return Promise.resolve({ supported: !!hit, requiredFiles: [] });
}

function installSharedAssetsArchive(files) {
  // Flatten: take everything from the archive and place it relative to the
  // mod root. The shared-assets mod type then maps mod root -> game _Data.
  const instructions = files
    .filter(f => !f.endsWith(path.sep))
    .map(f => ({
      type: 'copy',
      source: f,
      // strip any leading folder so sharedassets1.assets lands at the root
      destination: path.basename(f),
    }));
  return Promise.resolve({ instructions });
}

function main(context) {
  context.registerGame({
    id: GAME_ID,
    name: 'Warhammer 40,000: Battlesector',
    mergeMods: true,
    queryPath: findGame,
    queryModPath: () => '.',
    logo: 'gameart.png',
    executable: () => GAME_EXE,
    requiredFiles: [
      GAME_EXE,
      path.join(DATA_DIR, SHARED_ASSETS),
    ],
    setup: (discovery) => prepareForModding(context.api, discovery),
    environment: { SteamAPPId: STEAM_APP_ID },
    details: {
      steamAppId: parseInt(STEAM_APP_ID, 10),
      gogAppId: GOG_APP_ID,
    },
  });

  context.registerModType(
    'wh40k-bs-shared-assets',
    25,
    (gameId) => gameId === GAME_ID,
    () => getAssetModPath(context.api),
    isAssetReplacementMod,
    { mergeMods: false, name: 'Shared Assets Replacement' }
  );

  context.registerInstaller(
    'wh40k-bs-sharedassets-installer',
    25,
    testSharedAssetsArchive,
    installSharedAssetsArchive
  );

  return true;
}

module.exports = { default: main };
