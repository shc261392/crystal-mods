/**
 * Vortex Game Extension — Warhammer 40,000: Dawn of War - Definitive Edition
 *
 * Steam App ID : 3556750
 * Nexus domain : warhammer40kdawnofwar
 * Main exe     : W40k.exe
 *
 * Supported mod types
 * -------------------
 *  1. Locale mods  – deployed under  Engine/Locale/<Locale>/
 *     Detected by: Engine.ucs, EnginLoc.sga, data/font/, data/art/ui/,
 *                  data/sound/, existing Engine/Locale/ prefix, or a
 *                  known-locale-name top folder (e.g. Chinese/).
 *
 *  2. Root mods    – deployed relative to the game root.
 *     Covers SGA archives, race packs, map packs, loose file mods, etc.
 *     A single top-level wrapper folder is auto-stripped when the content
 *     does not already begin with a recognised game subfolder.
 *
 * SGA note
 * --------
 * Locale mods require Engine/Locale/<Locale>/EnginLoc.sga to be renamed to
 * EnginLoc.sga.disabled so the engine loads loose files instead of the pack.
 * Vortex API restrictions in some builds disallow api access during extension
 * initialization, so this extension intentionally avoids runtime event hooks.
 * If needed, rename EnginLoc.sga manually once before deploying locale mods.
 */

"use strict";

const path = require("path");
const { fs, util } = require("vortex-api");

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const GAME_ID = "warhammer40kdawnofwar";
const STEAM_APP_ID = "3556750";
const GAME_NAME = "Warhammer 40,000: Dawn of War - Definitive Edition";
const GAME_EXE = "W40k.exe";

/** All locale subfolders shipped with DoW DE. */
const KNOWN_LOCALES = [
	"Chinese",
	"SChinese",
	"English",
	"German",
	"French",
	"Russian",
	"Korean",
	"Japanese",
	"Polish",
	"Czech",
	"Italian",
	"Spanish",
	"Ukranian",
];

/**
 * Filenames whose mere presence strongly indicates a locale mod.
 * Compared case-insensitively.
 */
const LOCALE_FILENAME_SIGNATURES = ["engine.ucs", "engineloc.sga"];

/**
 * Path substrings (normalised, lowercased) only found inside
 * Engine/Locale/<Locale>/data/…  — any match → locale mod.
 */
const LOCALE_PATH_SIGNATURES = ["data/font/", "data/art/ui/", "data/sound/"];

/**
 * Known first-level game directories used to detect game-root-relative
 * archives (layout already correct, no stripping needed).
 */
const ROOT_GAME_DIRS = [
	"W40k",
	"WXP",
	"DXP2",
	"DXP3",
	"DoWDE",
	"Engine",
	"Dev",
	"Tools",
];

// ---------------------------------------------------------------------------
// Game discovery
// ---------------------------------------------------------------------------

function findGame() {
	return util.GameStoreHelper.findByAppId([STEAM_APP_ID]).then(
		(game) => game.gamePath,
	);
}

// ---------------------------------------------------------------------------
// Setup / prepare
// ---------------------------------------------------------------------------

/**
 * Ensures the default locale target directory exists so that Vortex can
 * deploy locale mod files to it on a fresh install.
 *
 * @param {object} discovery  IDiscoveryResult — contains `.path`
 */
function prepareForModding(discovery) {
	return fs.ensureDirWritableAsync(
		path.join(discovery.path, "Engine", "Locale", "Chinese"),
	);
}

// ---------------------------------------------------------------------------
// Installer: locale mod  (priority 20 — runs before the root fallback)
// ---------------------------------------------------------------------------

/**
 * Returns `supported: true` when the archive looks like a locale mod.
 *
 * @param {string[]} files   List of paths inside the archive.
 * @param {string}   gameId  Active game ID.
 */
function testLocaleContent(files, gameId) {
	if (gameId !== GAME_ID) {
		return Promise.resolve({ supported: false, requiredFiles: [] });
	}

	const normalised = files.map((f) => f.replace(/\\/g, "/").toLowerCase());

	const isLocale = normalised.some((f) => {
		// Match by filename
		if (LOCALE_FILENAME_SIGNATURES.includes(path.basename(f))) return true;
		// Match by data subdirectory pattern
		if (LOCALE_PATH_SIGNATURES.some((seg) => f.includes(seg))) return true;
		// Archive already contains a full Engine/Locale/ prefix
		if (f.includes("engine/locale/")) return true;
		// Top-level folder is a known locale name  (e.g. Chinese/Engine.ucs)
		const firstSegment = f.split("/")[0];
		if (KNOWN_LOCALES.map((l) => l.toLowerCase()).includes(firstSegment))
			return true;
		return false;
	});

	return Promise.resolve({ supported: isLocale, requiredFiles: [] });
}

/**
 * Installs locale mod files under the correct Engine/Locale/<Locale>/ path.
 *
 * Four supported archive layouts are handled:
 *
 *   A) Full path already present:
 *        Engine/Locale/Chinese/Engine.ucs  →  keep as-is (game-root-relative)
 *
 *   B) Locale folder at archive root:
 *        Chinese/Engine.ucs                →  Engine/Locale/Chinese/Engine.ucs
 *
 *   C) Files relative to locale root (default target: Chinese):
 *        Engine.ucs                        →  Engine/Locale/Chinese/Engine.ucs
 *        data/font/gillsans_16.fnt         →  Engine/Locale/Chinese/data/font/…
 *
 *   D) Single wrapper folder around locale-root files (Vortex default packaging):
 *        wh40k-dow-de-tc-mod-v1.0.0/data/font/…  →  Engine/Locale/Chinese/data/font/…
 *        wh40k-dow-de-tc-mod-v1.0.0/Engine.ucs   →  Engine/Locale/Chinese/Engine.ucs
 *
 * @param {string[]} files  Archive file list.
 */
