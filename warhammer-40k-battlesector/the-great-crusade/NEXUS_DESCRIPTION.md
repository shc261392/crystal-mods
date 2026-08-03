# The Great Crusade

Gameplay tuning for the **Crusade / Planetary Supremacy** roguelite in Warhammer
40,000: Battlesector.

## What it does

- **Fast, steady leveling** — every level costs a flat 100 XP more (100, 200,
  300 …), so units rank up quickly and evenly.
- **Level cap raised to 15** — roughly twice the upgrade picks per unit (14 vs 7).
- **Top-tier cards at every level** — Rare and Legendary ("gold") upgrade cards
  are offered from the very first level-up, so rushing levels no longer traps you
  in the low card pool.

Purely a data edit to the game's asset bundle — no code injection.

## Builds

- **Standalone** — for a normal (English) game.
- **TC-compatible** (`-tccompat`) — for players who also use the **Traditional
  Chinese Localization** mod. Install it **alongside** the TC mod (the TC mod is
  still required for full localization) and, in Vortex, set The Great Crusade to
  **win** the `startup_assets_all.bundle` conflict. This keeps the Chinese fonts
  and adds the crusade edits. Do not pair a *standalone* build with the TC mod.

## Requirements

- Warhammer 40,000: Battlesector **1.7.7**.
- No other mod that replaces `startup_assets_all.bundle` (except the TC setup above).

## Install

1. Download one build.
2. Install with Vortex (recommended) or drop the included
   `Warhammer 40K Battlesector_Data/StreamingAssets/startup_assets_all.bundle`
   into your game folder (back up the original first).
3. Start a Crusade / Planetary Supremacy run.

## Notes

- **Crusade / Planetary Supremacy only** — the campaign and skirmish are unaffected.
- **Not for multiplayer.** Disable it before playing multiplayer.
- A unit has 15–16 top-tier cards vs 14 picks at level 15, so the good-card pool
  is never exhausted.

## Disclaimer

Fan-made single-player asset edit. Not affiliated with or endorsed by Black Lab
Games or Games Workshop. Keep a backup of your saves and use at your own risk.
