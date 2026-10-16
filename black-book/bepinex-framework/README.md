# BepInEx Framework (Black Book)

The **BepInEx 5.4.23.5 (x64)** modding runtime for **Black Book** (Steam App ID
`1138660`), packaged as an installable mod. It is a **shared dependency**:
install it once, then install any BepInEx *plugin* mod for this game.

Plugin mods that require it:

- **Traditional Chinese Localization** — its `BlackBookTcFont.dll` font/OpenCC
  plugin (shipped inside the localization zip under `BepInEx/plugins/`).

## Why BepInEx 5 and not 6

Black Book runs on **Unity 2018.4.31f1** with the **Mono** scripting backend
(x64), not IL2CPP. Mono Unity games use **BepInEx 5**; BepInEx 6 IL2CPP would
not load. This package is therefore the BepInEx 5 `win_x64` release.

## What it is

The official **BepInEx 5.4.23.5** `win_x64` release plus the **UnityDoorstop**
loader. It adds a runtime that loads plugins at game start. It does **not**
modify any game asset or executable — it only adds loader files at the game
root; BepInEx generates its own `BepInEx/config/`, `BepInEx/plugins/` and
`LogOutput.log` on first run.

Deployed files (game root):

```
winhttp.dll            UnityDoorstop proxy (loads BepInEx at startup)
doorstop_config.ini    doorstop configuration
.doorstop_version
BepInEx/core/          BepInEx 5 runtime (preloader, Harmony, Mono.Cecil, …)
changelog.txt          upstream changelog (informational)
```

The upstream archive contains no `BepInEx/plugins/` folder; BepInEx creates it
on first launch, and the localization mod deploys its plugin into it.

## Install

1. Install **BepInEx Framework** with Vortex (or extract the zip into the game
   root). Launch the game once so BepInEx generates its working folders.
2. Install any BepInEx plugin mod (e.g. Traditional Chinese Localization).

> Install order: **BepInEx Framework first**, then the localization mod. Vortex
> deploys files by path, so the order does not change the result, but launching
> the game once after the framework is installed ensures `BepInEx/plugins/`
> exists before the plugin is dropped in.

## Build / package

```bash
./package.sh        # -> ../dist/bepinex-framework-v1.0.0.zip
```

Windows PowerShell:

```powershell
.\package.ps1       # same recipe, same output
```

`package.sh` reuses an already-downloaded copy of the upstream archive if one is
present in `dist/`, otherwise it downloads the official BepInEx build and
verifies its SHA-256 before packaging. The binaries are **not** committed to the
repo (only the packaging scripts are).

## Provenance & integrity

- Upstream: **BepInEx 5.4.23.5** (`win_x64`).
- Official artifact:
  `https://github.com/BepInEx/BepInEx/releases/download/v5.4.23.5/BepInEx_win_x64_5.4.23.5.zip`
- Official artifact SHA-256:
  `82f9878551030f54657792c0740d9d51a09500eeae1fba21106b0c441e6732c4`

The same URL and SHA-256 are pinned in `tc-localization/build_plugin.sh` (which
uses the archive's reference assemblies to compile the plugin). If you prefer,
download BepInEx yourself from the official release above and install it instead
of this repackage — the plugin mods work with any equivalent BepInEx 5 x64
install.

## License

BepInEx is distributed under the **LGPL-2.1** license by the **BepInEx
contributors** (BepInEx/BepInEx). This package only repackages the official,
unmodified release for convenient install; the runtime is **not** our work and
is not relicensed. See the BepInEx project for the full license text.

## Notes

- Windows. Black Book's Steam build is Windows-only; Linux users run it through
  Proton, where the usual BepInEx/doorstop launch setup applies.
- Not affiliated with Morteshka or HypeTrain Digital.
