# Red Laser Lasgun

A BepInEx 6 (IL2CPP) runtime plugin that renders the **Astra Militarum lasgun as
a glowing red laser beam** (muzzle → target) in Warhammer 40,000: Battlesector,
with **zero side effects** on other weapons.

## Requires

- **BepInEx Framework** mod (the BepInEx 6 IL2CPP runtime). Install it first.

## What it does

- On every lasgun shot, draws a per-shot **additive, camera-facing beam** — a
  bright core plus a wider dim glow halo — from the muzzle to the target.
- Uses its **own** material/colours (built at runtime from a shader that is always
  present in the shipped game), so **no shared game asset is modified** and no
  other weapon is affected.
- Hides the original flying bolt so only the beam shows (`HideBolt`, on by default).
- Affects **all AM las weapons** (Lasgun, Hot-Shot, Las Pistol, Multilaser,
  Lascannon) — every effect whose name contains `LasGun`.

## Install

1. Install the **BepInEx Framework** mod and launch the game once.
2. Install **Red Laser Lasgun** (Vortex recommended) and deploy.

## Configuration

Edit `BepInEx/config/com.crystalmods.redlaserlasgun.cfg` (created on first run),
then relaunch:

| Key | Default | Meaning |
|---|---|---|
| `Width` | 0.35 | Bright core width (world units). |
| `GlowWidthMul` | 3.5 | Glow-halo width as a multiple of the core. |
| `Duration` | 0.13 | Seconds the beam stays before fading. |
| `HideBolt` | true | Hide the original flying bolt. |
| `R` / `G` / `B` | 1 / 0.1 / 0.1 | Beam colour. |
| `Glow` | 3.0 | Intensity multiplier (additive brightness / bloom). |

## Compatibility

Runtime plugin (ships only `BepInEx/plugins/RedLaserLasgun.dll`) — no asset
bundle, so no file conflicts:

- **BepInEx Framework** — required.
- **The Great Crusade** — compatible (that mod edits a data bundle).
- **Traditional Chinese Localization** — compatible (coexists with `TCFix.dll`).
- **Lasgun Recolored** — compatible; with `HideBolt=true` the recoloured bolt is
  hidden, set `HideBolt=false` to keep both.

## Build

```bash
./package.sh        # dotnet build -c Release + zip -> ../../dist/red-laser-lasgun-v1.1.0.zip
```

Requires the .NET SDK and the game's `BepInEx/interop` assemblies (present after
BepInEx has run once).

## Disclaimer

Fan-made, single-player, cosmetic. Not affiliated with or endorsed by Black Lab
Games or Games Workshop.
