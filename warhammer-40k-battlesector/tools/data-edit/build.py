#!/usr/bin/env python3
"""Reference data-edit implementation — Battlesector unit & weapon stats.

Preserved from the retired **Superhuman Cadian** demo mod. This is the runnable
worked example behind `../../data_edit_tutorial.md`: it edits two balance tables
inside one Unity asset bundle and packages the result as a Vortex zip.

WHAT THIS EXAMPLE DOES (single-player sandbox / teaching)
=========================================================
It edits two balance tables inside ONE Unity asset bundle:

  * Unit 7003 "Cadian Shock Troops"
      - every core stat-sheet value  x2   (HP, movement, action points, evasion,
        armour, melee accuracy, activation/awareness range, momentum, ...)
      - unit point cost forced to 1
  * Weapon 7010 "Lasgun"
      - Attacks (shots per attack)  4 -> 50
      - Damage                      4 -> 8   (double)
      - ArmourPenetration           1 -> 2   (double)

HOW IT WORKS (the part worth learning)
======================================
Battlesector keeps its unit/weapon balance tables in one asset bundle:

    Warhammer 40K Battlesector_Data/StreamingAssets/startup_assets_all.bundle

which holds two MonoBehaviour tables:

    UnitDataTable     (one entry per unit)
    WeaponDataTable   (one entry per weapon)

Both are a pair of parallel arrays: ``keys[i]`` is the id of the entry whose stat
sheet is ``values[i]`` (e.g. keys[126] == "7003" -> values[126] is the Cadian
Shock Troops sheet). Editing a stat is just poking a field in that dict.

This script:
  1. loads the pristine bundle with UnityPy,
  2. finds the two tables by ``m_Name``,
  3. edits the numeric fields in place,
  4. saves the bundle back with the original packer,
  5. writes the bundle at its game-root-relative path (no metadata files),
  6. zips everything to ``dist/superhuman-cadian-v<version>.zip`` (deterministic),
  7. re-opens the produced bundle and asserts the new values are present.

USAGE
=====
    python build.py            # build -> dist/superhuman-cadian-v<ver>.zip
    python build.py dump       # print the CURRENT target values from the base
    python build.py --help

Requires UnityPy (``pip install UnityPy``), or run it through uv:

    uv run --no-project --with UnityPy python build.py

ENV
===
    BS_GAME_DIR        game install folder
                       (default: /mnt/d/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector)
    BS_VANILLA_BUNDLE  pristine startup bundle
                       (default: <game>/Warhammer 40K Battlesector_Data/StreamingAssets/
                                 startup_assets_all.bundle.vortex_backup)
"""

from __future__ import annotations

import os
import shutil
import sys
import zipfile
from pathlib import Path

import UnityPy

# ---------------------------------------------------------------------------
# The teaching payload — every edit this mod makes lives in this block.
# ---------------------------------------------------------------------------

VERSION = "1.0.1"
MOD_ID = "superhuman-cadian"
MOD_NAME = "Superhuman Cadian — A Tutorial on Modding Unit Stats"

# --- Unit 7003: Cadian Shock Troops ---------------------------------------
UNIT_ID = 7003

# Multiply every field in UNIT_SCALE_FIELDS by this.
UNIT_MULTIPLIER = 2.0

# The "core stat sheet": the numbers the game reads as a unit's stats. We list
# them EXPLICITLY rather than multiplying *every* field in the entry, because an
# entry also contains ids, enum codes, asset references and arrays — doubling
# those would corrupt the unit. (See ../../data_edit_tutorial.md §6.)
UNIT_SCALE_FIELDS = (
    "MaxHealth",  # per-model HP (total = MaxHealth x Members)
    "MaxActionPoints",  # AP per activation
    "MaxMovementPoints",  # movement points per turn
    "MinMovementRange",  # minimum move distance
    "Evasion",  # incoming-accuracy penalty
    "SingularArmor",  # damage-reduction armour (all-round profile)
    "ArmorFront",
    "ArmorLeft",
    "ArmorRight",
    "ArmorRear",
    "MeleeAccuracy",  # melee hit chance (a percentage -> capped at 100)
    "RangedAccuracyModifier",
    "RangedFalloffModifier",
    "ActivationRange",
    "AwarenessRange",
    "AwarenessConeRange",
    "MomentumPerModelDeath",
)

# Percent-style fields cannot usefully exceed 100.
PERCENT_FIELDS = {"MeleeAccuracy", "RangedAccuracyModifier", "RangedFalloffModifier"}
PERCENT_CAP = 100.0

# Absolute overrides applied after scaling (field -> exact new value).
UNIT_ABSOLUTE_FIELDS = {
    "PointCost": 1,  # was 40 — this is the "cheap unit" lever
}

# --- Weapon 7010: Lasgun --------------------------------------------------
# field -> absolute new value. Attacks is the shot count; Damage a float; AP int.
WEAPON_PATCHES: dict[int, dict[str, object]] = {
    7010: {
        "Attacks": 50,
        "Damage": 8.0,
        "ArmourPenetration": 2,
    },
}

