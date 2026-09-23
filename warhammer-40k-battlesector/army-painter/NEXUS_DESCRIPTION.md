# Army Painter

Recolor your army's paint scheme — **in-game** — with a color-changing UI.

**[b]Army Painter[/b]** is a BepInEx 6 (IL2CPP) plugin for Warhammer 40,000:
Battlesector. It recolors the local player's units (primary + secondary paint
colours) at runtime and gives you a hotkey-toggled window to pick new colours —
think Blood Angels red → Ultramarines blue, Ork green → whatever you like.

## Features

- **Primary + secondary recolor.** The plugin auto-detects the two dominant
  paint colours of each unit texture (armour + trim), then remaps those hues
  toward your chosen colours. Baked shading is preserved, metal/grime stays put,
  and glowing bits are untouched.
- **Color-changing UI.** Press **F10** (or click the on-screen **Army Painter**
  button) to open: faction presets, RGB sliders, hex input, live tint preview,
  **Apply paint**, and **Reset**.
- **Per-faction persistence.** Colours are saved per faction in the BepInEx
  config and auto-applied to new units.
- **Whole army scope.** Paints every unit you own; in the army-builder / model
  preview it paints every visible model so you can test colours first.

## Install

1. Install the **[b]BepInEx Framework[/b]** mod (required, install first) and
   launch the game once.
2. Install **Army Painter** with Vortex (recommended) and click **Deploy**.
3. Launch the game, open the painter, pick colours, **Apply paint**.

## Reversibility

The mod only sets runtime `MaterialPropertyBlock`s — it never modifies a game
file or shared material. **Reset** restores the original paint instantly.
Uninstall = remove the mod (plugin-only, no file conflicts with any other mod).

## Compatibility

Plugin-only (ships `BepInEx/plugins/ArmyPainter.dll`), so it coexists with
**Red Laser Lasgun**, **The Great Crusade**, and the **Traditional Chinese
Localization** mods without conflicts.

## FAQ

- **Nothing repaints?** Enable `DiagMode = true` in
  `BepInEx/config/com.crystalmods.armypainter.cfg`, relaunch, start a battle,
  and share the `[ArmyPainter] DIAG` lines from `BepInEx/LogOutput.log`.
- **The UI doesn't open on F10?** Use the on-screen button, or change
  `ToggleKey` in the config.

Fan-made, single-player, cosmetic. Not affiliated with Black Lab Games or Games
Workshop.
