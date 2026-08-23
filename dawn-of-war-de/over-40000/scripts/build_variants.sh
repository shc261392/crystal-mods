#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Build the four diagnostic test variants of "Over 40000" (v0.4.0 experimental)
# used to isolate the Haemonculus Honor Guard crash.
#
# Each variant is a self-contained Vortex ZIP in dist/ named clearly so the
# human tester can install exactly one at a time. Deployment to the game folder
# is NEVER done by this script (per repo rules) — the user installs manually.
#
# Variants:
#   A  noscale       -- squad-scale OFF (baseline, v0.3.0-like behaviour)
#   B  skip-canattach-- scale ON, but never scale squads with squad_can_attach_ext
#   C  skip-hg-attach-- scale ON, skip only *_hg* variants with squad_can_attach_ext
#   D  attach-2x     -- scale ON, squad_can_attach_ext squads scaled x2 instead of x5
#   E  nowc          -- scale ON x5 (v0.4.0), weapon-cap boost OFF (isolate WC block)
#   F  wc-only       -- scale OFF, weapon-cap boost ON  (isolate scaling)
#   G  wc-guard      -- v0.4.0 + nil-guarded WC block (proposed fix test)
#
# Usage (from the over-40000/ directory):
#   scripts/build_variants.sh [EXTRACT_ROOT]
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
EXTRACT_ROOT="${1:-$ROOT/../.copilot_workspace/extract}"
DIST="$ROOT/dist"
STAGE="$(mktemp -d "${TMPDIR:-/tmp}/ov4k-variants.XXXXXX")"
trap 'rm -rf "$STAGE"' EXIT

PY="$ROOT/scripts/generate_mod.py"

build_variant() {
  local label="$1"; shift
  local mod_root="$STAGE/mod-$label"
  echo "── building variant $label ──────────────────────────────"
  python3 "$PY" "$EXTRACT_ROOT" "$mod_root" "$@"
  # package into dist as a Vortex zip (W40k/WXP/DXP2/DXP3 subtrees)
  local pkg="$DIST/over-40000-v0.4.0-$label"
  rm -rf "$pkg" "$pkg.zip"
  mkdir -p "$pkg"
  cp -r "$mod_root"/W40k "$mod_root"/WXP "$mod_root"/DXP2 "$mod_root"/DXP3 "$pkg/"
  write_readme "$label" "$pkg"
  ( cd "$pkg" && zip -rq "../over-40000-v0.4.0-$label.zip" . )
  echo "✓ dist/over-40000-v0.4.0-$label.zip"
}

write_readme() {
  local label="$1" pkg="$2"
  cat > "$pkg/README-TEST.txt" <<EOF
Over 40000 -- diagnostic test variant: $label
==============================================
This is a TEST build used to isolate the Haemonculus Honor Guard crash
(reproduced in v0.4.0 experimental with squad scaling x5).

What this variant does:
EOF
  case "$label" in
    A-noscale)
      cat >> "$pkg/README-TEST.txt" <<EOF
  - Squad model-count scaling: OFF (v0.3.0-like baseline, control)
  - squad_can_attach_ext squads: unscaled
  - Weapon-cap boost (setup.scar): OFF
  Expected: no crash (matches v0.3.0). This is the control.
EOF
      ;;
    B-skip-canattach)
      cat >> "$pkg/README-TEST.txt" <<EOF
  - Squad model-count scaling: ON (x5)
  - squad_can_attach_ext squads: NEVER scaled (all 131 excluded)
  - Weapon-cap boost: ON
  Test: if no crash, scaling attachable command units is the trigger.
        If crash, the cause is NOT can_attach scaling (check WC boost /
        race caps / another scaled squad).
EOF
      ;;
    C-skip-hg-attach)
      cat >> "$pkg/README-TEST.txt" <<EOF
  - Squad model-count scaling: ON (x5)
  - squad_can_attach_ext squads: HG variants (_hg*) excluded, base ones scaled
        (Haemonculus HG stays 1/1; normal Haemonculus, Force Commander etc. x5)
  - Weapon-cap boost: ON
  Test: if no crash building the Haemonculus HG -> HG-specific.
        If crash -> the problem is not HG-specific (affects any attachable
        command unit, e.g. normal Haemonculus scaled to 5).
