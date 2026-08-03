# The Great Crusade

Gameplay tuning for the **Crusade / Planetary Supremacy** (Warzone) roguelite in
Warhammer 40,000: Battlesector. One tuned config, in two builds.

> Data-only Unity asset edit (no code injection). All changes are inside
> `startup_assets_all.bundle`.

## What it changes

| Lever | Vanilla | This mod |
|---|---|---|
| **XP per level** (`expNeededToLevelUp`) | 200, 440, 720 … (widening) | **flat +100**: 100, 200, 300 … 1400 |
| **Max level** | 8 (7 upgrade picks) | **15** (14 upgrade picks) |
| **Top-tier card availability** (`CardDropProbabilities`) | Rare/Legendary only near max level | **Rare & Legendary available at every level** |
| **Upgrade-card effect values** (`statsModifiers`) | fixed | **hand-editable** via [`cards.json`](cards.json) |

Net effect: units level up quickly on a steady curve, keep levelling to 15 for
roughly twice the upgrade picks, and the top-tier ("gold") upgrade cards are
offered from the start — so fast levelling no longer traps you in the low card
pool.

### Why only these three levers?

Card rarity is keyed to *level ÷ max-level*, so raising the cap alone would push
top-tier cards further away; flattening the rarity curves compensates. Other
knobs were tested in-game and **do nothing** in 1.7.7 — the XP multiplier, the
upgrade-reroll cost, and all requisition/HQ-token/skip rewards are hardcoded or
driven by a separate economy table — so this mod deliberately leaves them alone.

### Card-pool safety

A unit can draw **15–16 Rare/Legendary cards** (11 Rare + 4–5 Legendary), and
level 15 gives **14 picks**, so the top-tier pool is never exhausted — no empty
level-ups.

## Editing card effects (`cards.json`)

The upgrade cards and their effect values live in two hand-editable files:
[`cards.json`](cards.json) (the **35 player** upgrade cards) and
[`cards-nonplayer.json`](cards-nonplayer.json) (the **20 enemy / cluster-modifier**
cards). **Every build reads both files** and bakes the values into the bundle, so
to change what a card does you just edit the numbers and rebuild — no code changes.

Each card has a stable `id`, a readable `name`, a `note` (an auto-generated
summary of its current effects), a `tier`
(`Common`/`Uncommon`/`Rare`/`Legendary`), a `costMultiplier` (extra unit
point-cost when the upgrade is taken: `0.1` = +10%, `-0.1` = -10%), the `roles`
it can be offered to, and a list of `effects`. The top of each file has a
`_fields` legend, a `_tiers` table, and a `_statTypes` table mapping every stat
name to its id. Per effect:

| Field | Meaning |
|---|---|
| `stat` | Which stat changes (see the `_statTypes` legend). Retype to change the stat. |
| `multiplier` | Percentage change applied first. `0.2` = +20%, `-0.5` = -50%, `0` = none. |
| `addSubtract` | Flat amount added after the multiplier. `5` = +5. |
| `chance` | 0–100 % chance the effect triggers. `0` = always. |
| `intValue` | Integer parameter used by a few stat types (leave as-is if unsure). |

`id`, `name`, `note`, `tier`, `roles` and the `_`-prefixed legend keys are
informational — only `costMultiplier`, `stat`, `multiplier`, `addSubtract`,
`chance`, `intValue` are applied. Effects are matched by position, so **don't add
or remove entries in a card's `effects` list** (a build will refuse a mismatch);
edit the values in place.

```bash
make export-cards            # regenerate both card files (won't clobber)
make export-cards FORCE=1    # overwrite both with vanilla defaults
```

### Vanilla reference (`cards-vanilla.json`)

[`cards-vanilla.json`](cards-vanilla.json) is a **frozen, read-only** snapshot of
all 55 cards' unmodified values (regenerated from a pristine 1.7.7 bundle by
`make export-cards`). It's **not applied** at build time — it's there so you can
diff your edits against vanilla or reset a value. Every standalone build also
checks the base bundle against it and **warns if the base isn't pristine vanilla**,
so edits are always calibrated to true unmodded values.

