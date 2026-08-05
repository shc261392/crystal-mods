# BepInEx Framework (Battlesector)

The **BepInEx 6 (IL2CPP)** modding runtime for **Warhammer 40,000: Battlesector**,
packaged as an installable mod. It is a **shared dependency**: install it once,
then install any BepInEx *plugin* mod for this game.

Plugin mods that require it:

- **Traditional Chinese Localization** — its `TCFix` font-fix plugin.
- **Red Laser Lasgun** — the red laser-beam plugin.

## What it is

The official **BepInEx Bleeding-Edge build #785** (`6.0.0-be.785+6abdba4`,
win-x64) plus the **UnityDoorstop** loader. It adds a runtime that loads plugins
at game start. It does **not** modify any game asset or executable — it only adds
loader files at the game root; BepInEx generates its own `interop/`, `config/`,
`cache/` and `LogOutput.log` on first run.

Deployed files (game root):

```
winhttp.dll            UnityDoorstop proxy (loads BepInEx at startup)
doorstop_config.ini    target = BepInEx/core/BepInEx.Unity.IL2CPP.dll
.doorstop_version
BepInEx/core/          BepInEx runtime (preloader, IL2CPP loader, Harmony)
BepInEx/patchers/
dotnet/                bundled .NET (CoreCLR) runtime for IL2CPP
```

## Install

1. Install **BepInEx Framework** with Vortex (or extract the zip into the game
   root). Launch the game once so BepInEx generates its `interop/` folder.
2. Install any BepInEx plugin mod (TC Localization, Red Laser Lasgun, …).

## Build / package

```bash
./package.sh        # -> ../dist/bepinex-framework-v1.0.0.zip
```

`package.sh` reuses the already-built framework binaries if present, otherwise it
downloads the official BepInEx build and verifies its SHA-256 before packaging.
The binaries are **not** committed to the repo (only this packaging script is).

## Provenance & integrity

- Upstream: BepInEx Bleeding Edge build **785** (commit `6abdba4`).
- Official artifact:
  `https://builds.bepinex.dev/projects/bepinex_be/785/BepInEx-Unity.IL2CPP-win-x64-6.0.0-be.785+6abdba4.zip`
- Official artifact SHA-256:
  `2a7cbf74d26abe4765c3e662db1721b923bac39849ebfef2ca5dc7de7e2d9b7f`

If you prefer, download BepInEx yourself from the official site above and install
it instead of this repackage — the plugin mods work with any equivalent BepInEx 6
IL2CPP install.

## Notes

- Windows / Proton. On Linux/Proton, set the Steam launch option so the doorstop
  proxy is loaded (see BepInEx docs).
- Not affiliated with Black Lab Games or Games Workshop. BepInEx is distributed
  under its own license by the BepInEx project.
