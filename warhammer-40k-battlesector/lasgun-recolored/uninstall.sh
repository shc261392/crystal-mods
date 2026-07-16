#!/usr/bin/env bash
# =============================================================================
# uninstall.sh — restore the most recent backup created by deploy.sh (Linux/WSL2)
# Usage: bash uninstall.sh [--game-dir PATH] [--stamp YYYYMMDD-HHMMSS]
# If you installed via Vortex, just purge/remove the mod instead (auto-restore).
# =============================================================================
set -euo pipefail
RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; RESET='\033[0m'
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GAME_DIR=""; STAMP=""
BACKUP_DIR="${REPO_ROOT}/backup"
GAME_FOLDER_NAME="Warhammer 40K Battlesector"
DATA_SUBPATH="Warhammer 40K Battlesector_Data/StreamingAssets"

log()  { printf "${CYAN}▶${RESET} %s\n" "$*"; }
ok()   { printf "${GREEN}✓${RESET} %s\n" "$*"; }
die()  { printf "${RED}✗${RESET}  %s\n" "$*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --game-dir) GAME_DIR="$2"; shift 2;;
    --stamp) STAMP="$2"; shift 2;;
    *) die "Unknown option: $1";;
  esac
done

if [[ -z "$GAME_DIR" ]]; then
  for base in \
    "$HOME/.steam/steam/steamapps/common" \
    "$HOME/.local/share/Steam/steamapps/common" \
    "/mnt/c/Program Files (x86)/Steam/steamapps/common" \
    "/mnt/d/SteamLibrary/steamapps/common"; do
    [[ -d "$base/$GAME_FOLDER_NAME" ]] && { GAME_DIR="$base/$GAME_FOLDER_NAME"; break; }
  done
fi
[[ -n "$GAME_DIR" && -d "$GAME_DIR" ]] || die "Game directory not found. Use --game-dir PATH."

[[ -z "$STAMP" ]] && STAMP="$(ls -1 "$BACKUP_DIR" 2>/dev/null | sort | tail -1 || true)"
[[ -n "$STAMP" && -d "$BACKUP_DIR/$STAMP" ]] || die "No backup found in $BACKUP_DIR."
ok "Restoring backup: $STAMP"

# Restore every bundle that was backed up in this stamp.
DEPLOY_FILES=()
while IFS= read -r -d '' f; do DEPLOY_FILES+=("$(basename "$f")"); done \
  < <(find "$BACKUP_DIR/$STAMP" -maxdepth 1 -name '*.bundle' -print0)

for f in "${DEPLOY_FILES[@]}"; do
  bak="$BACKUP_DIR/$STAMP/$f"
  [[ -f "$bak" ]] || { log "No backup for $f, skipping"; continue; }
  log "Restore $f"
  cp -p "$bak" "$GAME_DIR/$DATA_SUBPATH/$f"
done
ok "Vanilla files restored."
