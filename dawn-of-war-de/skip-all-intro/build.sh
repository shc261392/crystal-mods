#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# skip-all-intro - DoW DE skip-all-intro movies mod - build (Linux / WSL2)
#
# Generates the 0-byte replacement movies into mod/ and packages a
# Vortex-installable zip into dist/.
#
# Usage: bash build.sh [--version 0.1.0]
# ---------------------------------------------------------------------------
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

VERSION="0.1.0"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --version) VERSION="$2"; shift 2 ;;
        *) echo "Unknown arg: $1" >&2; exit 2 ;;
    esac
done

PKG_NAME="skip-all-intro-v$VERSION"

echo "== skip-all-intro - DoW DE build (Linux/WSL2) =="
echo "  version: $VERSION"

# 1. Generate the replacement movies into mod/.
rm -rf mod
python3 scripts/generate_movies.py mod

# 2. Package the Vortex zip.
rm -rf "dist/$PKG_NAME" "dist/$PKG_NAME.zip"
mkdir -p "dist/$PKG_NAME"
cp -r mod/Engine mod/DXP2 mod/DXP3 "dist/$PKG_NAME/"
cd "dist/$PKG_NAME" && zip -r "../$PKG_NAME.zip" . -x "*.DS_Store" >/dev/null && cd "$REPO_ROOT"
echo "✓ dist/$PKG_NAME.zip"
echo "  Size: $(du -sh "dist/$PKG_NAME.zip" | cut -f1)"
echo "  Files: $(find "dist/$PKG_NAME" -type f | wc -l)"
