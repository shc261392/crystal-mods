# Game update 1.8.0 — what changed and what was fixed

**Game:** Warhammer 40,000: Battlesector **1.8.0** (Unity 6000.0.62f1, Steam
build `26223780`, patched 2026-11-13).

All six distributables in this folder now target 1.8.0. The separate
`battlesector-tools` website was intentionally left unchanged.

## Why the 1.7.7 mods broke

1. **Data tables were split.** `UnitDataTable` and `WeaponDataTable` are now
   empty composites. The rows live in 12 `UnitFactionDataTable_*` /
   `WeaponFactionDataTable_*` tables, plus `SharedWeaponDataTable`, reached
   through the composite's `sources` array. Anything that read the old
   `keys` / `values` arrays saw **zero entries**.
2. **Fonts moved and changed.** The TMP fonts left `sharedassets0/1.assets` for
   `sharedassets2.assets`, were rebuilt as dynamic atlases, and the description
   font changed. Prebuilt 1.7.7 asset files no longer match the game.
3. **All seven Chinese text repositories changed**, so a stale text patch
   misses the new strings.
4. **New schema:** weapon `ShotsPerSwitch`, loadout `SmallSprite` and
   `MembersOverride`, and a third weapon targeting mode.
5. **New content:** 15 new unit rows — 10 Servants of Chaos units plus one
   Blood Angels, two Ultramarines and two Black Legion variants — and three
   weapons (Enraged Strikes, Plasma Rifle, Cyclic Ion Raker).
6. **Vortex marker changed:** `sharedassets1.assets` became a tiny stub, so it
   is no longer a reliable install marker.

A mod built against 1.7.7 and installed on 1.8.0 either ships the old bundle
(removing 1.8.0 content), ships asset files with incompatible serialization
(the game can fail to launch), or silently edits nothing.

## What was fixed, per mod

| Mod | Old → new | Fix |
|---|---|---|
| **TC Localization** | 0.2.3 → **0.3.0** | Full rebuild against pristine 1.8.0: text from the new Chinese repositories; `sharedassets2.assets` fonts baked; startup and mapbuilder bundles rebuilt; launcher strings regenerated; `TCFix` 1.3.0 retargeted to `NotoSansCJKjp-Regular SDF`. Legacy 1.7.7 deploy/uninstall scripts are disabled. |
| **The Great Crusade** | 0.1.1 → **0.1.2** | Builds on the live 1.8.0 bundle instead of the 1.7.7 `.vortex_backup`; declares 1.8.0; deterministic zips; `make build` builds both the standalone and TC-compatible variants. |
| **Warpstorm** | 1.1.0 → **1.2.0** | Plugin applies edits through the composite `Keys`/`Values` view (works on 1.7.x and 1.8.0); configurator follows `sources` into the per-faction tables; `ShotsPerSwitch` editable; Servants of Chaos preset; rebuilt against 1.8.0 interop. |
| **Red Laser Lasgun** | 1.1.1 → **1.2.0** | Rebuilt against the 1.8.0 BepInEx interop; declares 1.8.0. No behaviour change. |
| **BepInEx Framework** | 1.0.1 → **1.0.2** | Runtime unchanged; metadata now declares 1.8.0. Official build #785 SHA-256 still verified. |
| **Vortex extension** | 1.2.0 → **1.3.0** | Install detection now uses `resources.assets` instead of the stubbed `sharedassets1.assets`. |

## Verification performed

- Every release zip rebuilt **byte-identically** (TGC both variants, TC,
  Warpstorm, Red Laser, BepInEx).
- **TC:** all 7 repositories converted to Traditional; 2217 relevant
  codepoints; **0 missing** in the sharedassets2, startup and mapbuilder fonts
  (3754 / 4236 / 3754 glyphs); baked atlas is inline, so no `.resS` is needed;
  new 1.8.0 units are translated.
- **TGC:** both bundles are 1.8.0-based; cap 15, XP 100–1400, rarity curves and
  levelMul assertions pass; 55 cards applied; vanilla reference check passes.
- **Warpstorm:** headless selftest reads **205 units / 446 weapons from 12/13
  source tables**, detects game 1.8.0, and round-trips a config.
- **BepInEx:** official BepInEx artifact downloaded and SHA-256 verified; the
  repackaged zip is byte-identical to the released one.
- **Vortex extension:** 1.3.0 zip contains `info.json` 1.3.0 plus the updated
  `index.js`.

Not verified automatically: in-game rendering and gameplay. The TC
descriptions/modals, TGC card effects, Warpstorm paint/stat application, and
Red Laser visuals still need a manual launch. `cards.py` still carries a
"mirrored from 1.7.7" comment; the build and vanilla checks pass, but in-game
card-effect confirmation is the remaining proof.

## Install order

1. **BepInEx Framework 1.0.2**
2. **TC Localization 0.3.0** (optional)
3. **The Great Crusade 0.1.2** — standalone, or the TC-compatible file if TC is
   installed (do not enable both TGC files together)
4. **Warpstorm 1.2.0** and/or **Red Laser Lasgun 1.2.0** (plugins, no conflicts)

All are Vortex-installable; no scripted deployment is required.