# ---------------------------------------------------------------------------
# Paths / I/O plumbing.
# ---------------------------------------------------------------------------

HERE = Path(__file__).resolve().parent
STAGE = HERE / ".copilot_workspace" / "stage"
DIST = HERE / "dist"
BUNDLE_REL = "Warhammer 40K Battlesector_Data/StreamingAssets/startup_assets_all.bundle"

_GAME_DIR = os.environ.get(
    "BS_GAME_DIR",
    "/mnt/d/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector",
)
VANILLA_BUNDLE = Path(
    os.environ.get(
        "BS_VANILLA_BUNDLE",
        f"{_GAME_DIR}/Warhammer 40K Battlesector_Data/StreamingAssets/"
        "startup_assets_all.bundle.vortex_backup",
    )
)


# ---------------------------------------------------------------------------
# Table helpers.
# ---------------------------------------------------------------------------


def find_table(env, name: str):
    """Return (object, typetree) for the MonoBehaviour table called ``name``."""
    for o in env.objects:
        if o.type.name != "MonoBehaviour":
            continue
        try:
            t = o.read_typetree()
        except Exception:  # non-script MonoBehaviours can't be parsed
            continue
        if isinstance(t, dict) and t.get("m_Name") == name:
            return o, t
    raise SystemExit(f"{name} not found in bundle — is this a Battlesector startup bundle?")


def row_index(tree: dict, ident: int) -> int:
    """Index of ``ident`` in a keys/values table (keys may be ints or strings)."""
    keys = tree["keys"]
    as_is = [k if isinstance(k, int) else str(k) for k in keys]
    for want in (ident, str(ident)):
        try:
            return as_is.index(want)
        except ValueError:
            continue
    raise SystemExit(f"id {ident} not found in table ({len(keys)} entries)")


def scaled(old: object, mult: float, percent_cap: float | None) -> object:
    """old x mult, preserving int/float type and honouring a percentage cap."""
    new = float(old) * mult
    if percent_cap is not None:
        new = min(new, percent_cap)
    if isinstance(old, int):
        return round(new)
    return new


# ---------------------------------------------------------------------------
# Edits.
# ---------------------------------------------------------------------------


def patch_unit(tree: dict) -> list[str]:
    idx = row_index(tree, UNIT_ID)
    unit = tree["values"][idx]
    changes: list[str] = []
    for field in UNIT_SCALE_FIELDS:
        if field not in unit:
            continue
        cap = PERCENT_CAP if field in PERCENT_FIELDS else None
        before = unit[field]
        after = scaled(before, UNIT_MULTIPLIER, cap)
        unit[field] = after
        changes.append(f"unit {UNIT_ID} {field}: {before} -> {after}")
    for field, value in UNIT_ABSOLUTE_FIELDS.items():
        before = unit.get(field)
        unit[field] = value
        changes.append(f"unit {UNIT_ID} {field}: {before} -> {value}")
    return changes


def patch_weapons(tree: dict) -> list[str]:
    changes: list[str] = []
    for weapon_id, fields in WEAPON_PATCHES.items():
        idx = row_index(tree, weapon_id)
        weapon = tree["values"][idx]
        for field, value in fields.items():
            before = weapon.get(field)
            weapon[field] = value
            changes.append(f"weapon {weapon_id} {field}: {before} -> {value}")
    return changes


# ---------------------------------------------------------------------------
# Build.
# ---------------------------------------------------------------------------


def apply_edits(env) -> list[str]:
    changes: list[str] = []
    unit_obj, unit_tree = find_table(env, "UnitDataTable")
    changes += patch_unit(unit_tree)
    unit_obj.save_typetree(unit_tree)

    weapon_obj, weapon_tree = find_table(env, "WeaponDataTable")
    changes += patch_weapons(weapon_tree)
    weapon_obj.save_typetree(weapon_tree)
    return changes


