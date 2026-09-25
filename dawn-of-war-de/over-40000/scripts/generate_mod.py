#!/usr/bin/env python3
"""Generate the "Over 40000" mod tree from an extraction of the DoW DE game data.

Usage:
    python3 scripts/generate_mod.py EXTRACT_ROOT [MOD_ROOT]

Where EXTRACT_ROOT points at a `relic sga unpack` extraction tree that contains
`DXP2/data` and `DXP3/data` subfolders (the extracted DXP2Data.sga / DXP3Data.sga).

Outputs the mod tree (default `mod/`):

    mod/W40k/Data/scar/setup.scar                       (cheat hook)
    mod/DXP2/Data/attrib/sbps/.../<squad>.rgd           (patched unit limits)
    mod/DXP3/Data/attrib/sbps/.../<squad>.rgd           (patched unit limits)

Unit limits are implemented by binary-patching the `max_squad_cap` float of each
`required_squad_cap` requirement in-place inside the compiled `.rgd` file. The
patched file is byte-identical to vanilla except for those 4-byte values, so it
loads exactly like the base data (no `.lua` override format risk).

Run with --dry-run to only print what would be generated.
"""
from __future__ import annotations

import argparse
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rgd_decode import Decoder, extract_aegd, relic_hash

REF = 0x49D60FAE  # fixed "reference" key -> path value
MAX_SQ = relic_hash("max_squad_cap")
SQ_REQ_EXT = relic_hash("squad_requirement_ext")
REQUIREMENTS = relic_hash("requirements")
RACE_SQ_TABLE = relic_hash("race_squad_cap_table")
AEGD_OFF = 0x28  # DATAAEGD payload starts at file offset 0x28
MAX_CAP = 40000.0
RACE_CAP = 40001.0
MAX_POP_CAP = relic_hash("max_pop_cap")  # ork waaagh pool cap (ork_race race_pop_table)
ORK_BANNER_APPLY_TABLE = 0x7C408388      # ork_waagh_banner modifier apply table
ORK_BANNER_MODIFIER_VALUE = 0x2ED8F799   # the apply-entry "value" float
ORK_BANNER_POP_CAP = 4000.0              # cheat build: +4000 waaagh cap per banner

TEMPLATES = Path(__file__).parent / "templates"


def _cap_field_hashes() -> dict[int, str]:
    return {
        relic_hash("base_squad_cap"): "base_squad_cap",
        relic_hash("max_squad_cap"): "max_squad_cap",
        relic_hash("base_support_cap"): "base_support_cap",
        relic_hash("max_support_cap"): "max_support_cap",
    }


def patch_race_caps(path: Path, target: float = RACE_CAP) -> bytes | None:
    """Return a copy of a race .rgd with race_squad_cap_table caps (and, when
    present, the race_pop_table max_pop_cap) set to target. Only ork_race.rgd
    carries max_pop_cap, so that float is patched there and nowhere else."""
    orig = path.read_bytes()
    size = struct.unpack_from("<I", orig, 0x24)[0]
    aegd = orig[AEGD_OFF:AEGD_OFF + size]
    d = Decoder(aegd)
    fields = _cap_field_hashes()
    file_offsets: list[int] = []
    top = d._table(12)
    if top is None:
        return None
    for kh, typ, vabs in top[1]:
        if typ != 100 or kh != RACE_SQ_TABLE:
            continue
        tbl = d._table(vabs)
        if tbl is None:
            continue
        for kh2, typ2, vabs2 in tbl[1]:
            if typ2 == 0 and kh2 in fields:
                file_offsets.append(AEGD_OFF + vabs2)
    # ork waaagh pool cap: max_pop_cap lives in the race_pop_table (top-level key
    # 0xfd01714f) and may sit in trailing bytes past the declared AEGD size;
    # reach it with a nested walk and let the len(data) guard below decide.
    stack = [12]
    seen: set[int] = set()
    while stack:
        abs_t = stack.pop()
        if abs_t in seen:
            continue
        seen.add(abs_t)
        tbl = d._table(abs_t)
        if tbl is None:
            continue
        for kh2, typ2, vabs2 in tbl[1]:
            if typ2 == 100:
                stack.append(vabs2)
            elif typ2 == 0 and kh2 == MAX_POP_CAP:
                file_offsets.append(AEGD_OFF + vabs2)
    if not file_offsets:
        return None
    data = bytearray(orig)
    for foff in file_offsets:
        # guard: the last float may sit in trailing bytes past the declared size
        if foff + 4 <= len(data):
            struct.pack_into("<f", data, foff, target)
    return bytes(data)


