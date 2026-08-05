#!/usr/bin/env python3
"""Crusade upgrade-card effect editing for the-great-crusade.

This module powers the hand-editable ``cards.json`` workflow:

  * ``export_cards(env)``  -> read the vanilla bundle and produce the JSON
    document (all player-eligible WarzoneUpgradeCards, with readable stat names,
    card tiers, and a legend explaining every field). Regenerate with
    ``make export-cards``.
  * ``load_cards(path)``   -> read ``cards.json`` back in.
  * ``apply_card_effects(env, data)`` -> overwrite each card's effect values in
    the bundle from the JSON. Called by ``build.py`` on every build.

Only the numeric effect fields are overridden in place (Type / Multiplier /
AddSubtract / Chance / IntValue); every other serialized field on the card is
preserved. Cards are matched by ``id`` (internalID); effects are matched by
position, and each effect also carries its ``stat`` name so a stat type can be
retyped by hand.
"""

from __future__ import annotations

import json
import struct
from pathlib import Path

# ---------------------------------------------------------------------------
# Enum tables (mirrored from the decompiled Assembly-CSharp, game v1.7.7).
# ---------------------------------------------------------------------------
# WarzoneUpgradeCard.Rarity  -> the card "tier".
RARITY_NAMES: dict[int, str] = {0: "Common", 1: "Uncommon", 2: "Rare", 3: "Legendary"}
RARITY_IDS: dict[str, int] = {v: k for k, v in RARITY_NAMES.items()}

# RoleGroup -> which unit roles a card can be offered to (informational).
ROLE_NAMES: dict[int, str] = {
    0: "None",
    1: "HQ",
    2: "Troop",
    3: "Elite",
    4: "Flyer",
    5: "FastAttack",
    6: "HeavySupport",
    7: "DedicatedTransport",
    8: "Fortification",
    9: "LordOfWar",
    10: "Trap",
}

# WarzoneUpgradeCard.Filter (bit flags) -> who the card applies to.
PLAYER_BIT, ENEMY_BIT, CLUSTER_BIT = 0x4, 0x8, 0x10
FILTER_FLAGS: dict[int, str] = {
    0x1: "Melee",
    0x2: "Ranged",
    0x4: "Player",
    0x8: "Enemy",
    0x10: "ClusterModifier",
    0x20: "Exclude_Vehicle",
    0x40: "Exclude_Flamers",
}

