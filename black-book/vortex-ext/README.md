# Black Book Vortex Extension — Build

## Structure

```
game-black-book/
├── index.js          # Main extension logic (game discovery + installers)
├── info.json         # Metadata (name, version, description)
├── DESCRIPTION.md    # Long description for Vortex UI
└── gameart.jpg       # 360×180 thumbnail — MISSING, needs to be added
```

## Files Status

- ✓ `index.js` — Complete
- ✓ `info.json` — Complete
- ✓ `DESCRIPTION.md` — Complete
- ⚠ `gameart.jpg` — Needs to be created or sourced (360×180 px recommended)

## Next Steps

1. Source or create `gameart.jpg` (game cover art, 360×180 px)
2. Package extension: `zip -r vortex-ext-game-black-book-v1.0.0.zip game-black-book/`
3. Upload to Nexus Mods for review

## Building the Extension Package

```bash
cd /home/shado/crystal-mods/black-book/vortex-ext
mkdir -p dist
zip -r dist/vortex-ext-game-black-book-v1.0.0.zip game-black-book/
```
