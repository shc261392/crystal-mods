# Easy Reinforcement — Dawn of War Definitive Edition

A small **standalone** mod that automatically reinforces the human player's
squads up to their full model count. It complements the "Over 40000" power-cheat
mod (which no longer bundles auto-reinforce) and can be used with it or on its
own.

> Formerly named **Auto Reinforcement**; renamed to **Easy Reinforcement** for
> 0.1.3.

## What it does

- Every ~1s, the human player's squads are set to passive **reinforce overwatch**
  mode (`SCMD_ReinforceTrooperOverwatch`), so they automatically reinforce up to
  their max model count.
- **It never interrupts your orders**: overwatch reinforcement happens in the
  background and does not change the squad's current build/capture/attack order.
- **Always on**: overwatch is kept enabled unconditionally (never turned off),
  so squads keep reinforcing even under attack. The command is idempotent, so
  re-sending it each tick is harmless and reliable.
- **Skips already-reinforcing squads** (`Squad_IsReinforcing`) to avoid redundant
  commands, and **skips work while an opening cinematic is playing**
  (`Event_IsAnyRunning`).
- **Requisition threshold**: overwatch is only enabled while the player's
  requisition is **>= 1000**. Below that, squads are not auto-reinforced, so the
  player keeps their requisition for other needs.
- Reinforcements cost requisition, which the game deducts automatically.

## Coverage

It ships as an **always-on wincondition** in the **W40k module**:
`W40k/Data/scar/winconditions/easyreinforce.scar` + `easyreinforce_local.lua`.

The engine resolves an always-on wincondition for **every** mission across all
four campaigns (main, Winter Assault, Dark Crusade, Soulstorm), so a single
W40k copy is sufficient. Shipping extra copies in the other modules would
register **duplicate 1s rules** (four copies → four rules each second), so this
mod ships exactly one.

## How it loads

`always_on = true` makes the wincondition load for **every** battle (single-player
missions, engine-driven multiplayer-map campaign battles, and skirmish) without
being selectable, and it does **not** conflict with the "Over 40000" mod's
`setup.scar`.

## Install

Drag `dist/easy-reinforcement-v0.1.3.zip` onto Vortex and **Deploy**. No other
mod is required.

**Uninstall:** disable/purge the mod in Vortex.

## Build

```bash
make build            # -> dist/easy-reinforcement-v0.1.3.zip
# or: bash build.sh   (Windows: .\build.ps1)
```

## Files

```
easy-reinforcement/
├── Makefile / build.sh / build.ps1
├── modinfo.json
└── mod/W40k/Data/scar/winconditions/
    ├── easyreinforce.scar
    └── easyreinforce_local.lua
```

## Version history

- **0.1.3** — renamed from Auto Reinforcement; current in-development build.
  Wincondition shipped in the W40k module only. (Under diagnostic iteration —
  an "Invalid command receiver" log line still appears in some missions; not
  yet resolved.)
- **0.1.2** — only auto-reinforce while the player's requisition is >= 1000.
- **0.1.1** — fix: always keep reinforce overwatch enabled. Removed the logic
  that turned overwatch off while a squad was under attack (which could leave
  squads un-reinforced).
- **0.1.0** — initial release as "Auto Reinforcement".