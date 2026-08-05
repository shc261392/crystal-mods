# The Great Crusade

Gameplay tuning for the **Crusade / Planetary Supremacy** roguelite in Warhammer
40,000: Battlesector.

## What it does

- **Fast, steady leveling** — every level costs a flat 100 XP more (100, 200,
  300 …), so units rank up quickly and evenly.
- **Level cap raised to 15** — roughly twice the upgrade picks per unit (14 vs 7).
- **Guaranteed top-tier cards at the upper levels** — Rare and Legendary ("gold")
  upgrade cards are guaranteed once a unit reaches the upper levels (~level 8 of
  15 and above). The early levels (roughly 1–7) keep close to the vanilla rarity
  mix, so the payoff is climbing the ranks rather than an instant flood of gold.
- **Cheaper upgrades** — in Crusade mode, taking an upgrade card normally raises a
  unit's point cost. This mod trims that cost for **every** card, scaled by tier —
  Common −10, Uncommon −15, Rare −20 and Legendary −25 percentage points off the
  vanilla cost (rarer cards get a bigger discount). Units stay cheaper as they
  upgrade, so a fully-upgraded veteran costs far less to field than in vanilla.

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
- Once you reach the top-tier levels, a unit has 15–16 top-tier cards to draw from
  vs 14 picks at level 15, so the good-card pool is never exhausted.

## Disclaimer

Fan-made single-player asset edit. Not affiliated with or endorsed by Black Lab
Games or Games Workshop. Keep a backup of your saves and use at your own risk.
