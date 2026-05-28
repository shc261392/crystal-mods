# Unreal Engine modding (stub)

> Status: **stub**.

## References

- UE4SS — <https://docs.ue4ss.com/>
- UE4SS repo — <https://github.com/UE4SS-RE/RE-UE4SS>
- FModel (asset browser) — <https://fmodel.app/>
- CUE4Parse — <https://github.com/FabRik/CUE4Parse>
- umodel (legacy) — <https://www.gildor.org/en/projects/umodel>
- repak (pak read/write) — <https://github.com/trumank/repak>
- UAssetGUI — <https://github.com/atenfyr/UAssetGUI>
- Unreal Modding Tools — <https://github.com/AstroTechies/unrealmodding>

## Quick decision tree

1. **Is it UE4 or UE5?** Check `<Game>/Binaries/Win64/<Game>-Shipping.exe`
   version info, or `<Game>/Content/Paks/global.utoc` (UE5 IoStore).
2. **IoStore enabled?** Presence of `.utoc` / `.ucas` next to `.pak`.
3. **Mod loader available?**
   - Blueprint / script mods → **UE4SS** (Lua + C++ + dumper).
   - Asset replacement → loose `.pak` in `<Game>/Content/Paks/~mods/`
     (load order via `~`/`zz_` prefixes).

## .pak workflow

- Extract: `repak unpack mod.pak`.
- Edit `.uasset` with UAssetGUI or repack from a Content/ tree.
- Repack: `repak pack mod_p/` → `mod_p.pak` (the `_p` suffix is required
  to mark it as a patch pak that overrides base files).
- Drop into `<Game>/Content/Paks/~mods/`.

## UE4SS plugin skeleton (Lua)

```
ue4ss/Mods/CrystalExample/
├── enabled.txt
├── Scripts/
│   └── main.lua
```

```lua
-- main.lua
local hook = RegisterHook("/Script/Engine.PlayerController:ClientRestart", function(self)
  print("[Crystal] PlayerController:ClientRestart fired")
end)
```

## TODO

- C++ UE4SS plugin (mod-loader SDK build).
- UE5 IoStore pak quirks (`oodle`, partial .utoc).
- Save-game format docs (GVAS) + edit examples.
- Mutator / blueprint asset import flow.
