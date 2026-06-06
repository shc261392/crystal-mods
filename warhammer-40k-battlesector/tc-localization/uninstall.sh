#!/usr/bin/env bash
# =============================================================================
# uninstall.sh — WH40K Battlesector TC Localization uninstaller
#
# Restores the original sharedassets1.assets from backup
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${REPO_ROOT}/backup"
GAME_FOLDER_NAME="Warhammer 40K Battlesector"
DATA_SUBPATH="Warhammer 40K Battlesector_Data"

log()   { printf "${CYAN}▶${RESET} %s\n" "$*"; }
ok()    { printf "${GREEN}✓${RESET} %s\n" "$*"; }
warn()  { printf "${YELLOW}⚠${RESET}  %s\n" "$*"; }
err()   { printf "${RED}✗${RESET}  %s\n" "$*" >&2; }
die()   { err "$*"; exit 1; }

# Find most recent backup
_find_latest_backup() {
    if [[ ! -d "$BACKUP_DIR" ]]; then
        return 1
    fi
    
    local latest
    latest=$(ls -t "$BACKUP_DIR"/sharedassets1.*.assets.backup 2>/dev/null | head -1)
    if [[ -n "$latest" ]]; then
        echo "$latest"
        return 0
    fi
    return 1
}

# Find game directory
_find_game() {
    local vdf_candidates=(
        "$HOME/.steam/steam/steamapps/libraryfolders.vdf"
        "$HOME/.local/share/Steam/steamapps/libraryfolders.vdf"
    )
    
    for drv in c d e f g; do
        vdf_candidates+=(
            "/mnt/${drv}/Program Files (x86)/Steam/steamapps/libraryfolders.vdf"
            "/mnt/${drv}/SteamLibrary/steamapps/libraryfolders.vdf"
        )
    done

    for vdf in "${vdf_candidates[@]}"; do
        [[ -f "$vdf" ]] || continue
        while IFS= read -r root; do
            [[ -z "$root" ]] && continue
            local candidate="$root/steamapps/common/$GAME_FOLDER_NAME"
            if [[ -d "$candidate" ]]; then
                echo "$candidate"
                return 0
            fi
        done < <(sed -nE 's/.*"path"\s+"([^"]+)".*/\1/p' "$vdf" | tr '\\' '/')
    done
    return 1
}

printf "\n"
echo "╭─ WH40K Battlesector — TC Localization Uninstaller ────────────╮"
echo "│ Repo root: $REPO_ROOT"
echo "╰──────────────────────────────────────────────────────────────────╯"
printf "\n"

# Find backup
log "Looking for backup..."
if ! BACKUP_FILE=$(_find_latest_backup); then
    die "No backup found in $BACKUP_DIR"
fi
ok "Found backup: $(basename "$BACKUP_FILE")"

# Find game directory
log "Auto-detecting game installation..."
if ! GAME_DIR=$(_find_game); then
    die "Could not auto-detect game directory. Set WH40K_BS_GAME_DIR or use deploy.sh again"
fi
ok "Found: $GAME_DIR"

# Verify paths
DATA_DIR="$GAME_DIR/$DATA_SUBPATH"
if [[ ! -d "$DATA_DIR" ]]; then
    die "Game data folder not found: $DATA_DIR"
fi

CURRENT_MOD="$DATA_DIR/sharedassets1.assets"
if [[ ! -f "$CURRENT_MOD" ]]; then
    warn "No mod file found at: $CURRENT_MOD"
    die "Nothing to uninstall"
fi

# Restore backup
log "Restoring original sharedassets1.assets..."
cp "$BACKUP_FILE" "$CURRENT_MOD"
ok "Restored: sharedassets1.assets"

# Verify
if [[ -f "$CURRENT_MOD" ]]; then
    ok "Verified: Original file restored"
else
    die "Restore failed: $CURRENT_MOD"
fi

printf "\n"
echo "╭─ UNINSTALL COMPLETE ─────────────────────────────────────────╮"
echo "│                                                                │"
echo "│ ✓ Original sharedassets1.assets restored                       │"
echo "│ ✓ Backup kept at: $BACKUP_DIR"
echo "│                                                                │"
echo "╰──────────────────────────────────────────────────────────────────╯"
printf "\n"