# StatChangeType -> what stat a card effect changes. Name <-> id both ways.
STAT_TYPES: dict[str, int] = {
    "None": 0,
    "Evasion": 1,
    "Movement": 2,
    "MinMovementRange": 3,
    "RangedArmor": 4,
    "MeleeArmor": 5,
    "BasicRangedDamageReceived": 6,
    "BasicMeleeDamageReceived": 7,
    "ActionPoints": 8,
    "RangedFalloff": 9,
    "MaxHP": 10,
    "CurrentHP": 11,
    "AdditionalMeleeAttacks": 12,
    "CustomMoveAnimation": 13,
    "MoveSpeed": 14,
    "MomentumGains": 15,
    "Momentum": 16,
    "HealPerTurn": 17,
    "HPPerModel": 18,
    "AdditionalRangedAttacks": 19,
    "AdditionalAttacks": 20,
    "PoisonRangedDamageReceived": 21,
    "PoisonMeleeDamageReceived": 22,
    "AllRangedDamageReceived": 23,
    "AllMeleeDamageReceived": 24,
    "IgnoreOverwatch": 25,
    "IgnorePistolChargeReactions": 26,
    "IgnoreMeleeZonesOfControl": 27,
    "IgnorePistolZonesOfControl": 28,
    "MPWhenLeavingTile": 29,
    "AllArmor": 30,
    "AllDamageReceived": 31,
    "PreventAllReactionAttacks": 32,
    "BonusHP": 33,
    "HealPerTurnPerModelPerMomentum": 34,
    "MomentumIfMovedEnoughFromSpawn": 35,
    "CustomIdleAnimation": 36,
    "CustomDamageAnimation": 37,
    "MovementCost": 38,
    "PreventSuppression": 39,
    "CriticalChanceAgainst": 40,
    "MeleeDamage": 1000,
    "RangedAccuracy": 1001,
    "MeleeAccuracy": 1002,
    "RangedDamage": 1003,
    "ArmorPiercing": 1004,
    "RangedAccuracyNonPistol": 1005,
    "RangedArmorPiercing": 1006,
    "MeleeArmorPiercing": 1007,
    "TileDamage": 1008,
    "CriticalChance": 1009,
    "CriticalChancePerMomentum": 1010,
    "AccuracyPerMomentum": 1011,
    "EvasionPerMomentum": 1012,
    "Accuracy": 1013,
    "Damage": 1014,
    "SplashDamage": 1015,
    "RangedIgnorePartialCover": 1016,
    "RangedDamageVehicle": 1017,
    "RangedArmourPiercingVehicle": 1018,
    "RangedCriticalChanceVehicle": 1019,
    "AllShots": 1020,
    "RangedAutoHit": 1021,
    "MaximumWeaponRange": 1022,
    "DamagePerMomentum": 1023,
    "RangeFalloffPerMomentum": 1024,
    "ArmorPiercingPerMomentum": 1025,
    "UnspentActionLoss": 1026,
    "RangedDamagePerMomentum": 1027,
    "ChangeIncomingGrazeChance": 1028,
    "ChangeOutcomingGrazeChance": 1029,
    "ChangeOutcomingGrazePerMomentumChance": 1030,
    "ChangeIncomingGrazePerMomentumChance": 1031,
    "CriticalChanceMelee": 1032,
    "CriticalChanceRange": 1033,
    "ChanceToHit": 1034,
    "JumpingMovementMode": 2000,
    "AbilityTriggerChance": 2001,
    "ApplyDamageAtEndOfTurn": 2002,
    "RemoveAtEndOfTurn": 2003,
    "DamageSelfOnAttack": 2004,
    "IgnoreTerrainPenalties": 2005,
    "NaturalKillerTriggerChance": 2006,
    "AddStatusEffectOnRemoveIgnoreExpiration": 2007,
    "FlyingMovementMode": 2008,
    "IncreaseStatusEffectExpiration": 2009,
    "FullMeleeReaction": 2010,
    "AwarenessRange": 2011,
    "AwarenessConeRange": 2012,
    "AwarenessConeAngle": 2013,
    "FullZonesOfControl": 2014,
    "RemoveAfterMovement": 2015,
    "StatsModifiedWhileAdjacentToHQUnit": 2016,
    "ChangeGrazeImpactSFX": 2017,
    "IgnoreTerrainPenaltiesBelowHeight": 2018,
    "AdditionalAdjacentRangedShot": 2019,
    "AbilityRange": 2020,
    "ReflectMelee": 2021,
    "Camouflaged": 2022,
    "ApplyDamageAtEndOfTurnToAllUnits": 2023,
    "PercentageDamageSelfOnAttack": 2024,
    "ArtilleryAnyRange": 3000,
    "ArtilleyArmorPiercingAgainst": 3001,
    "RangedArmorPiercingAgainst": 3002,
    "BuffRangedWeaponEffects": 3003,
    "BuffMeleeWeaponEffects": 3004,
    "RangedFalloffAgainst": 3005,
    "RangedAccuracyAgainst": 3006,
    "ArtilleryAccuracyAgainst": 3007,
    "PreventMovement": 10000,
    "PreventAttacking": 10001,
    "AdditionalAdjacentRangedTileSplash": 10002,
    "ChangeCommandPoints": 10003,
    "ChangeCommandPointParticles": 10004,
    "ChangeCommandPointParticlesGain": 10005,
}
STAT_NAMES: dict[int, str] = {v: k for k, v in STAT_TYPES.items()}

# Effect numeric fields overridden from JSON (all others preserved as-is).
_EFFECT_FIELDS = ("Multiplier", "AddSubtract", "Chance", "IntValue")

