#!/usr/bin/env bash
# Black Book — Traditional Chinese Localization Mod
# Uninstall script for Linux / WSL2 / Git Bash
#
# Restores the game's own Simplified Chinese config_zh.yaml files. No backup
# is required: source/sc/ contains them byte-for-byte, which is also the
# input the build converts from.
#
# Usage:
#   bash uninstall.sh [--dry-run] [--game-path PATH]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR/source/sc/StreamingAssets/Config"
DRY_RUN=false
GAME_DIR="${GAME_PATH:-}"

log()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >&2; }
error() { echo "[ERROR] $*" >&2; exit 1; }

# Every write to the game folder must go through this. Never bypass it.
restore_file() {
  if [[ "$DRY_RUN" == true ]]; then
    echo "      DRY-RUN: would restore ${2#"$GAME_DIR"/}"
  else
    mkdir -p "$(dirname "$2")"
    cp -f "$1" "$2"
  fi
}

STEAM_ROOTS=(
  "$HOME/.steam/steam"
  "$HOME/.steam/root"
  "$HOME/.local/share/Steam"
  "/mnt/c/Program Files (x86)/Steam"
  "/mnt/c/Program Files/Steam"
  "/mnt/d/SteamLibrary"
  "/mnt/e/SteamLibrary"
  "/mnt/g/SteamLibrary"
)

locate_game() {
  if [[ -n "$GAME_DIR" ]]; then
    [[ -d "$GAME_DIR/Black Book_Data" ]] || error "Not a Black Book folder: $GAME_DIR"
    echo "$GAME_DIR"; return 0
  fi
  local root path
  for root in "${STEAM_ROOTS[@]}"; do
    [[ -d "$root" ]] || continue
    for path in "$root/steamapps/common/Black Book" "$root/steamapps/common/black-book"; do
      if [[ -f "$path/Black Book.exe" ]]; then
        echo "$path"; return 0
      fi
    done
  done
  error "Black Book not found. Pass --game-path or set GAME_PATH."
}

main() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --dry-run)   DRY_RUN=true; shift ;;
      --game-path) GAME_DIR="${2:?--game-path needs a value}"; shift 2 ;;
      *)           error "Unknown option: $1" ;;
    esac
  done

  log "Black Book — Traditional Chinese Localization uninstaller"
  [[ "$DRY_RUN" == true ]] && log "(dry run: nothing will be written)"

  if [[ ! -d "$SOURCE_DIR" ]]; then
    error "Restoration source not found: $SOURCE_DIR"
    error "Run 'git checkout source/sc' to restore it, or verify the game"
    error "files through Steam (right-click -> Properties -> Verify integrity)."
  fi

  GAME_DIR="$(locate_game)"
  log "Game directory: $GAME_DIR"

  local config_dir="$GAME_DIR/Black Book_Data/StreamingAssets/Config"
  [[ -d "$config_dir" ]] || error "Game config directory not found: $config_dir"

  local count
  count="$(find "$SOURCE_DIR" -name config_zh.yaml | wc -l)"
  [[ "$count" -gt 0 ]] || error "Restoration source is empty: $SOURCE_DIR"
  log "Restoring $count Simplified Chinese config file(s)..."

  while IFS= read -r -d '' rel; do
    restore_file "$SOURCE_DIR/$rel" "$config_dir/$rel"
  done < <(cd "$SOURCE_DIR" && find . -name config_zh.yaml -printf '%P\0')

  log "  ✓ $count file(s) restored to the game's original Simplified Chinese"

  # Remove the empty scratch folder an older version of this mod created.
  if [[ -d "$GAME_DIR/Black Book_Data/resources" ]]; then
    if [[ "$DRY_RUN" == true ]]; then
      echo "      DRY-RUN: would remove Black Book_Data/resources/"
    else
      rmdir "$GAME_DIR/Black Book_Data/resources" 2>/dev/null &&
        log "  ✓ removed stray empty resources/ folder"
    fi
  fi

  cat >&2 <<EOF

==========================================
Uninstall complete
==========================================

The game's own Simplified Chinese localisation is back in place.

If anything still looks wrong, verify the install through Steam:
  right-click Black Book -> Properties -> Installed Files ->
  Verify integrity of game files
EOF
}

main "$@"