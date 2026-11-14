# Changelog — Warpstorm

## 1.2.2 — Add abilities (MVP)

Units can now gain abilities at runtime. Add an `AddAbilities` array to a unit
in `BepInEx/config/warpstorm/config.json`:

```json
"units": { "12008": { "AddAbilities": [20024] } }
```

`20024` is **Self Repair** (shared passive, +30 HP per turn; already on both
Rhino variants). The plugin clones the unit's `AbilityList`, appends valid
ability slots, and restores the original list when Warpstorm is toggled off.
The configurator preserves the field when saving but has no dedicated Abilities
UI yet. Restart a battle (or spawn new units) after saving.

## 1.2.1 — Configurator font fix

The 1.2.0 configurator was built in a clean worktree where the six Barlow UI
fonts were absent (they were excluded by the repository-wide `*.ttf` ignore
rule), so the EXE started without its embedded fonts and crashed when opening
the window:

```
Could not create glyphTypeface. Font family: Barlow Condensed
(key: avares://Warpstorm.Configurator/branding/fonts)
```

The fonts are now committed, the configurator build fails if any of the six is
missing, and the version is bumped so Vortex installs the fixed build. Plugin
behaviour is unchanged.

The configurator's embedded browser catalog is refreshed to 202 units / 442
weapons / 12 factions (Servants of Chaos included); the plugin and the
configurator's "Original" values read the live 1.8.0 tables (205 units / 446
weapons).

## 1.2.0 — Battlesector 1.8.0 support

Battlesector 1.8.0 moved unit and weapon data into per-faction tables merged by
a composite table, added the Servants of Chaos faction (10 units) plus five more
unit variants, and three weapons (Enraged Strikes, Plasma Rifle, Cyclic Ion
Raker); it also added the `ShotsPerSwitch` weapon field and a third weapon
targeting mode (`SwitchingTargetPerMember`).

- The plugin reads the merged `CompositeDataTableBase` view, so stat edits apply
  to every faction table in 1.8.0 (and still work on the 1.7.x plain tables).
- The configurator follows the composite table's `sources` array when it reads
  the game bundle; both layouts are supported.
- New fields: `ShotsPerSwitch` is editable; the third targeting mode is shown.
- Catalog regenerated from the 1.8.0 bundle: 202 units, 442 weapons, 12
  factions (Servants of Chaos included).
- Army Painter now includes the Servants of Chaos faction preset.
- Supports game version 1.8.0.

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