# Tier-based unit-cost reduction (percentage points subtracted from the vanilla
# costMultiplier) applied by `make cost-policy`. Higher tiers get cheaper.
TIER_COST_DELTA: dict[str, float] = {
    "Common": 0.10,
    "Uncommon": 0.15,
    "Rare": 0.20,
    "Legendary": 0.25,
}


def _f32(v: float) -> float:
    """Round-trip through float32 so JSON (float64) compares to the bundle value."""
    return struct.unpack("f", struct.pack("f", float(v)))[0]


def is_player_card(filter_flags: int) -> bool:
    """A card a player unit can receive (has Player bit, or isn't Enemy/Cluster)."""
    return bool(filter_flags & PLAYER_BIT) or not (filter_flags & (ENEMY_BIT | CLUSTER_BIT))


def decode_flags(value: int, table: dict[int, str]) -> list[str]:
    return [name for bit, name in table.items() if value & bit]


def _card_label(name: str, internal_id: int) -> str:
    """Turn 'WarzoneUpgradeCard-030-Armour&Evasion-Uncommon' into 'Armour&Evasion'."""
    parts = name.split("-")
    if parts and parts[0] == "WarzoneUpgradeCard":
        parts = parts[1:]
    if parts and parts[0].isdigit():
        parts = parts[1:]
    if parts and parts[-1] in RARITY_NAMES.values():
        parts = parts[:-1]
    return "-".join(parts) or name


def _iter_all_cards(env):
    """Yield (obj, typetree) for every WarzoneUpgradeCard (player and non-player)."""
    for o in env.objects:
        if o.type.name != "MonoBehaviour":
            continue
        try:
            t = o.read_typetree()
        except Exception:  # noqa: BLE001
            continue
        if not (isinstance(t, dict) and "statsModifiers" in t and "supportedRoles" in t):
            continue
        yield o, t


def _describe_effect(stat: str, mult: float, add: float, chance: float) -> str:
    parts = []
    if mult:
        parts.append(f"{mult * 100:+.0f}% {stat}")
    if add:
        parts.append(f"{add:+g} {stat}")
    if not parts:  # flag-style effect (no numeric change)
        parts.append(stat)
    text = " & ".join(parts)
    if chance:
        text += f" ({chance:g}% chance)"
    return text


def _card_note(tier: str, effects: list[dict], cost: float) -> str:
    """Human summary of a card, e.g. 'Rare: +20% RangedDamage [unit cost +5%]'."""
    bits = [
        _describe_effect(e["stat"], e["multiplier"], e["addSubtract"], e["chance"]) for e in effects
    ]
    note = f"{tier}: " + "; ".join(bits) if bits else tier
    return f"{note} [unit cost {cost * 100:+.0f}%]"


_LEGEND = {
    "_readme": (
        "Hand-editable Crusade upgrade-card effects for the-great-crusade. "
        "Edit the numbers under each card's 'effects' and rebuild with `make` "
        "(every build reads this file). Only 'multiplier', 'addSubtract', "
        "'chance', 'intValue' and 'stat' are applied; other keys are "
        "informational. Regenerate defaults with `make export-cards FORCE=1`. "
        "Player-facing upgrades are in cards.json; enemy / cluster-modifier "
        "cards are in cards-nonplayer.json."
    ),
    "_fields": {
        "id": "Card internalID. Match key — do NOT change.",
        "name": "Human label for the card (informational only).",
        "note": "Auto-generated summary of the card's current effects (informational).",
        "tier": "Card rarity/tier: Common | Uncommon | Rare | Legendary (informational).",
        "costMultiplier": "Extra unit point-cost when this upgrade is taken. 0.1 = +10%, -0.1 = -10%, 0 = no change. Editable.",
        "roles": "Unit roles that can be offered this card (informational).",
        "effects": "List of stat changes applied when the card is picked.",
        "effects[].stat": "Which stat changes (see _statTypes). Editable — retype to change the stat.",
        "effects[].multiplier": "Percent change applied first. 0.2 = +20%, -0.5 = -50%, 0 = no multiplier.",
        "effects[].addSubtract": "Flat amount added after the multiplier. 5 = +5, -3 = -3.",
        "effects[].chance": "0-100 percent chance the effect triggers. 0 = always.",
        "effects[].intValue": "Integer parameter used by a few stat types (leave as-is if unsure).",
    },
    "_tiers": RARITY_IDS,
}


