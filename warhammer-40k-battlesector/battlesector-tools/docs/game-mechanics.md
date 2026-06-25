# Battlesector — Game Mechanics & Data Research

Authoritative notes on how Warhammer 40,000: Battlesector mechanics map to the
data we extract (`MonoBehaviour/*DataTable.asset`) and how the tools model them.
Keep this updated as research continues — it is the persistent record.

Source data: AssetRipper export at
`/mnt/d/mods/battlesector/ExportedProject/Assets`. Decompiled managed code:
`.copilot_workspace/battlesector-data/decompiled/Assembly-CSharp.decompiled.cs`
(method bodies are AssetRipper stubs — field/struct layout is reliable, logic is
not).

## Damage (verified earlier)

- `Damage` = the **maximum** of a damage range. Minimum = `0.75 × max`
  (`MinDamageMultiplier`). A hit rolls uniformly in `[0.75·max, max]`.
- **Critical chance** = base + `5%` per point of armour piercing above target
  armour. **Graze chance** = `3%` per point of target armour above piercing; a
  graze deals **no** damage. Critical damage multiplier is native/unextractable.

## Melee vs ranged classification (NEW — fixes the 0% accuracy bug)

`WeaponDataTable.asset` has **no** `IsMelee`/`IsRanged` fields, so the original
parser defaulted everything to ranged. Correct classification is by range:

- **Melee** = `MaximumRange ≤ 1.5` tiles (adjacent). 149 of 439 weapons.
- **Ranged** = `MaximumRange ≥ 2`. 290 of 439.

### Melee accuracy

Melee weapons do not have a meaningful ranged accuracy. Two sub-cases:

- 103 melee weapons have `Accuracy = 0` (e.g. Power Sword, Bayonet, Big Choppa).
  In game these hit using the **wielding unit's `MeleeAccuracy`** stat.
- 46 melee weapons carry their own `Accuracy` of 75–100 (e.g. Astartes
  Chainsword 85, Accursed Chainaxe 100, Power Fist). Some weapons appear under
  both forms (different ids / unit contexts).

**Rule used by the tools:** melee hit accuracy =
`weapon.accuracy > 0 ? weapon.accuracy : unit.MeleeAccuracy`.

This was the root cause of the calculator "remaining HP never drops" bug: a
melee weapon with `accuracy = 0` produced a 0% hit chance, so expected damage was
0. The calculator now substitutes the attacker's melee accuracy (fallback 85
when no attacker unit is selected). Unit pages show the wielder's melee accuracy
for such weapons; the weapon page labels them "Melee" instead of "0%".

Persisted in the pipeline: `prepare_website_data.py` derives
`isMelee = rangeMax ≤ 1.5`. (`reclassify_melee.py` patches an existing
`weapons.json` in place without a full re-extract.)

## Cover (implemented in calculator UI/logic)

The calculator now uses a segmented cover control and applies cover as an
accuracy penalty (not armour):

- **¼ cover** = `−15%` attacker accuracy
- **½ cover** = `−30%`
- **¾ cover** = `−45%`
- **Full cover** = attack blocked (`Cannot attack`, hit chance forced to 0)

Implementation notes:

- UI: segmented shield buttons (`CoverShield`) in `calculator.astro`
- Logic: `coverAccPenalty = [0, 15, 30, 45, 0][cover]`, `blocked = cover >= 4`
  in `calculator.ts`
- Verified live after deploy:
  `100% → 85% → 70% → 55% → Cannot attack`

## Splash / Area of Effect (RESEARCHED)

`WeaponData.ImpactType` (`WeaponImpactType` enum) defines how a hit lands:

- `Single` (0) — damages one model per hit. 278 weapons.
- `Tile` (1) — every hit damages **all** models in the target unit. Only
  `Detonate` (1 weapon).
- `Splash` (2) — damages a primary plus secondary models. 161 weapons.

`WeaponData.SplashDamageSettings` (only meaningful when `ImpactType == Splash`):

- `Models` — number of models hit **including** the primary (2 = primary + 1
  secondary; flamers/grenades reach 8–10).
- `DamageFalloff` — 0..1 fraction by which **secondary** targets' damage is
  reduced (0.4 → secondaries take 40% less).
- `HeavyAll` — if true, all models in the area are knocked down even if not hit.

Many melee weapons are Splash (cleave): Chainsword `Models 3`, Power Sword
`Models 2`. Surfaced as a "Splash ×N" chip on weapon/unit pages plus an Impact
row on the weapon page. The original parser's `AreaOfEffect`/`SplashDamage`
field names do **not** exist in the asset (returned 0); the real fields are
`ImpactType` + `SplashDamageSettings`.

## Post-kill targeting / wasted attacks (RESEARCHED)

`WeaponData.BallisticWeaponTargetType` governs what happens when a target model
dies mid-attack (the "wasted attacks" behaviour):

- `None` (0) — redistributes to living models. _(No weapon uses this; surfaced
  as "redistribute" for completeness.)_
- `FixedTargetPerMember` (1) — each attacking member locks one enemy member; if
  that member dies, the attacker **stops** (remaining shots wasted). 429 weapons
  — the default.
- `FixedTargetForEntireUnit` (2) — every member targets the same highest-health
  enemy member; if it dies, the **whole unit** stops. 13 weapons.

Overkill is generally wasted (FixedTargetPerMember); 13 weapons waste even more
(whole unit focus-fires one model). Surfaced as a "Post-kill targeting" row on
the weapon page. _(Not yet modelled in the calculator's expected-damage math —
the one-round calc still assumes overkill carries; documented as a known
simplification.)_

`WeaponData.Pistol` (bool) = ranged weapon usable in melee (46 weapons, e.g.
Bolt Pistol, gauntlets, hand flamers). Used to refine melee detection:
**melee = `rangeMax ≤ 1.5` AND not `Pistol`** (143 melee).

## Command / HQ abilities (research tab added)

Reliable command/HQ data extraction remains **partially constrained** by
asset-linking gaps, but we now have a verified browse dataset from extracted
text tables plus HQ-unit ability-id coverage:

- Verified command/HQ text rows surfaced (e.g. `Voice of Command`,
  `Command Protocol`, `Master of War`, and multiple HQ command flavour/desc
  entries)
- HQ unit ability-id sets are grouped per faction from `units.json`
  (exact IDs, no guessing)
- New tab: `/command-abilities`

Known limitation: ability IDs are not yet fully resolvable to a complete
name+icon+description graph for every faction command entry.

## HQ upgrades / tech tree (research tab added)

We confirmed and surfaced upgrade-card data from the warzone upgrade table:

- Source: `complete_stats/additional_tables/warzone_upgrades.json`
- 135 entries mapped from GUIDs to known asset names via extracted meta index
- Grouped tiers found in IDs/asset naming:
  - Base (`0–34`)
  - Uncommon (`100–134`)
  - Rare (`200–224`)
  - Legendary (`300–309`)
  - Enemy modifiers (`500–514`)
  - Zone modifiers (`600–614`)
- New tab: `/hq-upgrades`

Known limitation: this is card-level upgrade coverage; full prerequisite-edge
graph reconstruction (node-to-node dependency chains) is not yet finalized.
