#!/usr/bin/env bash
# =============================================================================
# deploy.sh — WH40K Battlesector Traditional Chinese Localization deployer
#
# Supports:
#   • Linux (native Steam + Proton)
#   • WSL2 (Windows Subsystem for Linux — accesses Windows paths via /mnt/c ...)
#
# Usage:
#   bash deploy.sh [--game-dir PATH] [--dry-run] [--no-backup]
#
# What it does:
#   1. Auto-detect the game installation directory
#   2. Create a timestamped backup of existing sharedassets1.assets
#   3. Copy pre-built sharedassets1.assets to Warhammer 40K Battlesector_Data/
#   4. Verify deployment integrity
#
# Notes:
#   - sharedassets1.assets is a pre-built, pre-tested asset bundle
#   - In-game: select Chinese (Simplified) to display Traditional Chinese
#
# Run: make deploy  —OR—  bash deploy.sh
# =============================================================================
set -euo pipefail

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

# ── Script location = repo root ───────────────────────────────────────────────
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Defaults ─────────────────────────────────────────────────────────────────
GAME_DIR=""
DRY_RUN=false
NO_BACKUP=false
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="${REPO_ROOT}/backup"
MANIFEST_FILE="${BACKUP_DIR}/deploy_manifest_${STAMP}.txt"

# ── Game folder name (case-insensitive search) ────────────────────────────────
GAME_FOLDER_NAME="Warhammer 40K Battlesector"

# ── Files to deploy (pre-built asset) ──────────────────────────────────────
DEPLOY_FILES=(sharedassets1.assets)

# ── Target sub-path inside game root ─────────────────────────────────────────
DATA_SUBPATH="Warhammer 40K Battlesector_Data"

# ─────────────────────────────────────────────────────────────────────────────
log()   { printf "${CYAN}▶${RESET} %s\n" "$*"; }
ok()    { printf "${GREEN}✓${RESET} %s\n" "$*"; }
warn()  { printf "${YELLOW}⚠${RESET}  %s\n" "$*"; }
err()   { printf "${RED}✗${RESET}  %s\n" "$*" >&2; }
die()   { err "$*"; exit 1; }

# ─────────────────────────────────────────────────────────────────────────────
usage() {
    cat <<EOF
Usage: bash deploy.sh [OPTIONS]

Options:
  --game-dir PATH   Override auto-detected game installation directory
  --dry-run         Show what would be deployed without writing anything
  --no-backup       Skip backup step (not recommended)
  --help            Show this help message

Environment:
  WH40K_BS_GAME_DIR   Alternative to --game-dir (env var)
EOF
}

# ─────────────────────────────────────────────────────────────────────────────
# Argument parsing
# ─────────────────────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case $1 in
        --game-dir)  GAME_DIR="$2"; shift 2 ;;
        --dry-run)   DRY_RUN=true; shift ;;
        --no-backup) NO_BACKUP=true; shift ;;
        --help|-h)   usage; exit 0 ;;
        *) die "Unknown option: $1 (use --help)" ;;
    esac
done

# Allow env-var override
[[ -z "$GAME_DIR" && -n "${WH40K_BS_GAME_DIR:-}" ]] && GAME_DIR="$WH40K_BS_GAME_DIR"

# ─────────────────────────────────────────────────────────────────────────────
# Steam library discovery
# ─────────────────────────────────────────────────────────────────────────────

# Convert a Windows-style VDF path to a WSL2 accessible path.
# e.g. "D:\\SteamLibrary" -> "/mnt/d/SteamLibrary"
_win_to_wsl() {
    local p="$1"
    # VDF uses \\ (double backslash) as path separator — replace pairs with /
    p="${p//\\\\/\/}"
    # Convert leading drive letter  D:/ -> /mnt/d/
    if [[ "$p" =~ ^([A-Za-z]):(/.*)$ ]]; then
        p="/mnt/${BASH_REMATCH[1],,}${BASH_REMATCH[2]}"
    fi
    echo "$p"
}