def patch_banner_pop_cap(path: Path, target: float = ORK_BANNER_POP_CAP) -> bytes | None:
    """Return a copy of an ork_waagh_banner.rgd whose population_cap_player_modifier
    value float is set to `target` (per-banner waaagh pop cap grant).

    Semantic match: locate the applied-modifiers table (key 0x7c408388), then the
    entry whose modifier-path reference (key REF / 0x49d60fae) ends with
    `population_cap_player_modifier.lua`, and patch its value float
    (key ORK_BANNER_MODIFIER_VALUE / 0x2ed8f799).
    """
    orig = path.read_bytes()
    size = struct.unpack_from("<I", orig, 0x24)[0]
    aegd = orig[AEGD_OFF:AEGD_OFF + size]
    d = Decoder(aegd)
    # locate every applied-modifiers table
    apply_tables: list[int] = []
    stack = [12]
    seen: set[int] = set()
    while stack:
        abs_t = stack.pop()
        if abs_t in seen:
            continue
        seen.add(abs_t)
        tbl = d._table(abs_t)
        if tbl is None:
            continue
        for kh, typ, vabs in tbl[1]:
            if typ == 100:
                if kh == ORK_BANNER_APPLY_TABLE:
                    apply_tables.append(vabs)
                stack.append(vabs)
    value_offsets: list[int] = []
    for apply_abs in apply_tables:
        atl = d._table(apply_abs)
        if atl is None:
            continue
        for kh, typ, vabs in atl[1]:
            if typ != 100:
                continue
            entry = d._table(vabs)
            if entry is None:
                continue
            modpath = ""
            value_abs: int | None = None
            for kh2, typ2, vabs2 in entry[1]:
                if typ2 == 3 and kh2 == REF:
                    modpath = d._read_cstr(vabs2).lower()
                elif typ2 == 0 and kh2 == ORK_BANNER_MODIFIER_VALUE:
                    value_abs = vabs2
            if modpath.endswith("population_cap_player_modifier.lua") and value_abs is not None:
                value_offsets.append(AEGD_OFF + value_abs)
    if not value_offsets:
        return None
    data = bytearray(orig)
    for foff in value_offsets:
        if foff + 4 <= len(data):
            struct.pack_into("<f", data, foff, target)
    return bytes(data)


def find_max_squad_cap_offsets(aegd: bytes) -> list[int]:
    """Return AEGD-relative byte offsets of each required_squad_cap max_squad_cap float."""
    d = Decoder(aegd)
    offsets: list[int] = []
    top = d._table(12)
    if top is None:
        return offsets
    for kh, typ, vabs in top[1]:
        if typ != 100 or kh != SQ_REQ_EXT:
            continue
        req_ext = d._table(vabs)
        if req_ext is None:
            continue
        for kh2, typ2, vabs2 in req_ext[1]:
            if typ2 != 100 or kh2 != REQUIREMENTS:
                continue
            req_list = d._table(vabs2)
            if req_list is None:
                continue
            for kh3, typ3, vabs3 in req_list[1]:
                if typ3 != 100:
                    continue
                entry = d._table(vabs3)
                if entry is None:
                    continue
                is_cap = any(
                    typ4 == 3
                    and kh4 == REF
                    and d._read_cstr(vabs4).lower().endswith("required_squad_cap.lua")
                    for kh4, typ4, vabs4 in entry[1]
                )
                if not is_cap:
                    continue
                for kh4, typ4, vabs4 in entry[1]:
                    if typ4 == 0 and kh4 == MAX_SQ:
                        offsets.append(vabs4)
    return offsets


SQUAD_LOADOUT = relic_hash("squad_loadout_ext")
SQUAD_CAN_ATTACH = relic_hash("squad_can_attach_ext")
UNIT_MIN = relic_hash("unit_min")
UNIT_MAX = relic_hash("unit_max")
SQUAD_REINFORCE = relic_hash("squad_reinforce_ext")
COST_FIELD = relic_hash("cost")
REQUISITION = relic_hash("requisition")
POPULATION = relic_hash("population")
COST_EXT = relic_hash("cost_ext")
REINFORCE_FLOOR = 10.0   # requisition reinforce cost floor (lowest vanilla value is 20)
POPULATION_FLOOR = 1.0   # waaagh (ork population) reinforce cost floor
ALL_MODULES = ("W40k", "WXP", "DXP2", "DXP3")

# Squads/units that must NOT have their model count scaled: fixed-model
# "team" weapons (heavy-weapons teams, entrenched teams) are tied to a state
# machine that breaks with more models
# (e.g. "SIM -- Entity ... still has state 34 active while changing states").
SQUAD_SCALE_EXCLUDE = ("heavy_weapon", "entrench")

