#!/usr/bin/env bash
# The Great Crusade — restore the vanilla bundle backed up by deploy.sh.
# Usage: ./uninstall.sh [GAME_DIR]
set -euo pipefail
GAME_DIR="${1:-${BS_GAME_DIR:-/mnt/d/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector}}"
REL="Warhammer 40K Battlesector_Data/StreamingAssets/startup_assets_all.bundle"
TARGET="$GAME_DIR/$REL"
BAK="$TARGET.the-great-crusade.bak"

if [[ -f "$BAK" ]]; then
  mv -f "$BAK" "$TARGET"
  echo "restored original bundle from backup"
else
  echo "no backup found ($BAK); nothing to restore" >&2
  exit 1
fi
