#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Over 40000 - DoW DE power-cheat mod - build (Linux / WSL2)
#
# Auto-detects the Dawn of War Definitive Edition install (or use DOW_GAME_DIR /
# --game-dir), extracts the game data if needed, regenerates mod/ and builds the
# Vortex-installable zip into dist/.
#
# Experimental features (revert by building without these flags):
#   --squad-scale N    multiply every squad's unit_min/unit_max by N
#
# Usage: bash build.sh [--game-dir PATH] [--extract-root PATH] [--squad-scale N] [--resource-cheat on|off]
# ---------------------------------------------------------------------------
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

GAME_DIR="${DOW_GAME_DIR:-}"
EXTRACT_ROOT="${EXTRACT_ROOT:-../.copilot_workspace/extract}"
SQUAD_SCALE=5
RESOURCE_CHEAT=on
VERSION="0.1.3"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --game-dir) GAME_DIR="$2"; shift 2 ;;
        --extract-root) EXTRACT_ROOT="$2"; shift 2 ;;
        --squad-scale) SQUAD_SCALE="$2"; shift 2 ;;
        --resource-cheat) RESOURCE_CHEAT="$2"; shift 2 ;;
        *) echo "Unknown arg: $1" >&2; exit 2 ;;
    esac
done

if [[ "$RESOURCE_CHEAT" == "off" ]]; then
    PKG_NAME="over-40000-v${VERSION}-normal-resources"
else
    PKG_NAME="over-40000-v$VERSION"
fi

echo "== Over 40000 - DoW DE build (Linux/WSL2) =="
echo "  version: $VERSION   squad-scale: $SQUAD_SCALE   resource-cheat: $RESOURCE_CHEAT"

GAME_ARGS=("--extract-root" "$EXTRACT_ROOT")
[[ -n "$GAME_DIR" ]] && GAME_ARGS+=("--game-dir" "$GAME_DIR")

# 1. Ensure the game data is extracted (auto-detect game dir if not given).
python3 scripts/ensure_extract.py "${GAME_ARGS[@]}"

# 2. Regenerate the mod tree.
GEN_ARGS=("--squad-scale" "$SQUAD_SCALE" "--resource-cheat" "$RESOURCE_CHEAT" "--exclude-single-model" "on" "--descale-campaign-single" "on")
python3 scripts/generate_mod.py "$EXTRACT_ROOT" mod "${GEN_ARGS[@]}"

# 3. Package the Vortex zip.
rm -rf "dist/$PKG_NAME" "dist/$PKG_NAME.zip"
mkdir -p "dist/$PKG_NAME"
cp -r mod/W40k mod/WXP mod/DXP2 mod/DXP3 "dist/$PKG_NAME/"
cd "dist/$PKG_NAME" && zip -r "../$PKG_NAME.zip" . -x "*.DS_Store" >/dev/null && cd "$REPO_ROOT"
echo "✓ dist/$PKG_NAME.zip"
echo "  Size: $(du -sh "dist/$PKG_NAME.zip" | cut -f1)"
echo "  Files: $(find "dist/$PKG_NAME" -type f | wc -l)"
