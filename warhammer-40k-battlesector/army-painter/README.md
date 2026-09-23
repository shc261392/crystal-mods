# Army Painter

A BepInEx 6 (IL2CPP) runtime plugin that **recolors the local player's army** in
Warhammer 40,000: Battlesector — Blood Angels red → Ultramarines blue, Ork green
→ any colour you like — with an **in-game colour-changing UI**.

## Requires

- **BepInEx Framework** mod (the BepInEx 6 IL2CPP runtime). Install it first.

## What it does

- **Recolor engine.** For every player unit it auto-detects the two dominant
  paint colours of each unit's albedo texture (e.g. red armour + gold trim),
  remaps those hues toward your chosen **primary / secondary** colours, and
  applies the result per-renderer via `MaterialPropertyBlock`. Baked shading is
  preserved (luminance kept); metal / grime / neutral pixels are left untouched;
  glowing bits (emission) are never touched.
- **Color-changing UI.** Press **F10** (or the on-screen **Army Painter** button)
  to open a window with: faction preset buttons, primary/secondary RGB sliders +
  hex field, **Live tint preview**, **Apply paint**, and **Reset**.
- **Persistence.** Your colours are saved per faction in the BepInEx config
  (`com.crystalmods.armypainter.cfg`); new / revived units are repainted
  automatically.
- **Scope.** The local player's whole army (single-player and skirmish). In the
  army-builder / model preview it paints every visible model so you can test
  colours before a battle.

**No game asset is ever modified** — the plugin only sets runtime
`MaterialPropertyBlock`s on unit renderers, exactly like the game's own
`RendererMaterialModifier`. **Reset** restores the original paint.

## Install

1. Install the **BepInEx Framework** mod and launch the game once.
2. Install **Army Painter** (Vortex recommended) and deploy.
3. Launch the game, open the painter (F10 or button), pick colours, **Apply paint**.

## Configuration

Edit `BepInEx/config/com.crystalmods.armypainter.cfg`, or use the in-game UI:

| Key | Default | Meaning |
|---|---|---|
| `ToggleKey` | 282 (F10) | KeyCode int that toggles the UI. |
| `ShowButton` | true | Always-visible on-screen toggle button. |
| `AutoApply` | true | Repaint new/revived player units automatically. |
| `HueWindow` | 0.16 | Hue distance around each detected paint colour to recolor. |
| `SatThreshold` | 0.08 | Below this saturation pixels are treated as neutral and kept. |
| `BlendFeather` | 0.08 | Edge feather around the remap window. |
| `DiagMode` | false | Verbose logging of contestants/units/renderers/textures. |
| `Faction.*/Primary`, `Faction.*/Secondary` | — | Saved hex colours per faction. |

## Diagnostics

If units aren't picked up, set `DiagMode = true`, relaunch, start a battle, and
check `BepInEx/LogOutput.log` for `[ArmyPainter] DIAG` lines (contestants,
player unit counts, renderer/material/texture names, readable flags). This tells
us exactly how to adjust the ownership / model mapping.

## Compatibility

Runtime plugin (ships only `BepInEx/plugins/ArmyPainter.dll`) — no asset bundle,
so no file conflicts:

- **BepInEx Framework** — required.
- **Red Laser Lasgun** — compatible (independent plugin).
- **The Great Crusade** — compatible (that mod edits a data bundle).
- **Traditional Chinese Localization** — compatible (coexists with `TCFix.dll`).

## Build

```bash
./package.sh        # dotnet build -c Release + zip -> ../dist/army-painter-v1.0.0.zip
```

Requires the .NET SDK and the game's `BepInEx/interop` assemblies (present after
BepInEx has run once). Override `GameDir` if the game lives elsewhere:

```bash
dotnet build -c Release -p:GameDir="C:\Program Files (x86)\Steam\steamapps\common\Warhammer 40000 Battlesector"
```

## Disclaimer

Fan-made, single-player, cosmetic. Not affiliated with or endorsed by Black Lab
Games or Games Workshop.
