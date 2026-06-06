#!/bin/bash
# =============================================================================
# bisection_test.sh — Incremental component testing to isolate crash cause
#
# Purpose: Starting from original baseline, incrementally add TC mod components
#          and test to identify which file causes Dark Crusade crash
#
# Usage: bash scripts/bisection_test.sh [TEST_NUMBER]
#
# Tests:
#   0 = Baseline (original - should work)
#   1 = Baseline + TC Engine.ucs only
#   2 = Baseline + TC data/font/ only  
#   3 = Baseline + TC data/art/ only
#   4 = Baseline + TC data/sound/ only
#   5 = Full TC mod (all components)
# =============================================================================
set -euo pipefail

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

# ── Script location = repo root ───────────────────────────────────────────────
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${REPO_ROOT}/backup/original-baseline"
BASELINE_ENGINE_UCS="${BACKUP_DIR}/Engine.ucs.original"

# ── Test number (default to list tests if not provided) ────────────────────────
TEST_NUM="${1:-}"

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

list_tests() {
    cat <<EOF
${BOLD}Bisection Tests${RESET}

Test 0: ${GREEN}BASELINE${RESET} (original - reference)
  Components: Original Engine.ucs + EnginLoc.sga
  Expected: ${GREEN}No crash${RESET}
  Purpose: Establish clean baseline

Test 1: ${YELLOW}Baseline + TC Engine.ucs${RESET}
  Components: TC Engine.ucs + EnginLoc.sga (original data/)
  Expected: Test result
  Purpose: Isolate Engine.ucs impact

Test 2: ${YELLOW}Baseline + TC data/font/${RESET}
  Components: Original Engine.ucs + TC font files + EnginLoc.sga
  Expected: Test result
  Purpose: Isolate font file impact

Test 3: ${YELLOW}Baseline + TC data/art/${RESET}
  Components: Original Engine.ucs + TC art files + EnginLoc.sga
  Expected: Test result
  Purpose: Isolate art file impact

Test 4: ${YELLOW}Baseline + TC data/sound/${RESET}
  Components: Original Engine.ucs + TC sound files + EnginLoc.sga
  Expected: Test result
  Purpose: Isolate sound file impact

Test 5: ${RED}Full TC mod${RESET} (all components)
  Components: TC Engine.ucs + TC data/ (all)
  Expected: ${RED}Crash${RESET}
  Purpose: Confirm TC mod causes crash

Usage:
  bash scripts/bisection_test.sh 1    # Run test 1
  bash scripts/bisection_test.sh      # Show this list
EOF
}

prepare_game_state() {
    local test_num=$1
    
    log "Preparing game state for Test $test_num..."
    
    # Remove any existing TC data/
    [[ -d "${LOCALE_TARGET}/data" ]] && rm -rf "${LOCALE_TARGET}/data"
    
    # Start with baseline Engine.ucs
    cp "$BASELINE_ENGINE_UCS" "${LOCALE_TARGET}/Engine.ucs"
    ok "Base state: Original Engine.ucs + EnginLoc.sga"
    
    # Deploy additional components based on test number
    case $test_num in
        0)
            # Baseline - nothing to add
            ok "Test 0 (Baseline): Ready"
            ;;
        1)
            # Replace Engine.ucs with TC version
            log "Adding: TC Engine.ucs..."
            cp "${REPO_ROOT}/Engine.ucs" "${LOCALE_TARGET}/Engine.ucs"
            ok "Test 1 (TC Engine.ucs): Ready"
            ;;
        2)
            # Deploy TC font files
            log "Adding: TC data/font/..."
            mkdir -p "${LOCALE_TARGET}/data/font"
            cp -a "${REPO_ROOT}/data/font/"* "${LOCALE_TARGET}/data/font/" 2>/dev/null || true
            ok "Test 2 (TC data/font): Ready"
            ;;
        3)
            # Deploy TC art files
            log "Adding: TC data/art/..."
            mkdir -p "${LOCALE_TARGET}/data/art"
            cp -a "${REPO_ROOT}/data/art/"* "${LOCALE_TARGET}/data/art/" 2>/dev/null || true
            ok "Test 3 (TC data/art): Ready"
            ;;
        4)
            # Deploy TC sound files
            log "Adding: TC data/sound/..."
            mkdir -p "${LOCALE_TARGET}/data/sound"
            cp -a "${REPO_ROOT}/data/sound/"* "${LOCALE_TARGET}/data/sound/" 2>/dev/null || true
            ok "Test 4 (TC data/sound): Ready"
            ;;
        5)
            # Full TC mod
            log "Adding: Full TC mod (Engine.ucs + all data/)..."
            cp "${REPO_ROOT}/Engine.ucs" "${LOCALE_TARGET}/Engine.ucs"
            cp -a "${REPO_ROOT}/data"/* "${LOCALE_TARGET}/data/" 2>/dev/null || mkdir -p "${LOCALE_TARGET}/data"
            ok "Test 5 (Full TC mod): Ready"
            ;;
        *)
            die "Invalid test number: $test_num"
            ;;
    esac
}

verify_deployment() {
    local test_num=$1
    printf "\n${BOLD}Verification:${RESET}\n"
    
    # Check Engine.ucs
    if [[ -f "${LOCALE_TARGET}/Engine.ucs" ]]; then
        local size=$(stat -c%s "${LOCALE_TARGET}/Engine.ucs" 2>/dev/null || stat -f%z "${LOCALE_TARGET}/Engine.ucs")
        echo "  Engine.ucs: $size bytes"
    fi
    
    # Check data directories
    if [[ -d "${LOCALE_TARGET}/data/font" ]]; then
        local count=$(find "${LOCALE_TARGET}/data/font" -type f | wc -l)
        echo "  data/font: $count files"
    fi
    if [[ -d "${LOCALE_TARGET}/data/art" ]]; then
        local count=$(find "${LOCALE_TARGET}/data/art" -type f | wc -l)
        echo "  data/art: $count files"
    fi
    if [[ -d "${LOCALE_TARGET}/data/sound" ]]; then
        local count=$(find "${LOCALE_TARGET}/data/sound" -type f | wc -l)
        echo "  data/sound: $count files"
    fi
    
    echo "  EnginLoc.sga: $([ -f "${LOCALE_TARGET}/EnginLoc.sga" ] && echo 'present' || echo 'MISSING')"
}

# ── Main ───────────────────────────────────────────────────────────────────────

# If no test number, show list
if [[ -z "$TEST_NUM" ]]; then
    list_tests
    exit 0
fi

printf "\n${BOLD}DoW:DE — Bisection Test $TEST_NUM${RESET}\n\n"

# Find game dir
if ! GAME_DIR="$(find_game_dir)"; then
    die "Could not auto-detect game directory."
fi

LOCALE_TARGET="${GAME_DIR}/Engine/Locale/Chinese"
[[ -d "$LOCALE_TARGET" ]] || die "Expected locale directory missing: $LOCALE_TARGET"

# Prepare and deploy test state
prepare_game_state "$TEST_NUM"
verify_deployment "$TEST_NUM"

printf "\n${BOLD}Manual Testing:${RESET}\n"
printf "1. Launch Dark Crusade campaign\n"
printf "2. Test result:\n"
printf "   ${GREEN}No crash${RESET}  = This component is safe\n"
printf "   ${RED}Crashes${RESET}    = This component causes crash\n"
printf "\nWhen ready, re-run with next test number.\n\n"
