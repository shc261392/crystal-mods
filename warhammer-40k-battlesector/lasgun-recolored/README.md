# Lasgun Recolored

A **visual / FX mod** for **Warhammer 40,000: Battlesector** (1.7.4, Unity 6 /
IL2CPP) that recolours the Astra Militarum Lasgun to match the appearance of
Lasguns from the **Dawn of War** and **Space Marine** series. Provides an
alternative to the vanilla yellow/orange colour.

## About this mod

There is no single canon colour for Lasguns or Lascannons across all Warhammer
40,000 media — they vary significantly between the tabletop game, video games
(Dawn of War, Space Marine, Battlesector), and other depictions. This mod
provides an alternative aesthetic based on the laser weapons seen in Relic's
Dawn of War and Saber Interactive's Space Marine series.

## What it does

Recolours the firing FX of the standard **Lasgun** (weapon id `7010`) carried by
**Cadian Shock Troops / Guardsmen**:

| Change | Vanilla | Modded |
|------|--------:|-------:|
| Projectile / muzzle / trail colour | warm yellow/orange | **red (DoW/Space Marine style)** |

The recolour uses a deep red (`1, 0, 0.10`) with the HDR brightness **capped**
so the game's ACES tonemapping + bloom don't wash it back to orange. It covers
the bolt's point-light glow, `TrailRenderer` gradient, ParticleSystem start +
colour-over-lifetime gradients, and the four lasgun FX materials (`LasGunTrail`,
`LasGun_MuzzleFlashBurst`, `LasGun_MuzzleFlashFlare`,
`disperse_explosion_lasgun`). 

**Note**: these FX are **shared across other Astra Militarum las weapons**
(laspistol, multilaser, lascannon variants), so their bolts/muzzle flashes also
turn red. This is intentional to maintain a cohesive visual style. Not yet
verified in-game — please test.

## Optional: also change the Lasgun's stats

The stat boost is **off by default** (this mod ships colour/FX only). To also
apply it, edit `STAT_PATCH` in [build.py](build.py) and rebuild with `--stats`:

```python
# build.py
STAT_PATCH = {"Attacks": 50, "Damage": 8.0, "ArmourPenetration": 2}
#   Attacks = shots per attack   (vanilla 4)
#   Damage  = base damage/bolt    (vanilla 4)
#   ArmourPenetration = armour ignored (vanilla 1)
```

```bash
python build.py \
  --am-faction "$SA/faction-astramilitarum_assets_all.bundle" \
  --stats --startup "$SA/startup_assets_all.bundle"
bash package.sh
```

With `--stats`, a second bundle (`startup_assets_all.bundle`, holding
`WeaponDataTable`) is patched and added to the payload/zip. To revert to
vanilla stats, simply rebuild **without** `--stats`.

## Files patched

Unity asset bundles under `Warhammer 40K Battlesector_Data/StreamingAssets/`:

- `faction-astramilitarum_assets_all.bundle` — projectile/FX (`FX_WPN_AM_LasGunProjectile`,
  `FX_WPN_LasGunMuzzleFlash`). ~475 MB. **Always** patched (the colour/FX change).
- `startup_assets_all.bundle` — `WeaponDataTable`. **Only** patched with `--stats`.

## Tuning the red (if it still looks orange)

Battlesector uses ACES tonemapping + bloom, which shifts very **bright** reds
toward orange. The recolour therefore uses a *capped, deep* red by default. If
it still reads orange, lower the brightness cap and/or push the hue further from
orange — no code editing needed:

```bash
# Darker, more saturated red (lower cap):
python build.py --am-faction "$SA/faction-astramilitarum_assets_all.bundle" \
  --emission-cap 0.7

# Push hue toward crimson to counter the orange shift harder:
python build.py --am-faction "$SA/faction-astramilitarum_assets_all.bundle" \
  --red "1,0,0.25" --emission-cap 0.6
```

- `--emission-cap` clamps material colour/emission brightness (default `1.2`).
  Lower = deeper, less bloom-washed red.
- `--red R,G,B` sets the hue (default `1,0,0.10`). Keep green at `0`; a little
  blue counters the ACES orange shift.

Re-run `bash package.sh` after each build to refresh the zip.

## Building the payload from your own game files

This repo does **not** ship the patched bundles (they are large and derived from
copyrighted game data). You build them locally from your installed game:

```bash
pip install UnityPy
SA="/path/to/Warhammer 40000 Battlesector/Warhammer 40K Battlesector_Data/StreamingAssets"

# Colour / FX only (default, shipped build):
python build.py --am-faction "$SA/faction-astramilitarum_assets_all.bundle"

# Colour / FX + optional stat boost:
python build.py \
  --am-faction "$SA/faction-astramilitarum_assets_all.bundle" \
  --stats --startup "$SA/startup_assets_all.bundle"
```

`build.py` only **reads** your game bundles and writes patched copies into
`./payload/Warhammer 40K Battlesector_Data/StreamingAssets/`. It never writes to
your game directory.

## Installing

### Via Vortex (recommended)
1. Build the payload (above).
2. Zip it: `bash package.sh` → produces `dist/lasgun-recolored-v<ver>.zip`.
3. Drag the zip into Vortex (the repo's Battlesector extension deploys the
   bundles to the right paths). Vortex automatically backs up the originals as
   `*.vortex_backup` and restores them when you purge/remove the mod.

### Manual
- `bash deploy.sh` (Linux/WSL2) or `pwsh deploy.ps1` (Windows) copies the built
  payload into the detected game directory, backing up the originals first.
- **Deployment to the game directory is performed by you**, not by the build.

## Reverting

- **Vortex**: purge/remove the mod — originals are restored automatically.
- **Manual**: `bash uninstall.sh` / `pwsh uninstall.ps1` restores the timestamped
  backups created by the deploy scripts, or verify the game files via Steam.

## Notes / limitations

- Balance: 50 shots × 8 damage is intentionally extreme (sandbox/fun mod).
- Multiplayer: all players would need the same mod; use in singleplayer.
- Game updates that repackage the bundles will require rebuilding from the new
  vanilla files.
- Requires Battlesector **1.7.4**. Weapon id / path ids were verified against
  that build; other versions may differ.
