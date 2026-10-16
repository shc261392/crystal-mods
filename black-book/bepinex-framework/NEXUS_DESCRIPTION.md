# BepInEx Framework

The **BepInEx 5.4.23.5 (x64) modding runtime** for **Black Book**, packaged as a
one-click install. This is a **shared dependency** — install it once, then
install any BepInEx plugin mod for the game.

## Do I need this?

You need BepInEx Framework if you install a mod that says it requires BepInEx,
for example:

- **Traditional Chinese Localization** (its `BlackBookTcFont` plugin)

If you only use mods that replace game files, you do not need it.

## Which BepInEx version?

**BepInEx 5 (x64)**. Black Book is a **Unity 2018.4 Mono** game, so BepInEx 5 is
required; BepInEx 6 (IL2CPP) will not work. This package ships the official
BepInEx **5.4.23.5** `win_x64` release.

## What it does

It installs the official BepInEx 5.4.23.5 `win_x64` release plus the
UnityDoorstop loader. This runtime loads plugin mods when the game starts. It
does **not** change any game file — it only adds loader files at the game root
(`winhttp.dll`, `doorstop_config.ini`, `.doorstop_version`, `BepInEx/core/`),
and BepInEx creates its own working folders on first launch.

## Install

1. Install this mod (Vortex recommended), then launch the game once so BepInEx
   finishes setting up.
2. Install your BepInEx plugin mod(s).

## Security & provenance

This package contains the **official, unmodified** BepInEx runtime:

- Version: **BepInEx 5.4.23.5** (`win_x64`)
- Official download:
  `https://github.com/BepInEx/BepInEx/releases/download/v5.4.23.5/BepInEx_win_x64_5.4.23.5.zip`
- Official artifact **SHA-256**:
  `82f9878551030f54657792c0740d9d51a09500eeae1fba21106b0c441e6732c4`

If you have any security concern, you can **download BepInEx yourself from the
official BepInEx GitHub releases above**, verify the SHA-256, and install it
instead of this repackage — the plugin mods work with any equivalent BepInEx 5
x64 installation.

## License & credits

BepInEx is created and distributed by the **BepInEx contributors** under the
**LGPL-2.1** license. This page only repackages the official build for
convenient install; the runtime is not our work. Not affiliated with or endorsed
by Morteshka or HypeTrain Digital.

## Compatibility

- Works alongside all Black Book mods; it only adds the runtime.
- Windows. Black Book's Steam build is Windows-only; under Linux/Proton the
  usual BepInEx/doorstop launch setup applies.
