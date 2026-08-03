#!/usr/bin/env bash
# The Great Crusade — manual deploy (Linux / Proton / WSL).
# Extracts the chosen variant ZIP's bundle into the game folder, backing up the
# original once. Prefer installing via Vortex; this is for manual installs.
#
# Usage:
#   ./deploy.sh <path-to-variant-zip> [GAME_DIR]
# Env:
#   BS_GAME_DIR  default game folder if [GAME_DIR] not given.
set -euo pipefail

ZIP="${1:-}"
GAME_DIR="${2:-${BS_GAME_DIR:-/mnt/d/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector}}"
REL="Warhammer 40K Battlesector_Data/StreamingAssets/startup_assets_all.bundle"

if [[ -z "$ZIP" || ! -f "$ZIP" ]]; then
  echo "usage: ./deploy.sh <path-to-variant-zip> [GAME_DIR]" >&2
  echo "  e.g. ./deploy.sh dist/the-great-crusade-exp-x4-levels-15-v0.1.0.zip" >&2
  exit 2
fi
TARGET="$GAME_DIR/$REL"
if [[ ! -d "$GAME_DIR" ]]; then
  echo "game folder not found: $GAME_DIR" >&2; exit 2
fi

BAK="$TARGET.the-great-crusade.bak"
if [[ -f "$TARGET" && ! -f "$BAK" ]]; then
  cp -f "$TARGET" "$BAK"
  echo "backed up original -> $(basename "$BAK")"
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
unzip -o -q "$ZIP" "$REL" -d "$TMP"
cp -f "$TMP/$REL" "$TARGET"
echo "deployed $(basename "$ZIP") -> $TARGET"
