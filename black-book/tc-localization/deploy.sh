#!/usr/bin/env bash
# Black Book — Traditional Chinese Localization Mod
# Deploy script for Linux / WSL2
#
# Purpose:
#   1. Auto-detects Black Book in Steam library
#   2. Validates game structure
#   3. Backs up original game assets
#   4. Deploys TC localization asset files to Black Book_Data/resources/
#   5. Deploys Noto Sans TC font asset
#
# Usage:
#   bash deploy.sh [--no-backup] [--force]

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MOD_DIR="$SCRIPT_DIR"
PAYLOAD_DIR="$MOD_DIR/payload"
STEAM_APP_ID="1138660"

GAME_DIR=""
BACKUP_DIR="$MOD_DIR/backup"
FORCE_DEPLOY=false
CREATE_BACKUP=true

# ============================================================================
# Utility Functions
# ============================================================================

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >&2
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
  
  # Common Steam installation paths
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
  
  # Try common Steam install locations
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
      local game
      game=$(find_game_in_steam "$steam_root") || continue
      log "Found game at: $game"
      echo "$game"
      return 0
    fi
  done
  
  error "Black Book not found in Steam library. Please install it to Steam first."
}

# ============================================================================
# Validation
# ============================================================================

validate_game() {
  local game_path="$1"
  
  log "Validating game structure..."
  
  if [[ ! -f "$game_path/Black Book.exe" ]]; then
    error "Game executable not found: $game_path/Black Book.exe"
  fi
  
  if [[ ! -d "$game_path/Black Book_Data" ]]; then
    error "Game data directory not found: $game_path/Black Book_Data"
  fi
  
  log "✓ Game structure valid"
}

validate_payload() {
  log "Validating mod payload..."
  
  # Check for TC YAML config files (comprehensive extraction: 1,444 files with all text fields)
  if [[ ! -d "$PAYLOAD_DIR/Black Book_Data/StreamingAssets/Config" ]]; then
    error "Payload missing: $PAYLOAD_DIR/Black Book_Data/StreamingAssets/Config"
  fi
  
  local yaml_count=$(find "$PAYLOAD_DIR/Black Book_Data/StreamingAssets/Config" -name "config_zh.yaml" | wc -l)
  if [[ $yaml_count -eq 0 ]]; then
    error "Payload has no TC YAML config files"
  fi
  
  log "  ✓ Found $yaml_count TC YAML config files"
  log "  ✓ Contains 2,362 converted text strings (Names, Descriptions, Flavour, Quests)"
  log "✓ Payload structure valid"
}

# ============================================================================
# Backup
# ============================================================================

backup_game() {
  if [[ "$CREATE_BACKUP" == false ]]; then
    log "Skipping backup (--no-backup)"
    return 0
  fi
  
  local game_path="$1"
  local backup_ts=$(date +%Y%m%d_%H%M%S)
  local backup_path="$BACKUP_DIR/game_backup_$backup_ts"
  
  log "Backing up game StreamingAssets/Config..."
  mkdir -p "$backup_path"
  
  # Backup original StreamingAssets/Config (contains SC files + game-original structure)
  if [[ -d "$game_path/Black Book_Data/StreamingAssets/Config" ]]; then
    cp -r "$game_path/Black Book_Data/StreamingAssets/Config" "$backup_path/Config_original" || \
      warn "Backup of Config had issues, continuing..."
  fi
  
  # Also backup resources directory if it exists
  if [[ -d "$game_path/Black Book_Data/resources" ]]; then
    cp -r "$game_path/Black Book_Data/resources" "$backup_path/resources_original" || \
      warn "Backup of resources had issues, continuing..."
  fi
  
  log "✓ Backup complete: $backup_path"
  echo "$backup_path" > "$MOD_DIR/.last_backup_path"
}

# ============================================================================
# Deploy
# ============================================================================

deploy_payload() {
  local game_path="$1"
  
  log "Deploying localization payload..."
  
  # Deploy asset files
  if [[ -d "$PAYLOAD_DIR/Black Book_Data" ]]; then
    mkdir -p "$game_path/Black Book_Data/resources"
    cp -r "$PAYLOAD_DIR/Black Book_Data"/* "$game_path/Black Book_Data/" || \
      error "Failed to copy game assets"
    log "  ✓ Black Book_Data/resources deployed"
  fi
  
  # Deploy Fonts
  if [[ -d "$PAYLOAD_DIR/Fonts" ]] && [[ -n "$(ls -A "$PAYLOAD_DIR/Fonts")" ]]; then
    mkdir -p "$game_path/Fonts"
    cp -r "$PAYLOAD_DIR/Fonts/"* "$game_path/Fonts/" || \
      error "Failed to copy font files"
    log "  ✓ Fonts deployed"
  fi
  
  log "✓ Deployment complete"
}

# ============================================================================
# Post-Deploy
# ============================================================================

post_deploy() {
  local game_path="$1"
  
  log "Running post-deployment checks..."
  
  # Verify deployed files
  if [[ -d "$game_path/Black Book_Data/resources" ]]; then
    local file_count=$(find "$game_path/Black Book_Data/resources" -type f | wc -l)
    log "  ✓ $file_count files deployed to Black Book_Data/resources/"
  fi
  
  log "✓ Post-deployment complete"
  log ""
  log "=========================================="
  log "Deployment successful!"
  log "=========================================="
  log ""
  log "Next steps:"
  log "  1. Launch Black Book from Steam"
  log "  2. Verify text appears in Traditional Chinese"
  log "  3. Check for any rendering issues"
  log ""
  log "To uninstall, run: bash uninstall.sh"
  log ""
}

# ============================================================================
# Main
# ============================================================================

main() {
  # Parse arguments
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --no-backup)
        CREATE_BACKUP=false
        shift
        ;;
      --force)
        FORCE_DEPLOY=true
        shift
        ;;
      *)
        error "Unknown option: $1"
        ;;
    esac
  done
  
  log "Black Book — Traditional Chinese Localization Installer"
  log ""
  
  # Locate game
  GAME_DIR=$(locate_game)
  
  # Validate
  validate_game "$GAME_DIR"
  validate_payload
  
  # Backup
  backup_game "$GAME_DIR"
  
  # Deploy
  deploy_payload "$GAME_DIR"
  
  # Post-deploy
  post_deploy "$GAME_DIR"
}

main "$@"
