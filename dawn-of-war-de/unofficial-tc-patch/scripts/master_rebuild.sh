#!/usr/bin/env bash
# =============================================================================
# master_rebuild.sh — Complete automation for SGA rebuild with font size changes
#
# This script does EVERYTHING automatically:
#   1. Extracts/uses existing data/
#   2. Applies font size patches  
#   3. Attempts SGA repacking (with Windows fallback instructions)
#   4. Builds distribution packages
#
# Usage:
#   bash scripts/master_rebuild.sh --size 36
#   bash scripts/master_rebuild.sh --size 48
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

FONT_SIZE=${1:-36}
if [[ "$1" == "--size" ]]; then
    FONT_SIZE=${2:-36}
fi

log()  { printf "${CYAN}▶${RESET} %s\n" "$*"; }
ok()   { printf "${GREEN}✓${RESET} %s\n" "$*"; }
warn() { printf "${YELLOW}⚠${RESET}  %s\n" "$*"; }
err()  { printf "${RED}✗${RESET}  %s\n" "$*" >&2; }

printf "\n${BOLD}WH40K DoW:DE — Master SGA Rebuild Script${RESET}\n"
printf "${BOLD}Font Size: ${FONT_SIZE}${RESET}\n\n"

# ─────────────────────────────────────────────────────────────────────────────
# Step 1: Ensure data/ directory exists
# ─────────────────────────────────────────────────────────────────────────────
log "Step 1/4: Ensuring data/ directory exists..."

if [[ ! -d "data/font" ]]; then
    if [[ -d "backup/20260604-144320/data" ]]; then
        warn "data/ not found, copying from backup..."
        cp -r backup/20260604-144320/data .
        ok "Copied data/ from backup"
    else
        err "No data/ directory and no backup found"
        err "Cannot proceed without extracted SGA files"
        exit 1
    fi
else
    ok "data/ directory exists"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Step 2: Apply font size patches
# ─────────────────────────────────────────────────────────────────────────────
log "Step 2/4: Applying font size patches (SIZE=${FONT_SIZE})..."

python3 scripts/apply_font_fix.py \
    --root . \
    --size "$FONT_SIZE" \
    --mode fallback-only

ok "Font patches applied (sizeDefault=${FONT_SIZE})"

# Verify
SAMPLE_SIZE=$(grep "^[[:space:]]*sizeDefault" data/font/notosans_m_16_xc.fnt | awk '{print $3}' | tr -d ';')
if [[ "$SAMPLE_SIZE" == "$FONT_SIZE" ]]; then
    ok "Verified: sizeDefault=${SAMPLE_SIZE}"
else
    err "Verification failed: expected ${FONT_SIZE}, got ${SAMPLE_SIZE}"
    exit 1
fi

# ─────────────────────────────────────────────────────────────────────────────
# Step 3: Repack SGA (Windows execution required)
# ─────────────────────────────────────────────────────────────────────────────
log "Step 3/4: Repacking SGA..."

# Create buildfile
mkdir -p .copilot_workspace
cat > .copilot_workspace/EnginLocBuild.txt <<'EOF'
Archive
TOCStart alias="data" relativeroot="."
FileSettingsStart defcompression="1"
    Override wildcard=".*(gfx)$" minsize="-1" maxsize="-1" ct="1"
    Override wildcard=".*(fnt)$" minsize="-1" maxsize="-1" ct="2"
    Override wildcard=".*(ttf|ttc)$" minsize="-1" maxsize="-1" ct="0"
    Override wildcard=".*(fda|rat)$" minsize="-1" maxsize="-1" ct="2"
FileSettingsEnd
TOCEnd
EOF
sed -i 's/$/\r/' .copilot_workspace/EnginLocBuild.txt
ok "Buildfile created"

# Try running repack script on Windows
warn "SGA repacking requires Archive.exe (Windows native)"
warn "Attempting automated Windows execution..."

REPO_WIN=$(wslpath -w "$REPO_ROOT" 2>/dev/null || echo "$REPO_ROOT")
CMD_SCRIPT="scripts\\rebuild_sga.cmd"

printf "\n${YELLOW}Running: cmd.exe /c ${CMD_SCRIPT}${RESET}\n\n"
cmd.exe /c "$CMD_SCRIPT" 2>&1 | head -50 || warn "Windows execution may have failed (WSL2 socket error)"

# Check if SGA was rebuilt
OLD_TIMESTAMP=$(stat -c %Y EnginLocMod.sga 2>/dev/null || echo "0")
sleep 2
NEW_TIMESTAMP=$(stat -c %Y EnginLocMod.sga 2>/dev/null || echo "0")

if [[ "$NEW_TIMESTAMP" -gt "$OLD_TIMESTAMP" ]]; then
    ok "EnginLocMod.sga was rebuilt!"
    ls -lh EnginLocMod.sga
else
    warn "EnginLocMod.sga was NOT rebuilt (WSL2 limitation)"
    printf "\n${YELLOW}${BOLD}MANUAL STEP REQUIRED:${RESET}\n\n"
    printf "Open Windows Command Prompt and run:\n\n"
    printf "  ${CYAN}cd ${REPO_WIN}${RESET}\n"
    printf "  ${CYAN}${CMD_SCRIPT}${RESET}\n\n"
    printf "Then return here and press Enter to continue...\n"
    read -r
    
    # Recheck
    NEW_TIMESTAMP=$(stat -c %Y EnginLocMod.sga 2>/dev/null || echo "0")
    if [[ "$NEW_TIMESTAMP" -gt "$OLD_TIMESTAMP" ]]; then
        ok "EnginLocMod.sga detected! Continuing..."
    else
        err "EnginLocMod.sga still not updated"
        err "Please run the Windows CMD script manually and rerun this master script"
        exit 1
    fi
fi

# ─────────────────────────────────────────────────────────────────────────────
# Step 4: Build distribution package
# ─────────────────────────────────────────────────────────────────────────────
log "Step 4/4: Building distribution package..."

make package

if [[ "$FONT_SIZE" == "48" ]]; then
    # Rename for font48 variant
    VERSION=$(python3 -c "import json,pathlib; print(json.loads(pathlib.Path('modinfo.json').read_text())['version'])" 2>/dev/null || echo "1.0.5")
    mv "dist/wh40k-dow-de-tc-mod-v${VERSION}.zip" "dist/wh40k-dow-de-tc-mod-v${VERSION}-font48.zip" 2>/dev/null || true
    ok "Package created: dist/wh40k-dow-de-tc-mod-v${VERSION}-font48.zip"
else
    ok "Package created: dist/wh40k-dow-de-tc-mod-v*.zip"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Done!
# ─────────────────────────────────────────────────────────────────────────────
printf "\n${GREEN}${BOLD}✓✓✓ BUILD COMPLETE!${RESET}\n\n"
printf "Font size: ${BOLD}${FONT_SIZE}${RESET}\n"
printf "Package: ${BOLD}dist/wh40k-dow-de-tc-mod-v*${RESET}\n\n"

if [[ "$FONT_SIZE" == "36" ]]; then
    printf "To build the font48 variant:\n"
    printf "  ${CYAN}bash scripts/master_rebuild.sh --size 48${RESET}\n\n"
fi

printf "Next: Test the package in-game!\n\n"
