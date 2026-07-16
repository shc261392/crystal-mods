#!/usr/bin/env python3
"""
"""build.py — Lasgun Recolored mod builder (Warhammer 40,000: Battlesector).

Produces patched Unity asset bundles from your VANILLA game bundles, writing
them into ./payload/ laid out at their game-root-relative paths so the Vortex
extension (or the deploy scripts) can drop them straight into the game.

This script NEVER writes to your game directory. It only READS the vanilla
bundles you point it at and WRITES patched copies into ./payload/.

DEFAULT = COLOUR / FX ONLY. The Lasgun's stats are left at vanilla values.
  - Projectile colour: warm yellow/orange -> red
    (recolours the lasgun bolt + muzzle flash + flare FX: Lights, ParticleSystem
    start colours, colour-over-lifetime gradients, TrailRenderer gradients, and
    all 'lasgun' materials. These FX are shared across AM las weapons, so those
    also turn red.)

OPTIONAL stat changes (opt-in with --stats, requires --startup). These edit the
Astra Militarum standard Lasgun (weapon id 7010). Values live in STAT_PATCH
below — edit them there, then rebuild with --stats:
    STAT_PATCH = {"Attacks": 50, "Damage": 8.0, "ArmourPenetration": 2}
  (Attacks = shots per attack; vanilla is Attacks 4 / Damage 4 / AP 1.)

Usage:
  # Colour / FX only (default, shipped build):
  python build.py --am-faction /path/to/StreamingAssets/faction-astramilitarum_assets_all.bundle

  # Also apply the optional stat changes:
  python build.py \
      --am-faction /path/to/StreamingAssets/faction-astramilitarum_assets_all.bundle \
      --stats --startup /path/to/StreamingAssets/startup_assets_all.bundle

