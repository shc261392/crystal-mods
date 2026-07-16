#!/usr/bin/env bash
# =============================================================================
# package.sh — build a Vortex-installable zip from the built payload.
#
# The zip contains files at their game-root-relative paths
# (Warhammer 40K Battlesector_Data/StreamingAssets/*.bundle), which the repo's
# Battlesector Vortex extension deploys directly (Layout A).
#
# Usage: bash package.sh          # zips whatever is in ./payload
# =============================================================================
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAYLOAD="${REPO_ROOT}/payload"
DIST="${REPO_ROOT}/dist"
VER="$(python3 -c "import json,sys;print(json.load(open('${REPO_ROOT}/modinfo.json'))['version'])" 2>/dev/null || echo 0.1.0)"
OUT="${DIST}/lasgun-recolored-v${VER}.zip"

[[ -d "$PAYLOAD/Warhammer 40K Battlesector_Data" ]] || { echo "No payload found. Run build.py first." >&2; exit 1; }
mkdir -p "$DIST"
rm -f "$OUT"

( cd "$PAYLOAD" && zip -r -9 "$OUT" "Warhammer 40K Battlesector_Data" )
echo "Created: $OUT"
ls -la "$OUT"
