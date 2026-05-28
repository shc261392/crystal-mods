# Vortex extension authoring (stub)

> Status: **stub** — capture the essentials, expand as we ship more extensions.

## Primary references

- Vortex repo + wiki — <https://github.com/Nexus-Mods/Vortex/wiki>
- Extension API intro — <https://github.com/Nexus-Mods/Vortex/wiki/MODDINGWIKI-Developers-General-Introduction-to-Vortex-extensions>
- Game extension template — <https://github.com/Nexus-Mods/vortex-games>
- Nexus modding wiki — <https://modding.wiki/en/vortex>
- API typings — `vortex-api` npm package

## What a game extension is

A CommonJS module loaded at Vortex startup that registers a game definition
plus zero or more **installers**, **mod types**, **launch tools**, and
**event handlers**. No build step is required (plain JS), though TypeScript +
`vortex-api` types are recommended for non-trivial extensions.

Minimum shape:

```js
// index.js
function main(context) {
  context.registerGame({
    id: 'warhammer40kdawnofwar',
    name: 'Warhammer 40,000: Dawn of War – Definitive Edition',
    mergeMods: true,
    queryPath: findGame,           // returns install path or Promise<string>
    queryModPath: () => '.',       // mods deploy to game root by default
    logo: 'gameart.jpg',
    executable: () => 'W40k.exe',
    requiredFiles: ['W40k.exe'],
    environment: { SteamAPPId: '3556750' },
    details: { steamAppId: 3556750 },
  });
  return true;                     // returning false disables the extension
}
module.exports = { default: main };
```

## Discovery patterns

- **Steam**: prefer `util.steam.findByAppId(appId)`; fall back to
  `findByName(...)`.
- **GOG**: `util.gog.findByName(...)`.
- **Epic / Ubisoft / generic**: registry lookups (Windows) or env-var
  fallbacks; document the contract in the extension README.

## Installers

Register with `context.registerInstaller(id, priority, testSupported, install)`.
Lower priority numbers run first. Common patterns:

- Detect by **archive content** (file presence, top-level folder name).
- Strip a **single wrapper folder** when the archive is wrapped.
- Map files to a **subfolder** of the game root via `destination`.

Reference impl: [`dawn-of-war-de/unofficial-tc-patch/vortex-ext/game-warhammer40kdawnofwar/`](../../dawn-of-war-de/unofficial-tc-patch/vortex-ext/game-warhammer40kdawnofwar/).

## Packaging

`game-<id>/` folder containing `info.json` (Vortex manifest), `index.js`,
and `gameart.jpg` (640×360). Zip the folder; users drag-and-drop onto the
Vortex Extensions tab.

## Deploy / purge hooks

`context.api.events.on('did-deploy', ...)` for post-deploy steps (e.g. rename
`EnginLoc.sga` → `.disabled`). Pair with `'will-purge'` to undo.

## TODO

- Document mod types (`registerModType`) with a concrete example.
- Document load-order API (`registerLoadOrder`) for Bethesda / UE games.
- Document tool registration (`registerTool`) for launchers / editors.
- Snippet for a TypeScript extension with `vortex-api` types and esbuild.