Requires: UnityPy (pip install UnityPy).
"""
from __future__ import annotations

import argparse
import os
import sys

import UnityPy

# ---------------------------------------------------------------------------
# Constants (verified against Battlesector 1.7.4 / Unity 6000.0f1, IL2CPP)
# ---------------------------------------------------------------------------
WEAPON_TABLE_PATH_ID = 297598000547913130      # WeaponDataTable in startup bundle
TARGET_WEAPON = 7010                            # Astra Militarum standard Lasgun
STAT_PATCH = {"Attacks": 50, "Damage": 8.0, "ArmourPenetration": 2}

PROJECTILE_ROOT_NAMES = (
    "FX_WPN_AM_LasGunProjectile",  # the bolt (light + trail)
    "FX_WPN_LasGunMuzzleFlash",    # muzzle flash + flare at the barrel
)
# All lasgun FX materials are tinted by name so the whole firing effect (bolt,
# muzzle flash, flare, hit disperse) reads red rather than orange.
LASGUN_MATERIAL_SUBSTR = "lasgun"

# Target red. Defaults chosen to fight ACES tonemapping (which shifts very bright
# reds toward orange): a deep red with a touch of blue, and a capped HDR
# brightness. Both are overridable from the CLI (--red, --emission-cap).
RED = (1.0, 0.0, 0.10)     # r,g,b ratio (green kept at 0)
EMISSION_CAP = 1.2         # clamp material colour/emission magnitude to this

REL_STREAMING = os.path.join("Warhammer 40K Battlesector_Data", "StreamingAssets")


# ---------------------------------------------------------------------------
def patch_stats(startup_path: str, out_path: str) -> None:
    print(f"[stats] loading {startup_path}")
    env = UnityPy.load(startup_path)
    obj = next(
        o for o in env.objects
        if o.type.name == "MonoBehaviour" and o.path_id == WEAPON_TABLE_PATH_ID
    )
    tree = obj.read_typetree()
    keys = list(tree["keys"])
    idx = keys.index(TARGET_WEAPON)
    wpn = tree["values"][idx]
    before = {k: wpn[k] for k in STAT_PATCH}
    for k, v in STAT_PATCH.items():
        wpn[k] = v
    obj.save_typetree(tree)
    after = {k: wpn[k] for k in STAT_PATCH}
    print(f"[stats] weapon {TARGET_WEAPON}: {before} -> {after}")
    data = env.file.save(packer="original")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"[stats] wrote {out_path} ({len(data):,} bytes)")


# ---------------------------------------------------------------------------
def _collect_hierarchy(env, root_go_path_id):
    """Return the set of GameObject path_ids in the transform subtree of root."""
    # Build GameObject.path_id -> Transform, and Transform.path_id -> tree
    transforms = {}
    go_of_transform = {}
    for o in env.objects:
        if o.type.name in ("Transform", "RectTransform"):
            t = o.read_typetree()
            transforms[o.path_id] = t
            go_of_transform[o.path_id] = t.get("m_GameObject", {}).get("m_PathID")
    # Find root's transform
    root_transform_pid = None
    for tpid, t in transforms.items():
        if go_of_transform.get(tpid) == root_go_path_id:
            root_transform_pid = tpid
            break
    if root_transform_pid is None:
        return {root_go_path_id}
    result_go = set()
    stack = [root_transform_pid]
    while stack:
        tpid = stack.pop()
        t = transforms.get(tpid)
        if not t:
            continue
        gopid = go_of_transform.get(tpid)
        if gopid is not None:
            result_go.add(gopid)
        for child in t.get("m_Children", []):
            cpid = child.get("m_PathID")
            if cpid in transforms:
                stack.append(cpid)
    return result_go


def _apply_red(c, cap=None):
    """Set an RGBA colour dict to the target red, preserving alpha. If cap is
    given, the colour's brightness (max channel) is clamped to cap; otherwise
    the original brightness is preserved. Returns True if it changed."""
    if not isinstance(c, dict):
        return False
    r, g, b = RED
    mag = max(c.get("r", 0.0), c.get("g", 0.0), c.get("b", 0.0))
    if mag <= 0.0:
        mag = 1.0
    if cap is not None:
        mag = min(mag, cap)
    c["r"], c["g"], c["b"] = mag * r, mag * g, mag * b
    return True


def _recolor_gradient(grad):
    """Recolour all key* entries of a Unity gradient dict to red (keep alpha)."""
    changed = False
    if not isinstance(grad, dict):
        return False
    for k, v in grad.items():
        if k.startswith("key") and isinstance(v, dict):
            changed |= _apply_red(v)
    return changed


def _recolor_minmax(mm, cap=None):
    """Recolour a Unity MinMaxColor/MinMaxGradient dict: minColor/maxColor and
    minGradient/maxGradient key entries."""
    changed = False
    if not isinstance(mm, dict):
        return False
    for key in ("minColor", "maxColor"):
        if key in mm:
            changed |= _apply_red(mm[key], cap)
    for key in ("minGradient", "maxGradient"):
        if key in mm:
            changed |= _recolor_gradient(mm[key])
    return changed


def _tint_materials(env, material_pids):
    """Tint colour properties of lasgun materials to red, clamping brightness to
    EMISSION_CAP so bright HDR reds do not tonemap to orange. A material is
    tinted if it is referenced by an FX renderer (material_pids) OR its name
    contains 'lasgun'. Returns the number of materials modified."""
    # Properties that visibly drive the effect colour. Others (dither,
    # projection, UV, timescale) are left alone.
    color_props = ("_Color", "_TintColor", "_EmissionColor", "_BaseColor")
    count = 0
    for o in env.objects:
        if o.type.name != "Material":
            continue
        tree = o.read_typetree()
        name = tree.get("m_Name", "")
        if o.path_id not in material_pids and LASGUN_MATERIAL_SUBSTR not in name.lower():
            continue
        props = tree.get("m_SavedProperties", {})
        changed = False
        for prop_name, c in props.get("m_Colors", []):
            if prop_name not in color_props or not isinstance(c, dict):
                continue
            changed |= _apply_red(c, cap=EMISSION_CAP)
        if changed:
            o.save_typetree(tree)
            count += 1
    return count


def recolor_projectile(am_path: str, out_path: str) -> None:
    print(f"[color] loading {am_path}")
    env = UnityPy.load(am_path)

    # Find all target root GameObjects (projectile + muzzle flash), union their
    # transform hierarchies.
    subtree: set[int] = set()
    for o in env.objects:
        if o.type.name != "GameObject":
            continue
        try:
            if o.read().m_Name in PROJECTILE_ROOT_NAMES:
                subtree |= _collect_hierarchy(env, o.path_id)
        except Exception:
            pass
    if not subtree:
        print("[color] ERROR: lasgun FX GameObjects not found; skipping")
        return
    print(f"[color] FX hierarchies contain {len(subtree)} GameObjects")

    lights = ps = trails = 0
    material_pids: set[int] = set()  # materials referenced by FX renderers
    RENDERERS = ("MeshRenderer", "ParticleSystemRenderer", "TrailRenderer",
                 "SkinnedMeshRenderer", "SpriteRenderer")
    for o in env.objects:
        t = o.type.name
        if t not in ("Light", "ParticleSystem", "TrailRenderer") + RENDERERS:
            continue
        tree = o.read_typetree()
        go_pid = tree.get("m_GameObject", {}).get("m_PathID")
        if go_pid not in subtree:
            continue
        # Collect materials referenced by any renderer in the hierarchy
        if t in RENDERERS:
            for m in tree.get("m_Materials", []) or []:
                pid = m.get("m_PathID") if isinstance(m, dict) else None
                if pid:
                    material_pids.add(pid)
        if t == "Light":
            _apply_red(tree.get("m_Color", {}))
            o.save_typetree(tree)
            lights += 1
        elif t == "ParticleSystem":
            # Recolour the start colour AND the colour-over-lifetime gradient,
            # both of which can carry orange in vanilla.
            _recolor_minmax(tree.get("InitialModule", {}).get("startColor", {}))
            colmod = tree.get("ColorModule", {})
            if colmod.get("enabled"):
                _recolor_minmax(colmod.get("gradient", {}))
            o.save_typetree(tree)
            ps += 1
        elif t == "TrailRenderer":
            grad = tree.get("m_Parameters", {}).get("colorGradient", {})
            _recolor_gradient(grad)
            o.save_typetree(tree)
            trails += 1

    # Tint every lasgun FX material by name (bolt trail, muzzle flash, flare, hit
    # disperse). These are shared across all AM las weapons -> those also turn
    # red, as requested ("full red").
    mats = _tint_materials(env, material_pids)
    print(f"[color] recoloured Lights={lights} ParticleSystems={ps} "
          f"TrailRenderers={trails} Materials={mats}")

    data = env.file.save(packer="original")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"[color] wrote {out_path} ({len(data):,} bytes)")


# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(
        description="Build Lasgun Recolored payload (colour/FX by default)")
    ap.add_argument("--am-faction", required=True,
                    help="path to vanilla faction-astramilitarum_assets_all.bundle "
                         "(the projectile/FX recolour target)")
    ap.add_argument("--red", default=None,
                    help="projectile red as 'R,G,B' (0-1). Default 1,0,0.10 "
                         "(slight blue counters ACES orange shift)")
    ap.add_argument("--emission-cap", type=float, default=None,
                    help="clamp material colour/emission brightness (default 1.2). "
                         "Lower this if the bolt still tonemaps to orange")
    ap.add_argument("--stats", action="store_true",
                    help="ALSO apply the (optional) stat changes to the Lasgun. "
                         "Off by default: this mod is colour/FX only. Requires "
                         "--startup. See STAT_PATCH in this file / the README to "
                         "customise the values.")
    ap.add_argument("--startup", default=None,
                    help="path to vanilla startup_assets_all.bundle "
                         "(only needed with --stats)")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "payload"),
                    help="output payload root (default: ./payload)")
    args = ap.parse_args()

    global RED, EMISSION_CAP
    if args.red:
        parts = [float(x) for x in args.red.split(",")]
        if len(parts) != 3:
            print("ERROR: --red must be 'R,G,B'", file=sys.stderr)
            return 2
        RED = tuple(parts)
    if args.emission_cap is not None:
        EMISSION_CAP = args.emission_cap
    print(f"[cfg] RED={RED} EMISSION_CAP={EMISSION_CAP} stats={args.stats}")

    stream_out = os.path.join(args.out, REL_STREAMING)

    # Colour / FX recolour — the default (and only) behaviour of this mod.
    recolor_projectile(
        args.am_faction,
        os.path.join(stream_out, "faction-astramilitarum_assets_all.bundle"),
    )

    # Optional stat changes (opt-in). Off by default so the shipped mod is
    # colour/FX only and leaves the Lasgun's vanilla stats untouched.
    if args.stats:
        if not args.startup:
            print("ERROR: --stats requires --startup", file=sys.stderr)
            return 2
        patch_stats(args.startup,
                    os.path.join(stream_out, "startup_assets_all.bundle"))
    else:
        print("[stats] skipped (colour/FX-only build; pass --stats to enable)")

    print("\nDONE. Payload ready at:", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