def write_zip(out_path: Path, entries: dict[str, bytes]) -> None:
    """Write a byte-deterministic zip (fixed timestamps/attrs)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        for arcname, data in sorted(entries.items()):
            info = zipfile.ZipInfo(arcname, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, data)


def modinfo() -> dict:
    return {
        "id": MOD_ID,
        "name": MOD_NAME,
        "game": "warhammer-40k-battlesector",
        "version": VERSION,
        "author": "crystal-mods",
        "category": "Gameplay",
        "type": "asset-edit",
        "platforms": ["windows", "linux-proton"],
        "supportedVersions": ["1.7.7"],
        "engine": "Unity 6000.0.62f1 (IL2CPP)",
        "description": (
            "Demo/tutorial gameplay mod. Cadian Shock Troops (unit 7003): every core "
            "stat x2 and unit cost reduced to 1. Lasgun (weapon 7010): 50 attacks, "
            "double damage, double armour penetration."
        ),
        "changes": {
            "unit": {
                "id": UNIT_ID,
                "name": "Cadian Shock Troops",
                "statMultiplier": UNIT_MULTIPLIER,
                "pointCost": UNIT_ABSOLUTE_FIELDS["PointCost"],
            },
            "weapon": {"id": 7010, "name": "Lasgun", **WEAPON_PATCHES[7010]},
        },
        "deployFiles": [BUNDLE_REL],
        "conflicts": [
            "Any mod replacing warhammer-40k-battlesector "
            "Warhammer 40K Battlesector_Data/StreamingAssets/startup_assets_all.bundle "
            "(e.g. The Great Crusade, Traditional Chinese Localization). Only one "
            "startup-bundle mod can win that file."
        ],
    }


def build() -> Path:
    if not VANILLA_BUNDLE.exists():
        raise SystemExit(
            f"vanilla base bundle not found: {VANILLA_BUNDLE}\n"
            "Point BS_VANILLA_BUNDLE at a pristine startup_assets_all.bundle "
            "(Steam -> Verify integrity of game files, or a Vortex .vortex_backup)."
        )
    print(f"[build] base = {VANILLA_BUNDLE}")
    env = UnityPy.load(str(VANILLA_BUNDLE))
    for line in apply_edits(env):
        print("   *", line)
    bundle_bytes = env.file.save(packer="original")

    stage = STAGE
    # Start from a clean stage: a previous build's leftovers (e.g. the old
    # modinfo.json / README.md) must never leak into the archive.
    if stage.exists():
        shutil.rmtree(stage)
    bundle_out = stage / BUNDLE_REL
    bundle_out.parent.mkdir(parents=True, exist_ok=True)
    bundle_out.write_bytes(bundle_bytes)

    # modinfo.json / README.md are repo metadata, NOT game files — never stage
    # them, or the Vortex extension (which deploys every archive path) would put
    # them in the game root.

    verify(bundle_out)

    entries: dict[str, bytes] = {}
    for p in sorted(stage.rglob("*")):
        if p.is_file():
            entries[p.relative_to(stage).as_posix()] = p.read_bytes()
    out_zip = DIST / f"{MOD_ID}-v{VERSION}.zip"
    write_zip(out_zip, entries)
    print(f"[build] packaged -> {out_zip} ({out_zip.stat().st_size / 1048576:.1f} MB)")
    return out_zip


# ---------------------------------------------------------------------------
# Verify (read the produced bundle back and assert).
# ---------------------------------------------------------------------------


def _read_tables(path: Path) -> dict[str, dict]:
    env = UnityPy.load(str(path))
    out: dict[str, dict] = {}
    for o in env.objects:
        if o.type.name != "MonoBehaviour":
            continue
        try:
            t = o.read_typetree()
        except Exception:  # non-script MonoBehaviours can't be parsed
            continue
        if isinstance(t, dict) and t.get("m_Name") in ("UnitDataTable", "WeaponDataTable"):
            out[t["m_Name"]] = t
    return out


def verify(path: Path) -> None:
    tables = _read_tables(path)
    unit = tables["UnitDataTable"]["values"][row_index(tables["UnitDataTable"], UNIT_ID)]
    weapon = tables["WeaponDataTable"]["values"][row_index(tables["WeaponDataTable"], 7010)]

    assert unit["PointCost"] == 1, unit["PointCost"]
    assert unit["MaxHealth"] == 60, unit["MaxHealth"]
    assert unit["MaxActionPoints"] == 2, unit["MaxActionPoints"]
    assert unit["MaxMovementPoints"] == 8, unit["MaxMovementPoints"]
    assert unit["Evasion"] == 10, unit["Evasion"]
    assert unit["SingularArmor"] == 4, unit["SingularArmor"]
    assert unit["MeleeAccuracy"] == 100.0, unit["MeleeAccuracy"]
    assert weapon["Attacks"] == 50, weapon["Attacks"]
    assert weapon["Damage"] == 8.0, weapon["Damage"]
    assert weapon["ArmourPenetration"] == 2, weapon["ArmourPenetration"]
    print(
        "  verify OK: unit 7003 (HP 60, AP 2, MP 8, cost 1), lasgun 7010 (50 attacks, 8 dmg, 2 AP)"
    )


# ---------------------------------------------------------------------------
# Dump (inspect the base bundle's current values).
# ---------------------------------------------------------------------------


def dump() -> int:
    if not VANILLA_BUNDLE.exists():
        raise SystemExit(f"base bundle not found: {VANILLA_BUNDLE}")
    tables = _read_tables(VANILLA_BUNDLE)
    unit = tables["UnitDataTable"]["values"][row_index(tables["UnitDataTable"], UNIT_ID)]
    weapon = tables["WeaponDataTable"]["values"][row_index(tables["WeaponDataTable"], 7010)]
    print(f"== Unit {UNIT_ID} ({VANILLA_BUNDLE.name}) ==")
    for field in list(UNIT_SCALE_FIELDS) + list(UNIT_ABSOLUTE_FIELDS):
        print(f"  {field} = {unit.get(field)}")
    print("== Weapon 7010 ==")
    for field in WEAPON_PATCHES[7010]:
        print(f"  {field} = {weapon.get(field)}")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[1] == "dump":
        return dump()
    if len(argv) >= 2 and argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0
    build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
