# Handover — Haemonculus Honor Guard crash (over-40000 v0.4.0)

> Paste the "Next-session prompt" block at the end of this file into your next
> session to resume with full context.

## Status — RESOLVED & RELEASED as 0.1.6

- **ROOT CAUSE CONFIRMED (in-game, 2x2 isolation + failed guard test).** The
  `Over40000_BoostWeaponCaps` (WC) block in `setup.scar` was **both necessary
  and sufficient** for the crash, and **the nil/0 guard did NOT fix it** (variant
  G crashed in-game).
- **FIX SHIPPED:** the WC block is **removed entirely**.
- **RELEASED as 0.1.6** in **two variants** (both: squad scale x5, can-attach
  `scale`, EBP cost counter-scale, no WC block, single-model campaign variants
  descaled, cheat waits for opening NIS to finish, Dark Eldar Talos blacklisted,
  63 squads' cost counter-scale fixed, attachable leaders Priest/Commissar/Psyker
  blacklisted):
  - `dist/over-40000-v0.1.6.zip` — resource cheat on (start 40001 req/power,
    ×10 income)
  - `dist/over-40000-v0.1.6-normal-resources.zip` — normal resources
- All diagnostic test builds (A–G, experimental, recommended, bisect/dataab)
  were **deleted** from `dist/`. Generator defaults `--weapon-cap-boost off` and
  ships vanilla `setup.scar` when `--resource-cheat off`. The talos exclusion is
  a git-controlled blacklist (`scripts/templates/squads.blacklist.txt`) applied
  by default; `--blacklist-file` overrides it.
- The user's in-game confirmation of the final 0.1.6 build is the last open item
  (expected to pass — the WC block was the sole crash source; the DC/SS
  mission-start freeze from single-model honor-guard squads is fixed by
  `--descale-campaign-single`; the opening-cinematic cheat timing is fixed by
  polling `Event_IsAnyRunning()` instead of a fixed 1s one-shot; the DE crash
  from a scaled Talos is fixed by the blacklist).

## The confirmed root cause

### In-game results that isolate it

| variant | squad scale | can-attach | WC boost | Haemonculus HG | result |
|---|---|---|---|---|---|
| A-noscale | off | — | off | absent (vanilla) | **no crash** |
| B-skip-canattach | x5 | all 131 excluded | on | absent (vanilla) | **crash** |
| C-skip-hg-attach | x5 | `_hg*` excluded | on | absent (vanilla) | **crash** |
| D-attach-2x | x5 / can-attach x2 | at x2 | on | 2/2 | **crash** |
| E-nowc | x5 | skip (like B) | **off** | absent | **no crash** |
| F-wc-only | off | — | **on** | absent | **crash** |

B↔E differs **only** in the WC block (byte-verified). A↔F differs **only** in
the WC block. So:

- E no-crash + B crash ⇒ **WC block is necessary**.
- F crash + A no-crash ⇒ **WC block is sufficient by itself** (squad scaling
  and EBP cost division are NOT involved at all).
- **G (nil/0-guarded WC block) crashed in-game** ⇒ the guard did not fix it.
  Whatever the precise fault is inside the block (nil `* 4` is the prime
  suspect), the block must be **removed, not guarded**.

### The mechanism (data-confirmed, not guessed)

The WC block runs every 5 s (`Rule_AddInterval( Over40000_BoostWeaponCaps, 5 )`),
matching the reported 3–6 s crash window. For each owned squad it does:

```
local base = Squad_GetUpgradeMax( squadID )   -- reads squad_reinforce_ext.max_upgrades
local modifier = Modifier_Create( ..., base * 4, ... )
```

`max_upgrades` lives in `squad_reinforce_ext`. **432 of 866 squad files have no
`squad_reinforce_ext` at all** (the Haemonculus HG is one of them), so
`Squad_GetUpgradeMax` returns **nil** and `nil * 4` throws a Lua arithmetic
error that crashes the game on the next 5 s tick. The Haemonculus HG was just
the first such squad the tester built; **any** of the 432 would crash.

Data points from the scan (`.copilot_workspace/scan_reinforce.py`):
tactical=2.0, scourge=4.0, incubus HG=0.0 (ext present, base 0 → also skipped
by the guard), Haemonculus HG=**no ext at all (nil)**.

### What was refuted (do not revisit)

- `squad_can_attach_ext` scaling 1→5: B/C crash with the HG file absent/vanilla
  and D crashes with HG at 2/2 — the HG's own scaling is irrelevant.
- Squad scaling / EBP cost division: F (scale off, WC on) crashes — scaling is
  not even required.
- Race caps: byte-identical across variants — not a differentiator.

## The fix (SHIPPED): remove the WC block entirely

The guard approach (variant G) was tested in-game and **still crashed**. The
release therefore **drops the entire WC block**:

```
dist/over-40000-v0.1.0.zip                    (resource cheat on)
dist/over-40000-v0.1.0-normal-resources.zip   (normal resources)
```

- Config (both): squad scale **x5**, can-attach `scale` (full feature set),
  EBP per-model cost counter-scale — **WC block absent** from `setup.scar`.
- `scripts/generate_mod.py` defaults `--weapon-cap-boost` to **off** and
  supports `--resource-cheat {on,off}` (off ships vanilla `setup.scar`).
- Verified: WC references zero in both setup.scar files; the no-cheat
  `setup.scar` is byte-identical to the vanilla extract file; both variants
  differ only in `setup.scar` (+ README/NEXUS_DESCRIPTION).
