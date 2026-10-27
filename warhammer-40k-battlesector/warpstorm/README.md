# Warpstorm

Stat editor and Army Painter for *Warhammer 40,000: Battlesector* (BepInEx 6,
IL2CPP). Version 1.1.0. Single-player only.

- **Stat editor.** Change any unit or weapon stat, including points costs. Edits
  apply in every game mode and can be toggled on and off in game.
- **Army Painter.** Repaint a faction everywhere it appears, both the 3D models
  and the portraits. Use your own colours or one of ten curated chapter schemes
  with badges, or build a scheme pack in the Scheme Creator. **Opt-in:** it stays
  completely idle in game until you enable it and change a colour (see below).
- **Configurator.** A Windows app that edits all of the above. It comes in ten
  languages and pre-paints textures so the game loads them instantly.

The plugin only adds files; it modifies no game file. It stacks with other mods
(The Great Crusade, TC Localization, …).

## Install

1. Install the **BepInEx Framework** mod and start the game once.
2. Install **Warpstorm** with Vortex, or extract the zip into the game folder. It
   adds only `BepInEx/plugins/Warpstorm/`: the plugin, the configurator, and the
   built-in scheme packs.
3. Don't also install the standalone *Army Painter* mod, because Warpstorm
   already contains it.

## Open the configurator

Any of these opens it:

- **In game:** the small Warpstorm box in the top-left corner → **Open Configurator**.
- **Vortex:** Dashboard → Tools → *Warpstorm Configurator* (needs the Battlesector
  game extension 1.2.0 or later).
- **Start menu:** set it up once under *Settings → Add to Start menu*.
- **The file itself:** `<game>\BepInEx\plugins\Warpstorm\Warpstorm.Configurator.exe`

## Use

| Page | What it does |
|---|---|
| Units / Weapons | Search and filter, open an entry, type a new value. Steppers, per-stat reset, *Bulk edit* for the filtered list, loadout and *used by* links |
| Army Painter | Per faction: custom colours or a scheme pack; *Create your own scheme…*; *Import scheme pack…*; bake |
| Changes | Everything that differs from the game; unsaved items are marked |
| Settings | Game folder, hotkeys, toggles, file locations |
| Help | Quick start and the Army Painter tutorial |

**Save** (Ctrl+S) writes everything. A running game reloads it and the
configurator confirms it; otherwise the changes apply at the next launch. Stat
changes affect units created after the reload, so restart a battle that is
already running.

**Army Painter is opt-in.** On the *Army Painter* page, switch *Army Painter in
game* on and Save. Painting then starts only for factions with a non-default
colour or a scheme pack. If you only edit stats, leave it off: the plugin does no
scanning, texture work or rendering at all.

**In game:** **F10** toggles stat edits, **F9** reloads, **F1** opens the Army
Painter window. You can change the keys under Settings.

The full Army Painter walkthrough is in
[docs/army-painter-guide.md](docs/army-painter-guide.md). The scheme pack format
is described in [schemes/README.md](schemes/README.md).

## Files

| Path | Holds |
|---|---|
| `BepInEx/config/warpstorm/config.json` | stat edits (plain JSON, hand-editable) |
| `BepInEx/config/com.crystalmods.armypainter.cfg` | paint colours and chosen schemes |
| `BepInEx/config/com.crystalmods.warpstorm.cfg` | hotkeys and toggles |
| `BepInEx/config/warpstorm/schemes/` | scheme packs you made or imported |
| `BepInEx/cache/warpstorm/paint/` | baked paint (safe to delete) |
| `BepInEx/config/warpstorm/status.json`, `paint-status.json` | the plugin's report to the configurator |

## Troubleshooting

- **Army Painter does nothing.** It is opt-in: on the *Army Painter* page, switch
  *Army Painter in game* on, give a faction a non-default colour or a scheme,
  and Save.
- **Nothing changes in game.** Open `BepInEx/LogOutput.log` and look for these
  lines:
  - `Warpstorm ON … N edit(s) applied` for stat edits.
  - `[ArmyPainter] scene: …` for paint. It shows painted, kept, "nothing
    paintable" and "texture read failed" counts for each faction.
  - No `[Warpstorm]` lines at all means the DLL didn't load. Redeploy the mod in
    Vortex.
- **The configurator won't start.** Check `warpstorm-configurator.log` next to
  the EXE.
- **Windows SmartScreen or antivirus warning.** The EXE is not code-signed. Choose
  *More info → Run anyway*, and compare the SHA-256 with the one on the release
  page.

## Build

You need the .NET SDK, plus the game's `BepInEx/interop` assemblies, which
appear after BepInEx has run once.

```bash
make build      # the release: dist/warpstorm-v1.1.0.zip + dist/scheme-<id>-v<ver>.zip, byte-identical per input
make selftest   # headless pipeline check (game detect, catalog, bundle read, config round-trip)
python3 configurator/scripts/check-i18n.py   # all 10 string tables complete
```

Layout:

```
plugin/        BepInEx plugin: Plugin.cs (stats), TableApplier.cs, ArmyPainter.cs (paint)
configurator/  Avalonia app; i18n/<lang>.json string tables; Baker.cs (bake); MainWindow.*.cs (pages)
shared/        compiled into both: PaintMath.cs (recolour), SchemePack.cs, PaintCache.cs, fields.json
schemes/       built-in scheme packs (scheme.json + badge.png) and make-badges.py
tools/SchemeBuilder/  renders pack portraits and review sheets with the shared code
```

## Credits

- Unit and weapon data, names in ten languages and portraits come from
  **BattleSector Tools**.
- **Barlow** typeface by Jeremy Tribby, under the SIL Open Font License
  (`configurator/branding/fonts/OFL.txt`).
- Icons from **Material Design Icons** by Pictogrammers, under the Apache 2.0
  licence.
- Built with **Avalonia**, **AssetsTools.NET** (with its texture decoders) and
  **BCnEncoder.Net**.

Fan-made. Not affiliated with Black Lab Games or Games Workshop. Warhammer 40,000
and the chapter names belong to Games Workshop. The chapter badges are original
stencil drawings.
