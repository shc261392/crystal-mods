# Changelog — Warpstorm

## 1.1.0 — Army Painter is opt-in

- **Army Painter now does no paint work in game by default.** It is opt-in:
  enable *Army Painter → Army Painter in game* and Save. A stat-only setup never
  scans the scene, reads a texture or replaces a portrait.
- **Lazy rendering.** Even when enabled, painting starts only for factions whose
  colours differ from the game's defaults or that use a scheme pack. Until then
  the plugin does not scan the scene, read a texture or replace a portrait.
- Turning it off, or resetting the last custom colour, restores the game's own
  paint within a couple of seconds.
- Colour-only schemes no longer trigger the portrait scan (it is still used for
  scheme packs and when *Recolour 2D portraits* is on).

## 1.0.0 — first public release

### Stat editor
- Edit any unit or weapon stat, including point costs. Edits apply to the game's
  live data in every mode.
- Toggle the edits on or off in game (F10), and reload them in game (F9). The
  plugin also reloads by itself when you save in the configurator.
- The configurator confirms when a running game has picked up a save.

### Army Painter
Army Painter is merged into Warpstorm.

- **Coverage.** It repaints a whole faction everywhere it appears: battle (both
  sides), army management and menus.
  - 3D models are painted through per-renderer material copies. The game's own
    property blocks (emission, highlight, dither) can no longer wipe the paint.
  - Unit portraits are replaced in the UI with `Image.overrideSprite`. The
    game's sprite reference is never changed.
- **Ten chapter schemes**, all on the Ultramarines models, each with its own
  badge:
  - Salamanders, Space Wolves, Imperial Fists, White Scars, Dark Angels
  - Raven Guard, Iron Hands, Black Templars, Crimson Fists, Blood Ravens
- **Chapter badges.** A badge replaces the chapter symbol in the Ultramarines
  decal atlas. The squad markings stay.
- **Scheme Creator.** Build your own pack: colour rules with an eyedropper, a
  live preview on portraits and real model textures, an optional badge. Then
  save it or export it as a `.zip`. *Import scheme pack…* installs other
  people's packs.
- **Bake.** The configurator pre-paints the textures after every Save. In game,
  painted textures load instantly; anything it can't reach is painted live once
  and then cached.
- **Painted textures** are capped at 2048 px (adjustable), compressed to DXT5,
  and built inside a per-frame time budget so the game doesn't stall.

### Configurator
- Battlesector-styled UI.
  - **Lists:** units and weapons with portraits, role colours, in-game stat
    tiles, and loadout / used-by links.
  - **Editing:** bulk edit (set / multiply / add / reset over the filtered list).
  - **Pages:** a Changes review, Settings (hotkeys, toggles, file locations) and
    Help.
- Languages: English, Deutsch, Español, Français, 한국어, Polski,
  Português (Brasil), Русский, 简体中文 and 繁體中文. The UI and unit, weapon and
  faction names follow the language you pick.
- Loads your saved config instead of starting blank. Asks before you close with
  unsaved changes.
- Opens from the in-game **Open Configurator** button, from Vortex
  (Dashboard → Tools, game extension ≥ 1.2.0), or from an opt-in Start-menu
  shortcut.
- App icon and Windows version info. Single-file compression is off, which
  makes antivirus false positives less likely.

### Fixes since the pre-releases
- **Army Painter 3D paint.** It never applied, because of two bugs:
  - The `_Mode` filter skipped the opaque armour materials.
  - A C# `as Texture2D` cast on an Il2CppInterop `Texture` wrapper is always
    null, so no texture was ever read.
- **Bool stats.** The game files store true/false as 1/0, so bool stats showed
  wrong originals.
- **Saved colours.** Saving in the configurator no longer resets Army Painter
  colours to their defaults.

### Build
- `make build` is the one release recipe. It produces `dist/warpstorm-v<ver>.zip`
  and every `dist/scheme-<id>-v<ver>.zip`, byte-identical for the same inputs.
