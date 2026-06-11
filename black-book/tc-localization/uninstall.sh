#!/usr/bin/env bash
# Black Book — Traditional Chinese Localization Mod
# Uninstall script for Linux / WSL2
#
# Purpose:
#   Removes deployed TC localization asset files and optionally restores from backup
#
# Usage:
#   bash uninstall.sh [--no-restore] [--force]

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MOD_DIR="$SCRIPT_DIR"
STEAM_APP_ID="1138660"

GAME_DIR=""
BACKUP_DIR="$MOD_DIR/backup"
RESTORE_BACKUP=true
FORCE=false

# ============================================================================
# Utility Functions
# ============================================================================

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

error() {
  echo "[ERROR] $*" >&2
  exit 1
}

warn() {
  echo "[WARN] $*" >&2
}

# ============================================================================
# Steam Path Detection
# ============================================================================

find_game_in_steam() {
  local steam_root="$1"
  
  local steam_paths=(
    "$steam_root/steamapps/common/Black Book"
    "$steam_root/steamapps/common/black-book"
  )
  
  for path in "${steam_paths[@]}"; do
    if [[ -f "$path/Black Book.exe" ]]; then
      echo "$path"
      return 0
    fi
  done
  
  return 1
}

locate_game() {
  log "Locating Black Book..."
  
  local steam_roots=(
    "$HOME/.steam/steam"
    "$HOME/.steam/root"
    "$HOME/.local/share/Steam"
    "/mnt/c/Program Files (x86)/Steam"
    "/mnt/d/SteamLibrary"
    "C:/Program Files (x86)/Steam"
    "D:/SteamLibrary"
  )
  
  for steam_root in "${steam_roots[@]}"; do
    if [[ -d "$steam_root" ]]; then
      if local game=$(find_game_in_steam "$steam_root"); then
        log "Found game at: $game"
        echo "$game"
        return 0
      fi
    fi
  done
  
  error "Black Book not found in Steam library"
}

# ============================================================================
# Uninstall
# ============================================================================

remove_deployed_files() {
  local game_path="$1"
  
  log "Removing deployed TC localization files..."
  
  # Remove the entire StreamingAssets/Config (will be restored from backup)
  local config_path="$game_path/Black Book_Data/StreamingAssets/Config"
  if [[ -d "$config_path" ]]; then
    rm -rf "$config_path"
    log "  ✓ Removed StreamingAssets/Config (will be restored from backup)"
  fi
  
  # Remove fonts if they were deployed
  local fonts_path="$game_path/Fonts"
  if [[ -d "$fonts_path" ]] && [[ -f "$fonts_path/NotoSansTC.asset" ]]; then
    rm -f "$fonts_path/NotoSansTC.asset"
    log "  ✓ Removed NotoSansTC.asset"
  fi
  
  log "✓ Deployed files removed"
}

restore_from_backup() {
  local game_path="$1"
  
  if [[ "$RESTORE_BACKUP" == false ]]; then
    log "Skipping backup restoration (--no-restore)"
    log "WARNING: Game config files are missing. Restart game or verify Steam installation."
    return 0
  fi
  
  # Check for saved backup path first
  if [[ -f "$MOD_DIR/.last_backup_path" ]]; then
    local latest_backup=$(cat "$MOD_DIR/.last_backup_path")
    if [[ ! -d "$latest_backup" ]]; then
      latest_backup=""
    fi
  fi
  
  # If no saved path, find the most recent backup
  if [[ -z "$latest_backup" ]]; then
    latest_backup=$(ls -td "$BACKUP_DIR"/game_backup_* 2>/dev/null | head -1)
  fi
  
  if [[ -z "$latest_backup" ]] || [[ ! -d "$latest_backup" ]]; then
    error "No backup found! Cannot safely restore game files. Manually verify game integrity via Steam."
  fi
  
  log "Restoring from backup: $latest_backup"
  
  # Restore Config directory
  if [[ -d "$latest_backup/Config_original" ]]; then
    mkdir -p "$(dirname "$game_path/Black Book_Data/StreamingAssets/Config")"
    cp -r "$latest_backup/Config_original" "$game_path/Black Book_Data/StreamingAssets/Config" || \
      error "Failed to restore Config directory"
    log "  ✓ Config directory restored"
  fi
  
  # Restore resources directory if it exists
  if [[ -d "$latest_backup/resources_original" ]]; then
    mkdir -p "$(dirname "$game_path/Black Book_Data/resources")"
    cp -r "$latest_backup/resources_original" "$game_path/Black Book_Data/resources" || \
      warn "Failed to restore resources directory"
    log "  ✓ Resources restored"
  fi
  
  log "✓ Restoration complete"
  log ""
  log "Game has been restored to its original state."
  log "To verify game integrity, run: steam steam://validate/1138660"
}

# ============================================================================
# Main
# ============================================================================

main() {
  # Parse arguments
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --no-restore)
        RESTORE_BACKUP=false
        shift
        ;;
      --force)
        FORCE=true
        shift
        ;;
      *)
        error "Unknown option: $1"
        ;;
    esac
  done
  
  log "Black Book — Traditional Chinese Localization Uninstaller"
  log ""
  
  # Locate game
  GAME_DIR=$(locate_game)
  
  # Uninstall
  remove_deployed_files "$GAME_DIR"
  restore_from_backup "$GAME_DIR"
  
  log ""
  log "=========================================="
  log "Uninstall complete!"
  log "=========================================="
  log ""
  log "Black Book has been restored to its original state."
  log ""
}

main "$@"