# How to treat squads that carry `squad_can_attach_ext` (attachable command
# units such as Force Commander / Chaos Lord / Haemonculus). Default `scale`
# is the v0.4.0 behavior that reproduced the Haemonculus HG crash. The other
# policies build the diagnostic test variants:
#   scale   - scale model count by squad_scale (v0.4.0 behavior, may crash)
#   skip    - never scale squads with squad_can_attach_ext (variant B)
#   skip-hg - never scale _hg* variants with squad_can_attach_ext (variant C)
#   scale2  - scale squad_can_attach_ext squads by 2 instead (variant D)
CAN_ATTACH_POLICIES = ("scale", "skip", "skip-hg", "scale2")


def is_squad_scale_excluded(name: str) -> bool:
    n = name.lower()
    return any(p in n for p in SQUAD_SCALE_EXCLUDE)


def squad_has_can_attach(aegd: bytes) -> bool:
    """True if the squad AEGD carries a top-level squad_can_attach_ext."""
    d = Decoder(aegd)
    top = d._table(12)
    if top is None:
        return False
    return any(typ == 100 and kh == SQUAD_CAN_ATTACH for kh, typ, _ in top[1])


def squad_unit_max(aegd: bytes) -> float:
    """Return the squad's squad_loadout_ext unit_max value (1.0 if absent)."""
    offs = find_unit_offsets(aegd)
    vabs = offs.get("unit_max")
    if vabs is None or vabs + 4 > len(aegd):
        return 1.0
    return struct.unpack_from("<f", aegd, vabs)[0]


def squad_loadout_ebp_refs(aegd: bytes) -> list[str]:
    r"""Return basenames (foo.rgd) of EBP files referenced by squad_loadout_ext.

    Each loadout trooper row holds `squadtrooper\squad_trooper.nil` plus the
    `ebps\races\...\troops\....lua` path of the model this squad spawns.
    """
    d = Decoder(aegd)
    out: list[str] = []
    top = d._table(12)
    if top is None:
        return out
    for kh, typ, vabs in top[1]:
        if typ != 100 or kh != SQUAD_LOADOUT:
            continue
        t = d._table(vabs)
        if t is None:
            continue
        for kh2, typ2, vabs2 in t[1]:
            if typ2 != 100:
                continue
            sub = d._table(vabs2)
            if sub is None:
                continue
            for kh3, typ3, vabs3 in sub[1]:
                if typ3 != 3:
                    continue
                p = d._read_cstr(vabs3).replace("\\", "/").lower()
                if p.startswith("ebps/") and p.endswith(".lua"):
                    out.append(p.rsplit("/", 1)[-1][:-4] + ".rgd")
    return out


def effective_scale_for(name: str, aegd: bytes, squad_scale: int, policy: str,
                        exclude_single_model: bool = False, exclude_sp: bool = False,
                        descale_campaign_single: bool = False,
                        module: str = "") -> int:
    """Model-count scale factor that should apply to this squad file.

    Returns 0 when the squad's model count must not change (fixed-model team
    squads, or squad_can_attach_ext squads excluded by the active policy).

    `exclude_single_model` applies only to the base-game modules (W40k/WXP):
    the base-game engine validates at mod load that squads with complex
    upgrades stay at unit_max==1 ("Squads with complex upgrades have a
    maximum unit count of one!"), so single-model squads cannot be scaled
    there. DXP2/DXP3 have no such validation and single-model squads scale
    freely.

    `descale_campaign_single` applies only to the expansion modules
    (DXP2/DXP3): single-model squads whose name carries a campaign-only marker
    (`_advance_sp`, `_sp`, `_veteran_sp`, `_hg`) are NOT scaled. These are the
    campaign army / honor-guard variants (e.g. `eldar_squad_wraithlord_advance_sp`,
    `sisters_squad_immolator_hg_dxp3`) that are spawned at mission start with
    min loadout; scaling them freezes the SIM (Wraithlord HG in Tau Stronghold).
    Regular skirmish single-model squads (Predator, Rhino, Sentinel, etc.) are
    not matched and still scale.
    """
    n = name.lower()
    if any(p in n for p in SQUAD_SCALE_EXCLUDE):
        return 0
    if squad_scale <= 0:
        return 0
    if exclude_single_model and module in ("W40k", "WXP") and squad_unit_max(aegd) == 1.0:
        return 0
    if descale_campaign_single and module in ("DXP2", "DXP3") \
            and squad_unit_max(aegd) == 1.0 and _is_campaign_variant_name(n):
        return 0
    if exclude_sp and "_sp" in n:
        return 0
    if not squad_has_can_attach(aegd):
        return squad_scale
    if policy == "skip":
        return 0
    if policy == "skip-hg":
        return 0 if "_hg" in n else squad_scale
    if policy == "scale2":
        return 2
    return squad_scale


