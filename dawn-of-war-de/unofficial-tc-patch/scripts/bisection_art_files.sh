#!/bin/bash
# =============================================================================
# bisection_art_files.sh — Test each .gfx file individually to isolate crash
#
# Usage: bash scripts/bisection_art_files.sh [FILE_NUM]
#
# Tests:
#   0 = Baseline (no art files)
#   1 = fonthead.gfx only
#   2 = fontbody.gfx only
#   3 = fontaux.gfx only
#   4 = font_glyphs.gfx only
#   5 = fontdecor.gfx only
#   6 = All .gfx files (full art/ui/swf)
# =============================================================================
set -euo pipefail

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

# ── Script location ───────────────────────────────────────────────────────────
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${REPO_ROOT}/backup/original-baseline"
BASELINE_ENGINE_UCS="${BACKUP_DIR}/Engine.ucs.original"

# ── Test number ───────────────────────────────────────────────────────────────
TEST_NUM="${1:-}"

# ── Defaults ──────────────────────────────────────────────────────────────────
GAME_DIR=""

# ── Functions ─────────────────────────────────────────────────────────────────
log()   { printf "${CYAN}▶${RESET} %s\n" "$*"; }
ok()    { printf "${GREEN}✓${RESET} %s\n" "$*"; }
err()   { printf "${RED}✗${RESET}  %s\n" "$*" >&2; }
die()   { err "$*"; exit 1; }

find_game_dir() {
    local possible_paths=(
        "/mnt/d/SteamLibrary/steamapps/common/Dawn of War Definitive Edition"
        "/mnt/c/Program Files (x86)/Steam/steamapps/common/Dawn of War Definitive Edition"
        "$HOME/.local/share/Steam/steamapps/common/Dawn of War Definitive Edition"
    )
    for p in "${possible_paths[@]}"; do
        [[ -d "$p" ]] && echo "$p" && return 0
    done
    return 1
}

list_tests() {
    cat <<EOF
${BOLD}Art File Isolation Tests${RESET}

Test 0: ${GREEN}Baseline${RESET} (no art files)
  Expected: No crash

Test 1: fonthead.gfx only
  Size: 8.4 MB
  Expected: Test

Test 2: fontbody.gfx only
  Size: 8.3 MB
  Expected: Test

Test 3: fontaux.gfx only
  Size: 8.4 MB
  Expected: Test

Test 4: font_glyphs.gfx only
  Size: 988 KB
  Expected: Test

Test 5: fontdecor.gfx only
  Size: 8.4 MB
  Expected: Test

Test 6: All .gfx files (full art/ui/swf)
  Expected: Crash

Usage:
  bash scripts/bisection_art_files.sh 1   # Test fonthead.gfx
  bash scripts/bisection_art_files.sh     # Show this list
EOF
}

prepare_test() {
    local test_num=$1
    
    # Start clean: baseline + original Engine.ucs
    [[ -d "${LOCALE_TARGET}/data" ]] && rm -rf "${LOCALE_TARGET}/data"
    cp "$BASELINE_ENGINE_UCS" "${LOCALE_TARGET}/Engine.ucs"
    
    case $test_num in
        0)
            ok "Test 0: Baseline (no art files)"
            ;;
        1)
            log "Test 1: fonthead.gfx only..."
            mkdir -p "${LOCALE_TARGET}/data/art/ui/swf"
            cp "${REPO_ROOT}/data/art/ui/swf/fonthead.gfx" "${LOCALE_TARGET}/data/art/ui/swf/"
            ok "fonthead.gfx deployed"
            ;;
        2)
            log "Test 2: fontbody.gfx only..."
            mkdir -p "${LOCALE_TARGET}/data/art/ui/swf"
            cp "${REPO_ROOT}/data/art/ui/swf/fontbody.gfx" "${LOCALE_TARGET}/data/art/ui/swf/"
            ok "fontbody.gfx deployed"
            ;;
        3)
            log "Test 3: fontaux.gfx only..."
            mkdir -p "${LOCALE_TARGET}/data/art/ui/swf"
            cp "${REPO_ROOT}/data/art/ui/swf/fontaux.gfx" "${LOCALE_TARGET}/data/art/ui/swf/"
            ok "fontaux.gfx deployed"
            ;;
        4)
            log "Test 4: font_glyphs.gfx only..."
            mkdir -p "${LOCALE_TARGET}/data/art/ui/swf"
            cp "${REPO_ROOT}/data/art/ui/swf/font_glyphs.gfx" "${LOCALE_TARGET}/data/art/ui/swf/"
            ok "font_glyphs.gfx deployed"
            ;;
        5)
            log "Test 5: fontdecor.gfx only..."
            mkdir -p "${LOCALE_TARGET}/data/art/ui/swf"
            cp "${REPO_ROOT}/data/art/ui/swf/fontdecor.gfx" "${LOCALE_TARGET}/data/art/ui/swf/"
            ok "fontdecor.gfx deployed"
            ;;
        6)
            log "Test 6: All .gfx files..."
            mkdir -p "${LOCALE_TARGET}/data/art/ui/swf"
            cp -a "${REPO_ROOT}/data/art/ui/swf/"*.gfx "${LOCALE_TARGET}/data/art/ui/swf/"
            ok "All .gfx files deployed"
            ;;
        *)
            die "Invalid test number: $test_num"
            ;;
    esac
}

verify_test() {
    printf "\n${BOLD}Deployed:${RESET}\n"
    if [[ -d "${LOCALE_TARGET}/data/art/ui/swf" ]]; then
        find "${LOCALE_TARGET}/data/art/ui/swf" -name "*.gfx" | sed 's|.*/||' | sed 's/^/  /'
    else
        echo "  (no art files)"
    fi
}

# ── Main ───────────────────────────────────────────────────────────────────────

[[ -z "$TEST_NUM" ]] && { list_tests; exit 0; }

printf "\n${BOLD}DoW:DE — Art File Isolation Test $TEST_NUM${RESET}\n\n"

GAME_DIR=$(find_game_dir) || die "Could not find game directory"
LOCALE_TARGET="${GAME_DIR}/Engine/Locale/Chinese"
[[ -d "$LOCALE_TARGET" ]] || die "Locale directory missing: $LOCALE_TARGET"

prepare_test "$TEST_NUM"
verify_test

printf "\n${BOLD}Instructions:${RESET}\n"
printf "1. Launch Dark Crusade campaign\n"
printf "2. If no crash: This file is safe\n"
printf "3. If crash: This file causes the issue\n\n"