### Unit-cost policy (`make cost-policy`)

`make cost-policy` rewrites every card's `costMultiplier` to
**vanilla cost − a per-tier reduction**, making upgrades cheaper (higher tiers
cheaper):

| Tier | Reduction |
|---|---|
| Common | −0.10 (−10%) |
| Uncommon | −0.15 |
| Rare | −0.20 |
| Legendary | −0.25 |

The reduction is applied against the vanilla value in `cards-vanilla.json` (so
it's idempotent), and the per-tier amounts live in `TIER_COST_DELTA` in
[`cards.py`](cards.py). Re-run after `make export-cards` to re-apply the policy.

> Card **effect values** are structurally editable; confirm in-game that a given
> stat displays/behaves as expected before relying on it.

## Builds

- **`the-great-crusade-v0.1.0.zip`** (standalone) — built on the vanilla bundle.
- **`the-great-crusade-tccompat-v0.1.0.zip`** — built on the Traditional Chinese
  Localization bundle, so it keeps TC fonts. See "Using with TC localization".

## Using with TC localization

- **The TC mod is still required.** The `-tccompat` build only replaces
  `startup_assets_all.bundle` (with TC fonts *and* the crusade edits baked in).
  Full localization also needs the TC mod's other files (`resources.assets`,
  `sharedassets0/1.assets`, `stringsChinese.resx`, `TCFix.dll`, the mapbuilder
  bundle). Install **both**.
- **Vortex will report a file conflict** on `startup_assets_all.bundle`. Resolve
  it so **The Great Crusade loads *after* (wins over) the TC mod**.
- Do **not** pair the **standalone** build with the TC mod (its bundle lacks the
  TC fonts).

## Compatibility & limitations

- **Crusade / Planetary Supremacy only.** The narrative campaign and skirmish are
  unaffected.
- **Compatible with Lasgun Recolored.** That mod's default build ships only
  `faction-astramilitarum_assets_all.bundle`, a different file, so there's no
  conflict. (Its optional `--stats` build also replaces `startup_assets_all.bundle`
  and would conflict — don't use that variant alongside this mod.)
- **Traditional Chinese Localization** replaces `startup_assets_all.bundle` too —
  use the `-tccompat` build and let it win that conflict (see above).
- **Only one startup-bundle mod at a time.** This replaces
  `startup_assets_all.bundle`; it cannot coexist with another mod that also
  replaces that file except via the `-tccompat` build above.
- **Not multiplayer-safe.** Disable for multiplayer.

## Build

Leveling/rarity parameters are code in [`build.py`](build.py) (`LEVEL_CAP`,
`STEP`, `TOP_TIER_RARITIES`, `RARITY_FULL_FROM`); card effect values are data in
[`cards.json`](cards.json) (see "Editing card effects"); the [`Makefile`](Makefile)
selects the base. Every build applies both.

```bash
make all PYTHON=/path/to/python-with-unitypy     # both ZIPs
make standalone
make tccompat
make export-cards                                # regenerate cards.json defaults
```

### Build inputs

- **Vanilla base** — a pristine `startup_assets_all.bundle`; point
  `BS_VANILLA_BUNDLE` at it (default: the game folder's Vortex `.vortex_backup`).
  Canonical clean source is **Steam → Verify integrity of game files**.
- **TC-compat base** — the TC localization mod's dist bundle at
  `../tc-localization/translation/zh-TW/dist/startup_assets_all.bundle`.

Requires Python with [UnityPy](https://github.com/K0lb3/UnityPy).

## Install

Install one ZIP with Vortex (via the Battlesector extension) or copy
`Warhammer 40K Battlesector_Data/StreamingAssets/startup_assets_all.bundle` into
your game folder (back up the original first). `deploy.sh` / `deploy.ps1` install
manually; `uninstall.sh` / `uninstall.ps1` restore the backup.
