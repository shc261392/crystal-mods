# Army Painter scheme packs

A scheme pack repaints one game faction with curated results, e.g.
**Salamanders** repaints the Ultramarines models and portraits.

```
schemes/<id>/scheme.json     # the recipe (committed)
```

`make build` renders each pack with `tools/SchemeBuilder` (the same
`shared/PaintMath.cs` the plugin uses in game). Each rendered pack ships in two places:

- inside the mod at `BepInEx/plugins/Warpstorm/schemes/<id>/`
- as `dist/scheme-<id>-v<version>.zip`, which players can share and install with
  *Army Painter → Import scheme pack…*. Imported packs go to
  `BepInEx/config/warpstorm/schemes/<id>/`, and they override built-in packs.

Pack contents: `scheme.json` + `portraits/<sprite>.png`, which are the curated unit
portraits. Each file is named after the in-game portrait sprite.

## scheme.json

```jsonc
{
  "id": "salamanders", "name": "Salamanders", "version": "1.0.0", "author": "…",
  "description": "…",
  "faction": "Ultramarines",          // game Faction enum name this pack repaints
  "primary": "24572B", "secondary": "B08A4A",   // swatches shown in the configurator
  "rules": [                          // default recipe: 3D textures + portraits
    { "hue": 222, "width": 20, "feather": 10, "satMin": 0.22, "valMax": 0.97,
      "to": "24572B", "satScale": 0.95, "valScale": 0.85 }
  ],
  "textures":  { "ULT_INT_D": [ /* rules */ ] },          // optional 3D override per albedo
  "portraits": { "CaptainIcon": [ /* rules */ ] }         // optional portrait override
}
```

A rule moves pixels whose hue lies within `hue ± width`, softened by a further
`feather` (all in degrees), to the target colour `to`. Pixels below `satMin`
saturation or outside `valMin`–`valMax` brightness are left untouched. Saturation
and brightness are scaled by target ÷ source average, so the baked shading
survives. `satScale` / `valScale` darken or brighten the result. When several
rules match a pixel, the strongest one wins.

## Making or tuning a pack

```bash
dotnet build tools/SchemeBuilder -c Release
# review sheet: original vs scheme for every portrait (+ 3D albedos if exported)
dotnet tools/SchemeBuilder/bin/Release/net10.0/SchemeBuilder.dll \
  sheet schemes/<id> .copilot_workspace/scheme-review/<id>.png [--tex <albedo png dir>]
```

The source portraits are the game's Selection portraits, as published by
BattleSector Tools. They are downloaded once into
`.copilot_workspace/scheme-src/portraits/`. Text-on-white placeholder art is
skipped.
