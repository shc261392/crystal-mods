# Campaign garrison crash — Soulstorm Imperial Guard stronghold

## What this documents

The ×5 squad model scale breaks the **Soulstorm Imperial Guard stronghold**
(`stronghold_imperial_guard.scar`, DXP3): entering that mission (e.g. Ork vs
Imperial Guard) raises a **SCAR error at game start**. This documents the exact
edit responsible, the mechanism, and the per-map script fix shipped in **0.1.8**.

## Symptom

Starting the IG stronghold in the Soulstorm campaign errors out with a SCAR
error dialog at game start. It is **not** a load/parse error and not specific to
the resource cheat: it reproduces with the cheat variant, the
`-normal-resources` variant, and a chest-free build.

## Root cause (verified by isolation builds)

The trigger is scaling **`unit_min` (spawn size)** of the base
`guard_squad_guardsmen` (5 → 25). Everything else about the ×5 edit —
`unit_max` (9 → 45) and the per-model cost counter-scale — is exonerated.

| Variant | `unit_min` | `unit_max` | cost counter-scale | result |
|---|---|---|---|---|
| vanilla | 5 | 9 | — | — |
| full ×5 | 25 | 45 | ÷5 | **errors** |
| `unit_min` off | **5** | 45 | ÷5 | **clean** |
| costs off | 25 | 45 | vanilla | **errors** |
| costs only | **5** | **9** | ÷5 | (not needed) |

- `unit_min` off is clean **with** the cost counter-scale still applied → the
  cost change is **not sufficient** to cause the error.
- costs off **still errors** with `unit_min`/`unit_max` scaled → the cost change
  is **not necessary** either.
- Therefore scaling `unit_min` alone is both necessary and sufficient, and the
  cost counter-scale is irrelevant to this crash.

Other guard squads and other parts of the edit were cleared separately: caps,
the cheat scar, `guard_squad_command_squad`, idle vehicles, single-model
campaign variants, and the guard-only race split (ork-only is clean, guard-only
errors).

## Mechanism (verified by the fix)

`stronghold_imperial_guard.scar`'s `Rule_Garrision_Troops_In_Buildings()` spawns
the base guardsmen **at game start** with
`Util_CreateSquadsAtMarker(..., 1)` and then immediately calls
`Cmd_EnterBuilding(...)` on each squad.

In `scarutil.scar`, `Util_CreateSquadsAtMarker` passes `loadout = 0`, which means
**"min loadout"** — and the min loadout is the squad's `unit_min`. With the mod
that is **25 models**. The mission then garrisons those squads into
vanilla-sized HQ / Infantry-Command / Mechanized-Command buildings.

- The mission's later "produce" spawns already pass an explicit loadout
  (`Util_CreateSquadsAtMarkerEx(..., 1, 5)` and `(..., 1, 13)`) and were never
  affected — consistent with the spawn-size trigger.
- Scaling `unit_max` alone is fine because nothing at game start refers to
  `unit_max`.

**Verified:** the spawn size is the trigger, and forcing the garrison to a
vanilla loadout removes the error.

**Not instrumented (no claim):** the exact internal failure — i.e. *why* the
engine/mission objects to the oversized garrison. Patching the spawn size and
observing the error disappear is the only evidence; the internal reason was not
traced.

## The fix (0.1.8)

Squad `.rgd` data is **global** — one `guard_squad_guardsmen.rgd` is shared by
this mission, every other Soulstorm mission, and skirmish — so a data edit can
never be scoped to "this map only". The only place a per-map fix can live is the
mission script itself.

The generator (`scripts/generate_mod.py`) rewrites the **9** garrison calls in
that one file:

```lua
-- before (loadout 0 -> scaled unit_min = 25 models)
Util_CreateSquadsAtMarker(g_Player2, "...", "guard_squad_guardsmen", "...", 1)
-- after (explicit vanilla loadout 5)
Util_CreateSquadsAtMarkerEx(g_Player2, "...", "guard_squad_guardsmen", "...", 1, 5)
```

- Implemented by `CAMPAIGN_SCRIPT_FIXES` + `apply_campaign_script_fixes()`,
  default **on** (`--campaign-script-fix on`; turn off only for diagnostics that
  need to reproduce the bug).
- Shipped at `DXP3/Data/scenarios/sp/stronghold_imperial_guard.scar` in **both**
  release variants.
- `make build` applies it deterministically; `make verify` asserts it is present
  (11 `Ex` calls carrying guardsmen, 0 unpatched garrison calls).
- The generator **fails loudly** if the expected 9 sites are not found, so
  game-data drift cannot silently ship a partial fix.

## Verified evidence

- **Content diff:** the 0.1.8 zips equal the 0.1.7 zips **plus exactly this one
  file**; no other file was added, removed, or changed.
- **In-game:** with the patch the IG stronghold starts clean, with the rest of
  the world still on full ×5 scaling.
- **Determinism:** `make build` run twice yields byte-identical 0.1.8 zips.

## Scope / limitations

- Fixes **only** the Soulstorm (DXP3) IG stronghold. The Dark Crusade (DXP2)
  copy of the mission is separate and is **not** patched; if you hit the same
  error in the DC stronghold, the same patch approach applies there.
- Other campaign scripts also force-spawn base troop squads with loadout 0
  (e.g. W40k `ms04`/`ms05`, WXP `mso4`). Any mission that force-spawns a scaled
  base troop squad at min loadout could hit the same error. A global or
  race-scoped `unit_min` change would avoid all of them, but it would change
  spawn sizes **everywhere** (skirmish included) — which is why this fix is
  scoped to the mission script instead.
