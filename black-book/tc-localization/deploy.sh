#!/usr/bin/env bash
# Black Book — Traditional Chinese Localization Mod
# Install script for Linux / WSL2 / Git Bash
#
# Copies the mod's TC config_zh.yaml files over the game's Simplified Chinese
# originals. Restoration does NOT need a backup: source/sc/ holds the game's
# own Simplified Chinese files byte-for-byte, and uninstall.sh copies them back.
#
# Usage:
#   bash deploy.sh [--dry-run] [--game-path PATH]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAYLOAD_DIR="$SCRIPT_DIR/payload/Black Book_Data/StreamingAssets/Config"
STEAM_APP_ID="1138660"
DRY_RUN=false
GAME_DIR="${GAME_PATH:-}"

log()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >&2; }
error() { echo "[ERROR] $*" >&2; exit 1; }

# Every write to the game folder must go through this. Never bypass it.
install_file() {
  if [[ "$DRY_RUN" == true ]]; then
    echo "      DRY-RUN: would write ${2#"$GAME_DIR"/}"
  else
    mkdir -p "$(dirname "$2")"
    cp -f "$1" "$2"
  fi
}

# --------------------------------------------------------------------------- #
# Game discovery
# --------------------------------------------------------------------------- #

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

# --------------------------------------------------------------------------- #
# Install
# --------------------------------------------------------------------------- #

main() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --dry-run)   DRY_RUN=true; shift ;;
      --game-path) GAME_DIR="${2:?--game-path needs a value}"; shift 2 ;;
      *)           error "Unknown option: $1" ;;
    esac
  done

  log "Black Book — Traditional Chinese Localization installer"
  [[ "$DRY_RUN" == true ]] && log "(dry run: nothing will be written)"

  if [[ ! -d "$PAYLOAD_DIR" ]]; then
    error "Payload not found: $PAYLOAD_DIR — run 'make build' first."
  fi

  GAME_DIR="$(locate_game)"
  log "Game directory: $GAME_DIR"

  local config_dir="$GAME_DIR/Black Book_Data/StreamingAssets/Config"
  [[ -d "$config_dir" ]] || error "Game config directory not found: $config_dir"

  local count
  count="$(find "$PAYLOAD_DIR" -name config_zh.yaml | wc -l)"
  [[ "$count" -gt 0 ]] || error "Payload contains no config_zh.yaml files"
  log "Payload: $count Traditional Chinese config file(s)"

  # Only overwrite the Simplified Chinese localisation. Every other game file
  # (config.yaml, config_en/ja/ko.yaml, asset bundles) is left untouched.
  log "Installing..."
  while IFS= read -r -d '' rel; do
    install_file "$PAYLOAD_DIR/$rel" "$config_dir/$rel"
  done < <(cd "$PAYLOAD_DIR" && find . -name config_zh.yaml -printf '%P\0')

  log "  ✓ $count file(s) written into StreamingAssets/Config"

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
Installation complete
==========================================

Launch Black Book from Steam and check:
  - item names / descriptions in the inventory
  - ability names
  - chapter titles in the menu
  - the credits screen (Settings -> Credits)

Text that comes from Unity assets rather than config files is NOT covered by
this mod. See the "Coverage" section of README.md.

To uninstall:  bash uninstall.sh
EOF
}

main "$@"