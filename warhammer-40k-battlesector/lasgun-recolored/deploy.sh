#!/usr/bin/env bash
# =============================================================================
# deploy.sh — Lasgun Recolored deployer (Linux / WSL2)
#
# Copies the built payload bundles into the game's StreamingAssets folder,
# creating timestamped backups of the originals first.
#
# Usage: bash deploy.sh [--game-dir PATH] [--dry-run] [--no-backup]
#
# NOTE: run `python build.py ...` first to produce ./payload.
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; RESET='\033[0m'
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

GAME_DIR=""
DRY_RUN=false
NO_BACKUP=false
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="${REPO_ROOT}/backup"
GAME_FOLDER_NAME="Warhammer 40K Battlesector"
DATA_SUBPATH="Warhammer 40K Battlesector_Data/StreamingAssets"
PAYLOAD_ROOT="${REPO_ROOT}/payload/Warhammer 40K Battlesector_Data/StreamingAssets"
# Deploy whatever bundles the build produced (colour/FX only, or +stats).
DEPLOY_FILES=()
if [[ -d "$PAYLOAD_ROOT" ]]; then
  while IFS= read -r -d '' f; do DEPLOY_FILES+=("$(basename "$f")"); done \
    < <(find "$PAYLOAD_ROOT" -maxdepth 1 -name '*.bundle' -print0)
fi

log()  { printf "${CYAN}▶${RESET} %s\n" "$*"; }
ok()   { printf "${GREEN}✓${RESET} %s\n" "$*"; }
warn() { printf "${YELLOW}⚠${RESET}  %s\n" "$*"; }
die()  { printf "${RED}✗${RESET}  %s\n" "$*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --game-dir) GAME_DIR="$2"; shift 2;;
    --dry-run) DRY_RUN=true; shift;;
    --no-backup) NO_BACKUP=true; shift;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0;;
    *) die "Unknown option: $1";;
  esac
done

# Auto-detect game dir if not provided
if [[ -z "$GAME_DIR" ]]; then
  for base in \
    "$HOME/.steam/steam/steamapps/common" \
    "$HOME/.local/share/Steam/steamapps/common" \
    "/mnt/c/Program Files (x86)/Steam/steamapps/common" \
    "/mnt/d/SteamLibrary/steamapps/common" \
    "/mnt/c/SteamLibrary/steamapps/common"; do
    if [[ -d "$base/$GAME_FOLDER_NAME" ]]; then GAME_DIR="$base/$GAME_FOLDER_NAME"; break; fi
  done
fi
[[ -n "$GAME_DIR" && -d "$GAME_DIR" ]] || die "Game directory not found. Use --game-dir PATH."
ok "Game directory: $GAME_DIR"

TARGET_DIR="$GAME_DIR/$DATA_SUBPATH"
[[ -d "$TARGET_DIR" ]] || die "StreamingAssets not found at: $TARGET_DIR"

for f in "${DEPLOY_FILES[@]}"; do
  [[ -f "$PAYLOAD_ROOT/$f" ]] || die "Missing payload file: $PAYLOAD_ROOT/$f (run build.py first)"
done
[[ ${#DEPLOY_FILES[@]} -gt 0 ]] || die "No payload bundles found in $PAYLOAD_ROOT (run build.py first)."

$NO_BACKUP || mkdir -p "$BACKUP_DIR/$STAMP"
for f in "${DEPLOY_FILES[@]}"; do
  src="$PAYLOAD_ROOT/$f"
  dst="$TARGET_DIR/$f"
  if [[ "$NO_BACKUP" == false && -f "$dst" ]]; then
    log "Backup $f -> backup/$STAMP/"
    $DRY_RUN || cp -p "$dst" "$BACKUP_DIR/$STAMP/$f"
  fi
  log "Deploy $f -> $TARGET_DIR/"
  $DRY_RUN || cp -p "$src" "$dst"
done
ok "Done.${DRY_RUN:+ (dry-run)}"
$NO_BACKUP || ok "Originals backed up to: $BACKUP_DIR/$STAMP"