def _is_campaign_variant_name(name: str) -> bool:
    """True if a squad basename carries a campaign-only variant marker.

    Matches `_sp`, `_advance_sp`, `_veteran_sp` as a trailing/component token,
    and `_hg` / `_hg_<module>` honor-guard variants. Uses token boundaries so
    skirmish units whose names merely contain `_sp` mid-word (e.g.
    `land_speeder`, `tomb_spyder`) are NOT matched.
    """
    return bool(re.search(r"_(?:advance_|veteran_)?sp(?:\.rgd|$|_)|_hg(?:\.rgd|$|_)", name))


def collect_scale_maps(extract_root: Path, squad_scale: int, policy: str,
                       exclude_single_model: bool = False, exclude_sp: bool = False,
                       descale_campaign_single: bool = False,
                       races: set[str] | None = None,
                       squad_filter: set[str] | None = None,
                       exclude_squads: set[str] | None = None,
                       overrides: dict[str, int] | None = None
                       ) -> tuple[dict[str, int], dict[str, int]]:
    """Pre-scan every squad to map squad filename -> scale factor and each
    referenced EBP basename -> cost-division divisor.

    A referenced EBP's divisor is the strictest (minimum) factor of all squads
    that spawn it, so a shared leader EBP is not over-divided when one of its
    squads is excluded.

    `races` (optional) restricts model-count scaling to those race dirs
    (extracted from the sbps path); other squads still get caps patched but
    are not scaled. The race is detected by looking for a `sbps\\races\\<race>`
    segment in the relative path.

    `squad_filter` (optional) restricts scaling to ONLY the listed squads;
    `exclude_squads` (optional) scales everything normally EXCEPT the listed
    squads. Use one or the other, not both.

    `overrides` (optional, EXPERIMENTAL) maps squad basename (lowercase, no
    .rgd) to a forced scale factor applied AFTER every other rule — wins over
    blackslist/filters. Empty/None = canonical behavior.
    """
    squad_map: dict[str, int] = {}
    ebp_map: dict[str, int] = {}
    for module in ALL_MODULES:
        data_root = extract_root / module / "data"
        if not data_root.is_dir():
            continue
        for rgd in sorted(data_root.rglob("*.rgd")):
            if "sbps" not in str(rgd).replace("\\", "/"):
                continue
            try:
                aegd = extract_aegd(rgd)
            except Exception:
                continue
            eff = effective_scale_for(rgd.name, aegd, squad_scale, policy,
                                      exclude_single_model, exclude_sp,
                                      descale_campaign_single, module)
            if races is not None and eff > 0:
                rel = str(rgd.relative_to(data_root)).replace("\\", "/")
                seg = rel.split("/sbps/races/")
                race = seg[1].split("/")[0] if len(seg) == 2 else ""
                if race not in races:
                    eff = 0
            if squad_filter is not None and eff > 0:
                if rgd.name[:-4].lower() not in squad_filter:
                    eff = 0
            if exclude_squads is not None and eff > 0:
                if rgd.name[:-4].lower() in exclude_squads:
                    eff = 0
            if overrides:
                eff = overrides.get(rgd.name[:-4].lower(), eff)
            squad_map[(module, rgd.name)] = eff
            for ebp in squad_loadout_ebp_refs(aegd):
                # The EBP cost divisor must match the model-count scale of the
                # squads that spawn it. Use MAX across all referencing squads:
                # an excluded squad (eff 0) sharing the same EBP basename must
                # not prevent a scaled squad (eff 5) from getting its cost
                # counter-scaled. (min was wrong: a single excluded _sp variant
                # sharing the EBP zeroed the divisor -> scaled vehicles like the
                # Chimera shipped at 5x cost/time.)
                key = (module, ebp)
                if key not in ebp_map:
                    ebp_map[key] = eff
                elif eff > ebp_map[key]:
                    ebp_map[key] = eff
    return squad_map, ebp_map


def find_squad_reinforce_cost_offsets(aegd: bytes) -> list[tuple[int, str]]:
    """AEGD-relative offsets of every float under squad_reinforce_ext.cost.
    Returns (offset, kind) where kind is 'requisition', 'population' or 'other'."""
    d = Decoder(aegd)
    out: list[tuple[int, str]] = []
    top = d._table(12)
    if top is None:
        return out
    for kh, typ, vabs in top[1]:
        if typ != 100 or kh != SQUAD_REINFORCE:
            continue
        re = d._table(vabs)
        if re is None:
            continue
        for kh2, typ2, vabs2 in re[1]:
            if typ2 == 100 and kh2 == COST_FIELD:
                sub = d._table(vabs2)
                if sub is None:
                    continue
                stack = [sub]
                while stack:
                    t = stack.pop()
                    for kh3, typ3, vabs3 in t[1]:
                        if typ3 == 0:
                            if kh3 == REQUISITION:
                                kind = "requisition"
                            elif kh3 == POPULATION:
                                kind = "population"
                            else:
                                kind = "other"
                            out.append((vabs3, kind))
                        elif typ3 == 100:
                            s3 = d._table(vabs3)
                            if s3 is not None:
                                stack.append(s3)
    return out


