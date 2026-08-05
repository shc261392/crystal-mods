# BepInEx Framework

The **BepInEx 6 (IL2CPP) modding runtime** for Warhammer 40,000: Battlesector,
packaged as a one-click install. This is a **shared dependency** — install it
once, then install any BepInEx plugin mod for the game.

## Do I need this?

You need BepInEx Framework if you install a mod that says it requires BepInEx,
for example:

- **Traditional Chinese Localization** (its font-fix plugin)
- **Red Laser Lasgun**

If you only use pure asset mods, you do not need it.

## What it does

It installs the official **BepInEx Bleeding-Edge build #785** (win-x64) plus the
UnityDoorstop loader. This runtime loads plugin mods when the game starts. It
does **not** change any game file — it only adds loader files at the game root,
and BepInEx creates its own working folders on first launch.

## Install

1. Install this mod (Vortex recommended), then launch the game once so BepInEx
   finishes setting up.
2. Install your BepInEx plugin mod(s).

## Security & provenance

This package contains the **official, unmodified** BepInEx runtime:

- Build: **BepInEx Bleeding Edge #785** (`6.0.0-be.785+6abdba4`)
- Official download:
  `https://builds.bepinex.dev/projects/bepinex_be/785/BepInEx-Unity.IL2CPP-win-x64-6.0.0-be.785+6abdba4.zip`
- Official artifact **SHA-256**:
  `2a7cbf74d26abe4765c3e662db1721b923bac39849ebfef2ca5dc7de7e2d9b7f`

If you have any security concern, you can **download BepInEx yourself from the
official BepInEx website / builds server above**, verify the SHA-256, and install
it instead of this repackage — the plugin mods work with any equivalent BepInEx 6
IL2CPP installation.

## Compatibility

- Works alongside all Battlesector mods; it only adds the runtime.
- Windows and Linux/Proton (Proton needs the usual doorstop launch option).

## Disclaimer

BepInEx is created and distributed by the BepInEx project under its own license;
this page only repackages the official build for convenient install. Not
affiliated with or endorsed by Black Lab Games or Games Workshop.
