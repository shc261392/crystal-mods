# Black Book Vortex Extension

The Vortex game extension for **Black Book** (Steam App ID `1138660`, Windows)
lives in [`game-black-book/`](game-black-book/). See its
[README](game-black-book/README.md) for the full description and the
[NEXUS_DESCRIPTION.md](game-black-book/NEXUS_DESCRIPTION.md) for the Nexus mod
page copy.

## Structure

```
game-black-book/
├── index.js             # Game registration + generic installer
├── info.json            # Vortex manifest (name, author, version, description)
├── gameart.jpg          # 640×360 game art
├── README.md            # Extension README
├── NEXUS_DESCRIPTION.md # Copy for the Nexus mod page
└── scripts/
    ├── fetch-gameart.sh # Regenerate gameart.jpg from the Steam header
    └── package.js       # Build the flat Nexus-ready zip
```

## Install order (all three Black Book mods)

1. **BepInEx Framework** — `bepinex-framework-v*.zip` (shared runtime, once)
2. **Traditional Chinese Localization** — `tc-localization-v*.zip`
3. **This extension** — `game-black-book-*.zip` (install first if Vortex does
   not yet list Black Book)

## Packaging for Nexus

The extension archive must be flat (no wrapper folder). From
`game-black-book/`:

```bash
node scripts/package.js
```

Output: `dist/game-black-book-<version>.zip`, containing `info.json`,
`index.js`, `gameart.jpg` and `README.md` at the top level.

## Regenerating game art

```bash
bash game-black-book/scripts/fetch-gameart.sh   # -> game-black-book/gameart.jpg
```

Hand-review the result (640×360, dark-background-safe, no text) before
submitting to Nexus.