def patch_ebp_cost(path: Path, divisor: int) -> bytes | None:
    """Divide every cost_ext float in a unit EBP by divisor (counter-scale the
    per-model build cost & time)."""
    if divisor <= 1:
        return None
    orig = path.read_bytes()
    size = struct.unpack_from("<I", orig, 0x24)[0]
    aegd = orig[AEGD_OFF:AEGD_OFF + size]
    d = Decoder(aegd)
    offs: list[int] = []

    def walk(abs_table: int) -> None:
        t = d._table(abs_table)
        if t is None:
            return
        for kh, typ, vabs in t[1]:
            if typ == 0:
                foff = AEGD_OFF + vabs
                if foff + 4 <= len(orig):
                    offs.append(foff)
            elif typ == 100:
                walk(vabs)

    found = False
    for kh, typ, vabs in d._table(12)[1]:
        if typ == 100 and kh == COST_EXT:
            found = True
            walk(vabs)
    if not found or not offs:
        return None
    data = bytearray(orig)
    for foff in offs:
        cur = struct.unpack_from("<f", data, foff)[0]
        if cur != 0.0:
            struct.pack_into("<f", data, foff, cur / divisor)
    return bytes(data)


def find_unit_offsets(aegd: bytes) -> dict[str, int]:
    """Return AEGD-relative offsets of the squad_loadout_ext unit_min/unit_max floats."""
    d = Decoder(aegd)
    out: dict[str, int] = {}
    top = d._table(12)
    if top is None:
        return out
    for kh, typ, vabs in top[1]:
        if typ != 100 or kh != SQUAD_LOADOUT:
            continue
        tbl = d._table(vabs)
        if tbl is None:
            continue
        for kh2, typ2, vabs2 in tbl[1]:
            if typ2 != 0:
                continue
            if kh2 == UNIT_MIN:
                out["unit_min"] = vabs2
            elif kh2 == UNIT_MAX:
                out["unit_max"] = vabs2
    return out


def patch_squad_rgd(path: Path, max_cap: float = MAX_CAP, squad_scale: int = 0,
                    scale_model_count: bool = True, scale_costs: bool = True,
                    scale_unit_min: bool = True, scale_unit_max: bool = True) -> bytes | None:
    """Return a patched copy of a squad .rgd.

    Always raises `required_squad_cap` `max_squad_cap` to max_cap. When
    squad_scale > 0, also multiplies squad_loadout_ext unit_min/unit_max by it
    (if scale_model_count), and divides squad_reinforce_ext cost/time by it (if
    scale_costs), so the per-model build cost and time stay vanilla while the
    model count grows.
    Returns None if the squad has no required_squad_cap (and thus no patch).

    `squad_scale` is the *effective* scale factor for this squad (0 = do not
    scale), already resolved by the caller via `effective_scale_for` / the
    active can-attach policy. Model-count exclusions are therefore encoded in
    the caller; this function only applies the factor it is given.
    """
    orig = path.read_bytes()
    size = struct.unpack_from("<I", orig, 0x24)[0]
    aegd = orig[AEGD_OFF:AEGD_OFF + size]
    offsets = find_max_squad_cap_offsets(aegd)
    if not offsets and squad_scale <= 0:
        return None
    data = bytearray(orig)
    for off in offsets:
        struct.pack_into("<f", data, AEGD_OFF + off, max_cap)
    if squad_scale > 0:
        if scale_model_count:
            for name, off in find_unit_offsets(aegd).items():
                if name == "unit_min" and not scale_unit_min:
                    continue
                if name == "unit_max" and not scale_unit_max:
                    continue
                foff = AEGD_OFF + off
                if foff + 4 > len(data):
                    continue
                cur = struct.unpack_from("<f", data, foff)[0]
                if cur > 0:
                    struct.pack_into("<f", data, foff, cur * squad_scale)
        if scale_costs:
            # counter-scale the per-model build/reinforce cost & time so totals stay vanilla
            for off, kind in find_squad_reinforce_cost_offsets(aegd):
                foff = AEGD_OFF + off
                if foff + 4 > len(data):
                    continue
                cur = struct.unpack_from("<f", data, foff)[0]
                if cur > 0:
                    new = cur / squad_scale
                    if kind == "requisition" and new < REINFORCE_FLOOR:
                        new = REINFORCE_FLOOR
                    if kind == "population" and new < POPULATION_FLOOR:
                        # waaagh (ork population) reinforce costs must never drop
                        # below 1.0 waaagh per reinforce tick
                        new = POPULATION_FLOOR
                    struct.pack_into("<f", data, foff, new)
    patched = bytes(data)
    # sanity: re-decode the patched AEGD and confirm caps were rewritten
    paegd = patched[AEGD_OFF:AEGD_OFF + size]
    if offsets and sorted(find_max_squad_cap_offsets(paegd)) != sorted(offsets):
        raise RuntimeError(f"offset map changed after patch: {path}")
    for off in offsets:
        if struct.unpack_from("<f", paegd, off)[0] != max_cap:
            raise RuntimeError(f"patch verification failed at {path} offset {off:#x}")
    return patched