# Enumerate Steam library roots from libraryfolders.vdf
_steam_library_roots() {
    local vdf_candidates=()

    # Native Linux / Proton paths
    vdf_candidates+=(
        "$HOME/.steam/steam/steamapps/libraryfolders.vdf"
        "$HOME/.local/share/Steam/steamapps/libraryfolders.vdf"
        "$HOME/snap/steam/common/.local/share/Steam/steamapps/libraryfolders.vdf"
        "$HOME/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/libraryfolders.vdf"
    )

    # WSL2: scan common Windows drive mounts (C–G)
    for drv in c d e f g; do
        vdf_candidates+=(
            "/mnt/${drv}/Program Files (x86)/Steam/steamapps/libraryfolders.vdf"
            "/mnt/${drv}/SteamLibrary/steamapps/libraryfolders.vdf"
        )
    done

    for vdf in "${vdf_candidates[@]}"; do
        [[ -f "$vdf" ]] || continue
        while IFS= read -r raw; do
            if [[ "$raw" =~ ^[A-Za-z]: ]]; then
                _win_to_wsl "$raw"
            else
                echo "$raw"
            fi
        done < <(sed -nE 's/.*"path"\s+"([^"]+)".*/\1/p' "$vdf")
    done
}

# Find game directory by scanning Steam libraries
_find_game() {
    local roots; roots=($(_steam_library_roots))
    
    for root in "${roots[@]}"; do
        local candidate="$root/steamapps/common/$GAME_FOLDER_NAME"
        if [[ -d "$candidate" ]]; then
            echo "$candidate"
            return 0
        fi
    done
    return 1
}

# ─────────────────────────────────────────────────────────────────────────────
# Main deployment logic
# ─────────────────────────────────────────────────────────────────────────────

printf "\n"
echo "╭─ WH40K Battlesector — TC Localization Deployer ─────────────────╮"
echo "│ Repo root: $REPO_ROOT"
echo "╰───────────────────────────────────────────────────────────────────╯"
printf "\n"

if $DRY_RUN; then warn "[DRY RUN — no files will be written]"; fi

# 1. Resolve game directory
if [[ -z "$GAME_DIR" ]]; then
    log "Auto-detecting game installation..."
    if GAME_DIR=$(_find_game); then
        ok "Found: $GAME_DIR"
    else
        die "Could not auto-detect game directory. Set WH40K_BS_GAME_DIR or use --game-dir PATH"
    fi
fi

# Verify game directory exists
if [[ ! -d "$GAME_DIR" ]]; then
    die "Game directory does not exist: $GAME_DIR"
fi

# 2. Verify data directory
DATA_DIR="$GAME_DIR/$DATA_SUBPATH"
if [[ ! -d "$DATA_DIR" ]]; then
    die "Game data folder not found: $DATA_DIR"
fi
ok "Game data folder: $DATA_DIR"

# 3. Verify source files exist
log "Checking deployment files..."
for f in "${DEPLOY_FILES[@]}"; do
    src="$REPO_ROOT/dist/$f"
    if [[ ! -f "$src" ]]; then
        die "Source file not found: $src"
    fi
    ok "Ready: $f"
done

# 4. Create backup
if [[ "$NO_BACKUP" != "true" ]]; then
    log "Creating backup..."
    mkdir -p "$BACKUP_DIR"
    for f in "${DEPLOY_FILES[@]}"; do
        orig="$DATA_DIR/$f"
        if [[ -f "$orig" ]]; then
            backup="$BACKUP_DIR/${f%.assets}.${STAMP}.assets.backup"
            if $DRY_RUN; then
                log "[DRY] Would backup: $orig → $backup"
            else
                cp "$orig" "$backup"
                ok "Backed up: ${f%.assets}.*"
            fi
        fi
    done
    echo "$STAMP" > "$MANIFEST_FILE"
fi

# 5. Deploy files
log "Deploying files..."
for f in "${DEPLOY_FILES[@]}"; do
    src="$REPO_ROOT/dist/$f"
    dst="$DATA_DIR/$f"
    if $DRY_RUN; then
        log "[DRY] Would copy: $src → $dst"
    else
        cp "$src" "$dst"
        ok "Deployed: $f"
    fi
done

# 6. Verify
if ! $DRY_RUN; then
    log "Verifying deployment..."
    for f in "${DEPLOY_FILES[@]}"; do
        dst="$DATA_DIR/$f"
        if [[ -f "$dst" ]]; then
            ok "Verified: $f"
        else
            die "Deployment failed: $f not found at $dst"
        fi
    done
fi

printf "\n"
if $DRY_RUN; then
    echo "╭─ DRY RUN COMPLETE ───────────────────────────────────────────╮"
else
    echo "╭─ DEPLOYMENT COMPLETE ────────────────────────────────────────╮"
fi
echo "│                                                                  │"
echo "│ ✓ In-game: Select Chinese (Simplified) for Traditional Chinese   │"
echo "│ ✓ Backup location: $BACKUP_DIR"
echo "│                                                                  │"
echo "╰──────────────────────────────────────────────────────────────────╯"
printf "\n"
