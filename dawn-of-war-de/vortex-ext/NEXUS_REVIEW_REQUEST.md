### Nexus Username

shadowevor

### Extension URL

https://www.nexusmods.com/site/mods/1934?published=1

### Game URL

https://www.nexusmods.com/warhammerdawnofwarddefinitiveedtion

### Existing Extension URL

_No response_

### New features

# Dawn of War — Definitive Edition · Vortex Game Support Extension

Adds full mod management support for **Warhammer 40,000: Dawn of War — Definitive Edition** (Steam App ID 3556750) to Vortex.

---

## Game Detection

Automatically discovers the game installation via Steam (App ID `3556750`) and registers the executable `W40k.exe`.

---

## Generic Mod Installer *(priority 20)*

Handles all replacement mods: locale packs, SGA archives, race/map packs, gameplay scripts, and loose-file mods.

**Deployment** — files are deployed to their full paths relative to the game root:
- `Engine/Locale/Chinese/Engine.ucs` → deployed to `Engine/Locale/Chinese/Engine.ucs`
- `Engine/Locale/Chinese/EnginLoc.sga` → deployed to `Engine/Locale/Chinese/EnginLoc.sga`
- `W40k/data/…` → deployed to `W40k/data/…`

**Archive layouts supported:**

| Layout | Example archive path | Deployed to |
|--------|----------------------|-------------|
| Full path present | `Engine/Locale/Chinese/Engine.ucs` | Game root (deployed as-is) |
| Single wrapper folder | `wh40k-dow-de-tc-mod-v1.0.3/Engine/Locale/Chinese/Engine.ucs` | Game root (wrapper stripped) |

A single top-level wrapper folder is automatically detected and stripped for convenience. Mods packaged with full deployment paths work out of the box.

---

## File Management

The extension lets Vortex's staging system handle file deployment and restoration natively. When a user uninstalls a mod, Vortex automatically restores the previous game state without manual backup management.

---

## Source Code

<https://github.com/shc261392/crystal-mods/tree/master/dawn-of-war-de/vortex-ext/game-warhammer40kdawnofwar>


### Information

- [x] I confirm the above is accurate

### Packaging

- [x] This extension is packaged correctly

### Testing

- [x] This game extension has been tested

### Review Tasks

If a task fails, contact the author to request changes before continuing.

- [ ] Double-check for existing extension
- [ ] Is the extension [packaged correctly](https://github.com/Nexus-Mods/Vortex/wiki/How-to-package-a-game-extension)?
- [ ] Does it install into Vortex?
- [ ] Does it correctly discover the game?
- [ ] Does it successfully install a mod?
- [ ] Does it successfully install a collection?
- [ ] Does the game run correctly with the mods installed?

When reviewed and passed, please complete the following tasks:

- [ ] Run the GitHub Actions to add to manifest
- [ ] Contact author
- [ ] Ask Community to enable the Vortex button for the game
- [ ] Update the #vortex-announcements channel on Discord