def to_deploy_path(rgd_path: Path, extract_root: Path, module: str) -> str:
    """Convert an extracted .rgd path into the game-root-relative deploy path."""
    rel = rgd_path.relative_to(extract_root / module / "data")
    parts = [p.replace("\\", "/") for p in rel.parts]
    return f"{module}/Data/{'/'.join(parts)}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("extract_root", type=Path, help="extraction tree (with DXP2/data, DXP3/data)")
    ap.add_argument("mod_root", type=Path, nargs="?", default=Path(__file__).parent.parent / "mod")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--squad-scale", type=int, default=0,
                    help="multiply every squad's unit_min/unit_max by N (0 = off)")
    ap.add_argument("--can-attach-policy", choices=CAN_ATTACH_POLICIES, default="scale",
                    help="how to treat squad_can_attach_ext squads (default: scale, "
                         "the v0.4.0 behavior; use skip/skip-hg/scale2 for diagnostics)")
    ap.add_argument("--weapon-cap-boost", choices=("auto", "on", "off"), default="off",
                    help="whether to include the Over40000_BoostWeaponCaps block in "
                         "setup.scar (default off: the WC block crashed the game "
                         "(nil Squad_GetUpgradeMax * 4 on 432/866 squads) and was "
                         "dropped from the recommended build; auto = on when "
                         "--squad-scale > 0, else off; on = force include)")
    ap.add_argument("--setup-template", type=Path, default=None,
                    help="alternate setup.scar template file (default: "
                         "templates/setup.scar; use templates/setup.wc-guard.scar for "
                         "the nil-guarded weapon-cap boost)")
    ap.add_argument("--resource-cheat", choices=("on", "off"), default="on",
                    help="whether to include the resource cheat (starting 40001 "
                         "requisition/power + x10 income + +400000 bank cap) in "
                         "setup.scar (default on; off ships vanilla setup.scar for "
                         "normal resources)")
    ap.add_argument("--scale-model-count", choices=("on", "off"), default="on",
                    help="whether to multiply squad unit_min/unit_max by squad_scale "
                         "(default on; off keeps model counts vanilla)")
    ap.add_argument("--scale-unit-min", choices=("on", "off"), default="on",
                    help="whether to scale unit_min (initial squad size) when "
                         "--scale-model-count is on (default on)")
    ap.add_argument("--scale-unit-max", choices=("on", "off"), default="on",
                    help="whether to scale unit_max (max reinforce size) when "
                         "--scale-model-count is on (default on)")
    ap.add_argument("--scale-costs", choices=("on", "off"), default="on",
                    help="whether to counter-scale per-model costs (squad reinforce "
                         "cost AND unit EBP cost_ext) by squad_scale "
                         "(default on; off keeps costs vanilla)")
    ap.add_argument("--modules", default=",".join(ALL_MODULES),
                    help="comma-separated list of modules to patch data for "
                         "(default: W40k,WXP,DXP2,DXP3). Used to isolate which "
                         "module's edits break a campaign.")
    ap.add_argument("--exclude-single-model", choices=("on", "off"), default="off",
                    help="when on, squads whose original unit_max is 1.0 (single-model "
                         "vehicles/heroes/NPCs/civilians) are NOT model-count scaled "
                         "in W40k/WXP (base-game validator rejects them). "
                         "DXP2/DXP3 unaffected. Default off.")
    ap.add_argument("--exclude-sp", choices=("on", "off"), default="off",
                    help="when on, squads with '_sp' in their filename (single-player "
                         "campaign variants) are NOT model-count scaled "
                         "(caps still patched). Default off.")
    ap.add_argument("--descale-campaign-single", choices=("on", "off"), default="off",
                    help="when on, single-model squads in DXP2/DXP3 with a "
                         "campaign-only name marker (_advance_sp, _sp, _veteran_sp, "
                         "_hg) are NOT model-count scaled. These are campaign army / "
                         "honor-guard variants spawned at mission start with min "
                         "loadout (scaling them freezes the SIM, e.g. Wraithlord HG "
                         "in Tau Stronghold). Skirmish single-model squads still "
                         "scale. Default off.")
    ap.add_argument("--races", default="",
                    help="comma-separated list of race dirs to model-count scale "
                         "(e.g. space_marines,orks). Empty = all races. Caps still "
                         "patched for all. Used to isolate which race's scaling "
                         "breaks a campaign.")
    ap.add_argument("--squads-file", type=Path, default=None,
                    help="file with one squad basename (no .rgd) per line; when set, "
                         "ONLY those squads are model-count scaled (caps still "
                         "patched for all). Complements --races; used to isolate "
                         "campaign-referenced squads.")
    ap.add_argument("--blacklist-file", type=Path, default=None,
                    help="path to a squad-scaling blacklist (one basename per line, "
                         "no .rgd). When set, this REPLACES the default git-controlled "
                         "blacklist (scripts/templates/squads.blacklist.txt). The "
                         "default is always applied unless this override is passed, "
                         "so `make build` is deterministic.")
    ap.add_argument("--scale-overrides", default="",
                    help="comma-separated SQUAD_BASENAME=factor overrides applied "
                         "AFTER every other scaling rule (e.g. "
                         "necron_tomb_spyder_squad=0,necron_scarab_squad=50). "
                         "EXPERIMENTAL/diagnostic only — never used for a formal "
                         "release (AGENTS.md hard rule 15). Empty = no overrides, "
                         "canonical behavior.")
    args = ap.parse_args()
    modules = tuple(m.strip() for m in args.modules.split(",") if m.strip())
    for m in modules:
        if m not in ALL_MODULES:
            raise SystemExit(f"error: unknown module '{m}' (allowed: {', '.join(ALL_MODULES)})")
    race_filter: set[str] | None = None
    if args.races:
        race_filter = set(r.strip() for r in args.races.split(",") if r.strip())
    squad_filter: set[str] | None = None
    if args.squads_file is not None:
        squad_filter = set(
            ln.strip().removesuffix(".rgd").lower()
            for ln in args.squads_file.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        )
    exclude_squads: set[str] | None = None
    blacklist_src = args.blacklist_file if args.blacklist_file is not None else TEMPLATES / "squads.blacklist.txt"
    if blacklist_src.is_file():
        exclude_squads = set(
            ln.strip().removesuffix(".rgd").lower()
            for ln in blacklist_src.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.lstrip().startswith("#")
        )

    # Experimental per-squad scale overrides (squad basename -> factor). Applied
    # AFTER every other rule in collect_scale_maps. Empty by default: canonical
    # builds are unaffected (AGENTS.md hard rule 15).
    scale_overrides: dict[str, int] = {}
    for tok in (t.strip() for t in args.scale_overrides.split(",") if t.strip()):
        name, sep, factor = tok.partition("=")
        if not sep:
            raise SystemExit(f"error: bad --scale-overrides token '{tok}' (expected NAME=factor)")
        try:
            scale_overrides[name.strip().lower()] = int(factor)
        except ValueError:
            raise SystemExit(f"error: bad --scale-overrides factor '{factor}' in '{tok}'")

    # ---- setup.scar (cheat hook) ----
    if args.resource_cheat == "off":
        # no resource cheat: ship vanilla setup.scar (normal resources). The WC
        # block only exists in the cheat template, so nothing else to strip.
        scar_src = args.setup_template or (TEMPLATES / "setup.nocheat.scar")
    else:
        scar_src = args.setup_template or (TEMPLATES / "setup.scar")
    scar_dst = args.mod_root / "W40k" / "Data" / "scar" / "setup.scar"
    if args.dry_run:
        print(f"would write {scar_dst}")
    else:
        text = scar_src.read_text(encoding="utf-8")
        # the weapon-cap boost is tied to the experimental squad-scale feature by
        # default (auto); explicit --weapon-cap-boost on/off decouples them so the
        # WC block can be isolated from squad scaling in diagnostic variants
        wc_include = args.weapon_cap_boost
        if wc_include == "auto":
            wc_include = "on" if args.squad_scale > 0 else "off"
        if wc_include == "off":
            while True:
                begin = text.find("--[[OVER40000:WC_BEGIN]]")
                end = text.find("--[[OVER40000:WC_END]]")
                if begin == -1 or end == -1 or end < begin:
                    break
                end_line = text.find("\n", end)
                text = text[:begin] + text[end_line + 1:]
        text = text.replace("\n", "\r\n")
        scar_dst.parent.mkdir(parents=True, exist_ok=True)
        scar_dst.write_text(text, encoding="ascii", newline="")
        print(f"wrote {scar_dst}")

    # ---- race cap files (population/vehicle caps -> RACE_CAP) ----
    race_total = 0
    for module in modules:
        data_root = args.extract_root / module / "data"
        if not data_root.is_dir():
            print(f"warning: {data_root} not found, skipping {module}", file=sys.stderr)
            continue
        for rgd in sorted(data_root.rglob("*.rgd")):
            if "racebps" not in str(rgd).replace("\\", "/"):
                continue
            patched = patch_race_caps(rgd)
            if patched is None:
                continue
            deploy = to_deploy_path(rgd, args.extract_root, module)
            dst = args.mod_root / deploy
            if args.dry_run:
                print(f"would write {dst}")
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(patched)
                print(f"wrote {dst}")
            race_total += 1
    print(f"TOTAL patched race files: {race_total}")

    # ---- ork waaagh banner (resource-cheat variant only: +4000 waaagh per banner) ----
    banner_total = 0
    if args.resource_cheat == "on":
        for module in modules:
            data_root = args.extract_root / module / "data"
            if not data_root.is_dir():
                continue
            for rgd in sorted(data_root.rglob("*.rgd")):
                if rgd.name != "ork_waagh_banner.rgd" or "ebps" not in str(rgd).replace("\\", "/"):
                    continue
                patched = patch_banner_pop_cap(rgd)
                if patched is None:
                    continue
                deploy = to_deploy_path(rgd, args.extract_root, module)
                dst = args.mod_root / deploy
                if args.dry_run:
                    print(f"would write {dst}")
                else:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    dst.write_bytes(patched)
                    print(f"wrote {dst}")
                banner_total += 1
        print(f"TOTAL patched ork banner files: {banner_total}")

    # ---- unit EBP per-model cost/time counter-scale (when squad_scale > 0) ----
    ebp_total = 0
    if args.squad_scale > 0 and args.scale_costs == "on":
        _, ebp_scale_map = collect_scale_maps(args.extract_root, args.squad_scale,
                                              args.can_attach_policy,
                                              args.exclude_single_model == "on",
                                              args.exclude_sp == "on",
                                              args.descale_campaign_single == "on",
                                              race_filter, squad_filter, exclude_squads,
                                              scale_overrides)
        for module in modules:
            data_root = args.extract_root / module / "data"
            if not data_root.is_dir():
                continue
            for rgd in sorted(data_root.rglob("*.rgd")):
                rel = str(rgd).replace("\\", "/")
                if "ebps/races" not in rel or "/troops/" not in rel:
                    continue
                divisor = ebp_scale_map.get((module, rgd.name), args.squad_scale)
                if divisor <= 1:
                    continue
                patched = patch_ebp_cost(rgd, divisor)
                if patched is None:
                    continue
                deploy = to_deploy_path(rgd, args.extract_root, module)
                dst = args.mod_root / deploy
                if args.dry_run:
                    print(f"would write {dst}")
                else:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    dst.write_bytes(patched)
                ebp_total += 1
        print(f"TOTAL patched unit EBP costs: {ebp_total}")

    # ---- squad unit-limit / scale overrides (patched .rgd) ----
    total = 0
    squad_scale_map, _ = collect_scale_maps(args.extract_root, args.squad_scale,
                                            args.can_attach_policy,
                                            args.exclude_single_model == "on",
                                            args.exclude_sp == "on",
                                            args.descale_campaign_single == "on",
                                            race_filter, squad_filter, exclude_squads,
                                            scale_overrides)
    for module in modules:
        data_root = args.extract_root / module / "data"
        if not data_root.is_dir():
            print(f"warning: {data_root} not found, skipping {module}", file=sys.stderr)
            continue
        for rgd in sorted(data_root.rglob("*.rgd")):
            if "sbps" not in str(rgd).replace("\\", "/"):
                continue
            eff = squad_scale_map.get((module, rgd.name), args.squad_scale)
            patched = patch_squad_rgd(rgd, squad_scale=eff,
                                      scale_model_count=args.scale_model_count == "on",
                                      scale_costs=args.scale_costs == "on",
                                      scale_unit_min=args.scale_unit_min == "on",
                                      scale_unit_max=args.scale_unit_max == "on")
            if patched is None:
                continue
            deploy = to_deploy_path(rgd, args.extract_root, module)
            dst = args.mod_root / deploy
            if args.dry_run:
                print(f"would write {dst}")
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(patched)
                print(f"wrote {dst}")
            total += 1
    print(f"TOTAL patched squad files: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