EOF
      ;;
    D-attach-2x)
      cat >> "$pkg/README-TEST.txt" <<EOF
  - Squad model-count scaling: ON (x5), but squad_can_attach_ext squads x2
        (Haemonculus HG / normal Haemonculus become 2 models, not 5)
  - Weapon-cap boost: ON
  Test: if no crash -> scale factor matters (2 is OK, 5 is not).
        If crash -> even 2 models breaks the attach state machine.
EOF
      ;;
    E-nowc)
      cat >> "$pkg/README-TEST.txt" <<EOF
  - Squad model-count scaling: ON (x5), can-attach squads excluded (same as B)
  - Weapon-cap boost: OFF (WC block stripped from setup.scar)
  Test: identical to variant B except the WC block is absent. If NO crash ->
        the WC block (Over40000_BoostWeaponCaps, fires every 5s) is the crash
        trigger, NOT squad scaling. If crash -> squad scaling / EBP cost
        division alone is the trigger.
EOF
      ;;
    F-wc-only)
      cat >> "$pkg/README-TEST.txt" <<EOF
  - Squad model-count scaling: OFF (v0.3.0-like, no unit_min/unit_max change)
  - EBP cost division: OFF
  - Weapon-cap boost: ON (WC block present in setup.scar, fires every 5s)
  Test: if crash -> the WC block alone is sufficient to crash.
        If NO crash -> WC is necessary but not sufficient; crash needs the
        combination with squad scaling.
EOF
      ;;
    G-wc-guard)
      cat >> "$pkg/README-TEST.txt" <<EOF
  - Squad model-count scaling: ON (x5), same as v0.4.0 / variant B
  - Weapon-cap boost: ON but nil-guarded (squads without squad_reinforce_ext
        max_upgrades are skipped, so Squad_GetUpgradeMax nil cannot crash)
  Test: proposed FIX. If NO crash building a Haemonculus HG / other squads ->
        the guard fixes the WC block; the feature can ship with the guard.
        If crash -> guard insufficient; drop the WC block entirely.
EOF
      ;;
  esac
  cat >> "$pkg/README-TEST.txt" <<EOF

Installation: install in Vortex, enable, launch Soulstorm, build a
Haemonculus Honor Guard and watch for the 3-6s crash.
EOF
}

mkdir -p "$DIST"

# A: baseline, no squad scaling (v0.3.0-like). Note: setup.scar weapon-cap
#    boost is stripped automatically when --squad-scale is 0.
build_variant "A-noscale" --squad-scale 0

# B: scale ON (x5), but exclude every squad_can_attach_ext squad.
build_variant "B-skip-canattach" --squad-scale 5 --can-attach-policy skip

# C: scale ON (x5), exclude only *_hg* variants that have squad_can_attach_ext.
build_variant "C-skip-hg-attach" --squad-scale 5 --can-attach-policy skip-hg

# D: scale ON (x5 globally), but squad_can_attach_ext squads get x2 instead.
build_variant "D-attach-2x" --squad-scale 5 --can-attach-policy scale2

# E: identical to B (scale x5, skip can-attach) but WC block stripped ->
#    isolates the WC boost from squad scaling. If E does not crash while B
#    does, the WC block is the trigger.
build_variant "E-nowc" --squad-scale 5 --can-attach-policy skip --weapon-cap-boost off

# F: no scaling but WC block present -> isolates squad scaling.
build_variant "F-wc-only" --squad-scale 0 --weapon-cap-boost on

# G: v0.4.0 scaling + nil-guarded WC block -> proposed fix test.
build_variant "G-wc-guard" --squad-scale 5 --can-attach-policy skip --setup-template "$ROOT/scripts/templates/setup.wc-guard.scar"

echo "── done ──────────────────────────────────────────────────"
ls -la "$DIST"/over-40000-v0.4.0-*.zip