def export_cards(env, player: bool | None = True) -> dict:
    """Build the hand-editable JSON document from the vanilla bundle.

    ``player=True`` -> player-facing upgrade cards; ``player=False`` -> enemy /
    cluster-modifier cards; ``player=None`` -> all cards (used for the vanilla
    reference).
    """
    used_stats: dict[str, int] = {}
    cards: list[dict] = []
    for _o, t in _iter_all_cards(env):
        if player is not None and is_player_card(int(t.get("filter", 0))) != player:
            continue
        internal_id = int(t.get("internalID", 0))
        rarity = int(t.get("rarity", 0))
        roles = [ROLE_NAMES.get(int(r), str(r)) for r in t.get("supportedRoles", [])]
        effects = []
        for s in t.get("statsModifiers", []) or []:
            if not isinstance(s, dict):
                continue
            stat_id = int(s.get("Type", 0))
            stat_name = STAT_NAMES.get(stat_id, str(stat_id))
            used_stats[stat_name] = stat_id
            effects.append(
                {
                    "stat": stat_name,
                    "multiplier": round(float(s.get("Multiplier", 0.0)), 6),
                    "addSubtract": round(float(s.get("AddSubtract", 0.0)), 6),
                    "chance": round(float(s.get("Chance", 0.0)), 6),
                    "intValue": int(s.get("IntValue", 0)),
                }
            )
        tier = RARITY_NAMES.get(rarity, str(rarity))
        cost = round(float(t.get("extraTAPCostMultiplier", 0.0)), 6)
        cards.append(
            {
                "id": internal_id,
                "name": _card_label(str(t.get("m_Name", "")), internal_id),
                "note": _card_note(tier, effects, cost),
                "tier": tier,
                "costMultiplier": cost,
                "roles": roles,
                "effects": effects,
            }
        )
    cards.sort(key=lambda c: c["id"])
    doc = dict(_LEGEND)
    doc["_scope"] = (
        "player upgrade cards"
        if player is True
        else "enemy / cluster-modifier cards"
        if player is False
        else "ALL cards (frozen vanilla reference — do not hand-edit)"
    )
    # only list the stat types actually present, sorted by id, for a compact legend
    doc["_statTypes"] = {
        name: sid for name, sid in sorted(used_stats.items(), key=lambda kv: kv[1])
    }
    doc["cards"] = cards
    return doc


def write_cards(env, path: Path, player: bool = True, force: bool = False) -> bool:
    """Write a card JSON file from the vanilla bundle. Refuses to clobber unless force."""
    if path.exists() and not force:
        print(f"  {path.name} already exists — not overwriting (use FORCE=1).")
        return False
    doc = export_cards(env, player=player)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print(f"  wrote {path.name} ({len(doc['cards'])} cards)")
    return True


def load_cards(path: Path) -> dict:
    return json.loads(path.read_text())


def _overrides_by_id(*docs: dict) -> dict[int, dict]:
    merged: dict[int, dict] = {}
    for data in docs:
        for c in data.get("cards", []):
            merged[int(c["id"])] = c
    return merged