function installLocaleContent(files) {
	const norm = files.map((f) => f.replace(/\\/g, "/"));
	const fileEntries = norm.filter((f) => !f.endsWith("/"));

	// Layout A — archive already has Engine/Locale/ prefix
	if (fileEntries.some((f) => f.toLowerCase().includes("engine/locale/"))) {
		return Promise.resolve({
			instructions: fileEntries.map((f) => ({
				type: "copy",
				source: f,
				destination: path.normalize(f),
			})),
		});
	}

	// Layout B — top-level directory is a known locale name
	const topDir = fileEntries[0] && fileEntries[0].split("/")[0];
	if (topDir && KNOWN_LOCALES.includes(topDir)) {
		return Promise.resolve({
			instructions: fileEntries.map((f) => ({
				type: "copy",
				source: f,
				destination: path.normalize("Engine/Locale/" + f),
			})),
		});
	}

	// Layout D — single non-locale wrapper folder: strip it before mapping
	// Detect: all files share one common top-level prefix that is NOT a locale
	// name or game dir, but the files underneath look like locale-root content.
	const topDirs = [...new Set(fileEntries.map((f) => f.split("/")[0]))].filter(
		Boolean,
	);
	if (topDirs.length === 1) {
		const wrapper = topDirs[0];
		const prefixLen = wrapper.length + 1;
		const stripped = fileEntries.map((f) => f.substring(prefixLen));
		const looksLikeLocale = stripped.some((f) => {
			const low = f.toLowerCase();
			if (LOCALE_FILENAME_SIGNATURES.includes(path.basename(low))) return true;
			if (LOCALE_PATH_SIGNATURES.some((seg) => low.includes(seg))) return true;
			return false;
		});
		if (looksLikeLocale) {
			return Promise.resolve({
				instructions: fileEntries.map((f, i) => ({
					type: "copy",
					source: f,
					destination: path.normalize("Engine/Locale/Chinese/" + stripped[i]),
				})),
			});
		}
	}

	// Layout C — files relative to locale root, default to Chinese
	return Promise.resolve({
		instructions: fileEntries.map((f) => ({
			type: "copy",
			source: f,
			destination: path.normalize("Engine/Locale/Chinese/" + f),
		})),
	});
}

// ---------------------------------------------------------------------------
// Installer: root mod  (priority 50 — fallback)
// ---------------------------------------------------------------------------

/**
 * Accepts all remaining mods for this game (SGA archives, race/map packs,
 * gameplay scripts, etc.).
 *
 * @param {string[]} files   Archive file list.
 * @param {string}   gameId  Active game ID.
 */
function testRootContent(files, gameId) {
	return Promise.resolve({
		supported: gameId === GAME_ID,
		requiredFiles: [],
	});
}

/**
 * Installs mod files relative to the game root.
 *
 * Two archive layouts are handled:
 *
 *   A) Already game-root-relative (starts with a known game subfolder):
 *        W40k/data/…   →  W40k/data/… (no change)
 *
 *   B) Wrapped in a single top-level folder:
 *        MyMod/W40k/…  →  W40k/…     (wrapper stripped)
 *
 *   C) Flat / no clear structure → deploy as-is to game root
 *
 * @param {string[]} files  Archive file list.
 */
function installRootContent(files) {
	const norm = files.map((f) => f.replace(/\\/g, "/"));
	const fileEntries = norm.filter((f) => !f.endsWith("/"));

	// Layout A — archive paths already start with a known game directory
	if (
		fileEntries.some((f) =>
			ROOT_GAME_DIRS.some((dir) => f.startsWith(dir + "/")),
		)
	) {
		return Promise.resolve({
			instructions: fileEntries.map((f) => ({
				type: "copy",
				source: f,
				destination: path.normalize(f),
			})),
		});
	}

	// Layout B / C — detect a single wrapper folder and strip it if present
	const topDirs = [...new Set(fileEntries.map((f) => f.split("/")[0]))].filter(
		Boolean,
	);
	const singleWrapper = topDirs.length === 1 ? topDirs[0] : null;
	const prefixLen = singleWrapper ? singleWrapper.length + 1 : 0;

	return Promise.resolve({
		instructions: fileEntries.map((f) => ({
			type: "copy",
			source: f,
			destination: path.normalize(prefixLen ? f.substring(prefixLen) : f),
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
		queryModPath: () => ".",
		logo: "gameart.jpg",
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

	// Locale installer — higher priority (lower number) so it runs first
	context.registerInstaller(
		"dow-locale-mod",
		20,
		testLocaleContent,
		installLocaleContent,
	);

	// Root installer — lower priority, fallback for all other DoW mods
	context.registerInstaller(
		"dow-root-mod",
		50,
		testRootContent,
		installRootContent,
	);

	return true;
}

module.exports = { default: main };
