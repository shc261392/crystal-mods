#!/bin/bash
# =============================================================================
# deploy_baseline.sh — Deploy original baseline (not TC mod) for bisection testing
#
# Purpose: Deploy ONLY the original unmodified files for baseline testing
# DO NOT deploy any TC mod modifications in this script
#
# Usage: bash scripts/deploy_baseline.sh
# =============================================================================
set -euo pipefail

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

# ── Script location = repo root ───────────────────────────────────────────────
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${REPO_ROOT}/backup/original-baseline"
BASELINE_ENGINE_UCS="${BACKUP_DIR}/Engine.ucs.original"

# ── Defaults ──────────────────────────────────────────────────────────────────
GAME_DIR=""

# ── Functions ─────────────────────────────────────────────────────────────────
log()   { printf "${CYAN}▶${RESET} %s\n" "$*"; }
ok()    { printf "${GREEN}✓${RESET} %s\n" "$*"; }
warn()  { printf "${YELLOW}⚠${RESET}  %s\n" "$*"; }
err()   { printf "${RED}✗${RESET}  %s\n" "$*" >&2; }
die()   { err "$*"; exit 1; }

find_game_dir() {
    local possible_paths=(
        "/mnt/d/SteamLibrary/steamapps/common/Dawn of War Definitive Edition"
        "/mnt/c/Program Files (x86)/Steam/steamapps/common/Dawn of War Definitive Edition"
        "$HOME/.local/share/Steam/steamapps/common/Dawn of War Definitive Edition"
        "$HOME/.steam/steamapps/common/Dawn of War Definitive Edition"
    )
    for p in "${possible_paths[@]}"; do
        if [[ -d "$p" ]]; then
            echo "$p"
            return 0
        fi
    done
    return 1
}

# ── Verify backup exists and is valid ──────────────────────────────────────────
verify_baseline_backup() {
    [[ -f "$BASELINE_ENGINE_UCS" ]] || die "Backup file not found: $BASELINE_ENGINE_UCS"
    
    log "Verifying baseline backup integrity..."
    local backup_md5=$(md5sum "$BASELINE_ENGINE_UCS" | awk '{print $1}')
    local expected_md5="9cf2453a7c1525679ce0c38d6379e3ce"
    
    if [[ "$backup_md5" != "$expected_md5" ]]; then
        die "Backup checksum mismatch! Expected: $expected_md5, Got: $backup_md5"
    fi
    
    ok "Backup integrity verified (MD5: $backup_md5)"
}

# ── Main deployment ───────────────────────────────────────────────────────────
printf "\n${BOLD}DoW:DE — Deploy ORIGINAL BASELINE (not TC mod)${RESET}\n"
printf "Repo: %s\n\n" "$REPO_ROOT"

# 1. Verify backup exists first
verify_baseline_backup

# 2. Resolve game directory
if [[ -z "$GAME_DIR" ]]; then
    log "Auto-detecting game installation..."
    if ! GAME_DIR="$(find_game_dir)"; then
        die "Could not auto-detect game directory."
    fi
    ok "Found: $GAME_DIR"
else
    [[ -d "$GAME_DIR" ]] || die "Specified game dir does not exist: $GAME_DIR"
fi

LOCALE_TARGET="${GAME_DIR}/Engine/Locale/Chinese"
[[ -d "$LOCALE_TARGET" ]] || die "Expected locale directory missing: $LOCALE_TARGET"

printf "\n${BOLD}Target:${RESET} %s\n\n" "$LOCALE_TARGET"

# 3. Remove any existing TC mod data/ directory
if [[ -d "${LOCALE_TARGET}/data" ]]; then
    log "Removing TC mod data/ directory..."
    rm -rf "${LOCALE_TARGET}/data"
    ok "Removed ${LOCALE_TARGET}/data/"
fi

# 4. Deploy ORIGINAL Engine.ucs from backup
log "Deploying original Engine.ucs from backup..."
cp "$BASELINE_ENGINE_UCS" "${LOCALE_TARGET}/Engine.ucs"
ok "Deployed original Engine.ucs (MD5: 9cf2453a7c1525679ce0c38d6379e3ce)"

# 5. Restore/enable EnginLoc.sga (use original, not modified)
log "Restoring EnginLoc.sga..."
if [[ -f "${LOCALE_TARGET}/EnginLoc.sga.disabled" ]]; then
    mv "${LOCALE_TARGET}/EnginLoc.sga.disabled" "${LOCALE_TARGET}/EnginLoc.sga"
    ok "Re-enabled EnginLoc.sga"
else
    # Verify original EnginLoc.sga exists
    [[ -f "${LOCALE_TARGET}/EnginLoc.sga" ]] || die "EnginLoc.sga not found"
    ok "EnginLoc.sga already present (original)"
fi

# 6. Verify final state
printf "\n${BOLD}Verification:${RESET}\n"
echo "  Engine.ucs: $(file "${LOCALE_TARGET}/Engine.ucs" | grep -o 'ASCII\|Unicode')"
echo "  EnginLoc.sga: $([ -f "${LOCALE_TARGET}/EnginLoc.sga" ] && echo 'present' || echo 'MISSING')"
echo "  TC mod data/: $([ -d "${LOCALE_TARGET}/data" ] && echo 'PRESENT (should be empty)' || echo 'absent (correct)')"

printf "\n${GREEN}✓ ORIGINAL BASELINE DEPLOYED${RESET}\n"
printf "This is the clean original state - should NOT crash.\n\n"