- `NEXUS_DESCRIPTION.md` written (fun-mod framing, Sentinel 5-model squad
  example, two-variant install instructions).
- **Awaiting the human's in-game confirmation** that the 0.1.0 builds play
  crash-free with the Haemonculus HG.

## What was built

### Generator (`scripts/generate_mod.py`)

- `--can-attach-policy {scale,skip,skip-hg,scale2}`.
- `--weapon-cap-boost {auto,on,off}` (default **off**: the WC block crashed the
  game and was dropped from the recommended build; `auto` = on when scale>0).
- `--setup-template PATH` — alternate `setup.scar` template (used for the
  `setup.wc-guard.scar` diagnostic; not needed for the recommended build).
  Lint clean (ruff).

### Variants (`scripts/build_variants.sh`)

```
scripts/build_variants.sh [EXTRACT_ROOT]
```

Produces `dist/over-40000-v0.4.0-*.zip` (self-contained, `README-TEST.txt`):

- `A-noscale` — control (scale off, WC off). **No crash.**
- `B-skip-canattach` — scale x5, all can-attach excluded, WC on. **Crash.**
- `C-skip-hg-attach` — scale x5, `_hg*` excluded, WC on. **Crash.**
- `D-attach-2x` — scale x5 / can-attach x2, WC on. **Crash.**
- `E-nowc` — B minus WC block. **No crash** ⇒ WC necessary.
- `F-wc-only` — A plus WC block. **Crash** ⇒ WC sufficient.
- `G-wc-guard` — v0.4.0 + nil/0-guarded WC block. **Crash** ⇒ guard insufficient;
  WC block must be removed, not guarded.

### Recommended production build

`dist/over-40000-v0.4.0-recommended.zip` — full v0.4.0 feature set (scale x5,
can-attach `scale`) with the WC block removed. User-approved deliverable.

## Decision constraints / caveats

- The recommended build ships the **full v0.4.0 squad-scaling feature set**
  (including can-attach `scale`) minus the WC block. The human approved this
  config after the guard failed.
- `--weapon-cap-boost` defaults to `off`; `setup.wc-guard.scar` and the `auto`/
  `on` flags remain only for diagnostics and are NOT used in production.
- Do not silently ship a can-attach policy change — the tests show it does not
  stop the crash.

## Files

- `over-40000/scripts/generate_mod.py` — generator (can-attach policy,
  `--weapon-cap-boost` default off, `--resource-cheat {on,off}`,
  `--setup-template`)
- `over-40000/scripts/build_variants.sh` — built the 7 diagnostic test ZIPs
  (historic; not needed for the release)
- `over-40000/scripts/templates/setup.scar` — WC block present (unguarded; NOT
  used by the release build)
- `over-40000/scripts/templates/setup.nocheat.scar` — vanilla setup.scar used
  by the `-normal-resources` variant
- `over-40000/scripts/templates/setup.wc-guard.scar` — nil/0-guarded WC block
  (diagnostic only; guard proven insufficient in-game)
- `over-40000/dist/over-40000-v0.1.0.zip` — **release A** (resource cheat on)
- `over-40000/dist/over-40000-v0.1.0-normal-resources.zip` — **release B**
  (normal resources; setup.scar byte-identical to vanilla)
- `over-40000/NEXUS_DESCRIPTION.md` — copy-paste text for the Nexus page
- Scratch analysis tools under `../.copilot_workspace/`:
  - `scan_reinforce.py`, `find_max_upgrades.py`, `dump_reinforce.py`,
    `dump_top_ext.py`, `dump_loadout.py` — mechanism data scans
  - `analyze_squad.py`, `scan_squads.py`, `scan_attach.py`, `attach_dump.py`,
    `dump_ext.py`, `diff_floats.py`, `check_ebp_costs.py`
  - `squad_scan.tsv` (866 squads), `attach_scan.tsv`
  - `build_g.sh`, `build_recommended.sh`, `build_release.sh` — build scripts
- Extracted data: `../.copilot_workspace/extract/`
- Saved builds: `../.copilot_workspace/saved/` (v0.3.0 + old zips)

---

## Next-session prompt

```
Context: over-40000 mod (DoW DE), Haemonculus HG crash in v0.4.0 — RESOLVED &
RELEASED as 0.1.0. Resume from:
dawn-of-war-de/over-40000/HANDOVER-HAEMONCULUS-CRASH.md
Read the handover, then:
1. ROOT CAUSE CONFIRMED + FIX SHIPPED: the Over40000_BoostWeaponCaps block in
   setup.scar was both necessary and sufficient for the crash (E-nowc no crash
   / F-wc-only crash, single-variable deltas). The nil/0 guard (variant
   G-wc-guard) ALSO crashed in-game, so the block was REMOVED ENTIRELY.
2. Released as 0.1.0 in two variants (both: squad scale x5, can-attach scale,
   EBP cost counter-scale, WC block gone):
     dist/over-40000-v0.1.0.zip                   (resource cheat on)
     dist/over-40000-v0.1.0-normal-resources.zip  (normal resources)
   All test builds were deleted. NEXUS_DESCRIPTION.md written (fun-mod framing).
3. Ask the human whether both 0.1.0 builds play crash-free in-game (build a
   Haemonculus HG, watch ~6s). If they do, the release is complete.
4. Do NOT reintroduce the WC block; do not ship diagnostic variants.
```