def apply_card_effects(env, *docs: dict) -> list[str]:
    """Override each card's effect values in the bundle from one or more JSON docs."""
    overrides = _overrides_by_id(*docs)
    changes: list[str] = []
    seen: set[int] = set()
    for o, t in _iter_all_cards(env):
        internal_id = int(t.get("internalID", 0))
        card = overrides.get(internal_id)
        if card is None:
            continue
        seen.add(internal_id)
        effects = card.get("effects", [])
        live = t.get("statsModifiers") or []
        if len(effects) != len(live):
            raise SystemExit(
                f"card {internal_id} ({card.get('name')}): cards.json has "
                f"{len(effects)} effects but the bundle has {len(live)}. Effects "
                "are matched by position — do not add or remove effect entries."
            )
        dirty = False
        if "costMultiplier" in card:
            new_cost = float(card["costMultiplier"])
            if _f32(t.get("extraTAPCostMultiplier", 0.0)) != _f32(new_cost):
                t["extraTAPCostMultiplier"] = new_cost
                dirty = True
        for edit, slot in zip(effects, live):
            stat_name = edit.get("stat")
            if stat_name is not None:
                if stat_name not in STAT_TYPES:
                    raise SystemExit(
                        f"card {internal_id}: unknown stat {stat_name!r}. "
                        "See the _statTypes legend in cards.json."
                    )
                new_type = STAT_TYPES[stat_name]
                if int(slot.get("Type", 0)) != new_type:
                    slot["Type"] = new_type
                    dirty = True
            for json_key, tt_key in (
                ("multiplier", "Multiplier"),
                ("addSubtract", "AddSubtract"),
                ("chance", "Chance"),
                ("intValue", "IntValue"),
            ):
                if json_key not in edit:
                    continue
                new_val = edit[json_key]
                if tt_key == "IntValue":
                    new_val = int(new_val)
                    if slot.get(tt_key) != new_val:
                        slot[tt_key] = new_val
                        dirty = True
                else:
                    new_val = float(new_val)
                    if _f32(slot.get(tt_key, 0.0)) != _f32(new_val):
                        slot[tt_key] = new_val
                        dirty = True
        if dirty:
            o.save_typetree(t)
            changes.append(f"card {internal_id} ({card.get('name')}): effects updated")
    missing = set(overrides) - seen
    if missing:
        print(f"  note: {len(missing)} cards.json id(s) not found in bundle: {sorted(missing)}")
    return changes


def apply_cost_policy(
    doc: dict, vanilla_by_id: dict[int, dict], tier_delta: dict[str, float] | None = None
) -> int:
    """Set each card's costMultiplier = vanilla cost - tier reduction; refresh notes.

    Reads the vanilla cost from ``vanilla_by_id`` (from cards-vanilla.json) so the
    result is idempotent regardless of the current value in ``doc``.
    """
    tier_delta = tier_delta or TIER_COST_DELTA
    changed = 0
    for c in doc.get("cards", []):
        tier = c.get("tier")
        delta = tier_delta.get(tier)
        if delta is None:
            continue
        van = vanilla_by_id.get(int(c["id"]))
        van_cost = (
            float(van["costMultiplier"])
            if van and "costMultiplier" in van
            else float(c.get("costMultiplier", 0.0))
        )
        new_cost = round(van_cost - delta, 6)
        c["costMultiplier"] = new_cost
        c["note"] = _card_note(tier, c.get("effects", []), new_cost)
        changed += 1
    return changed


def check_vanilla(env, ref: dict) -> list[str]:
    """Compare the base bundle's card values to the frozen vanilla reference.

    Returns a list of human-readable mismatches (empty => base is vanilla). Used
    to detect a non-pristine base bundle before edits are layered on.
    """
    ref_by_id = _overrides_by_id(ref)
    mismatches: list[str] = []
    for _o, t in _iter_all_cards(env):
        internal_id = int(t.get("internalID", 0))
        card = ref_by_id.get(internal_id)
        if card is None:
            continue
        want_cost = float(card.get("costMultiplier", 0.0))
        if _f32(t.get("extraTAPCostMultiplier", 0.0)) != _f32(want_cost):
            mismatches.append(
                f"card {internal_id}: costMultiplier base={t.get('extraTAPCostMultiplier')} vanilla={want_cost}"
            )
        live = t.get("statsModifiers") or []
        for i, (edit, slot) in enumerate(zip(card.get("effects", []), live)):
            for json_key, tt_key in (("multiplier", "Multiplier"), ("addSubtract", "AddSubtract")):
                if _f32(slot.get(tt_key, 0.0)) != _f32(float(edit.get(json_key, 0.0))):
                    mismatches.append(
                        f"card {internal_id} effect[{i}].{tt_key}: base={slot.get(tt_key)} vanilla={edit.get(json_key)}"
                    )
    return mismatches
