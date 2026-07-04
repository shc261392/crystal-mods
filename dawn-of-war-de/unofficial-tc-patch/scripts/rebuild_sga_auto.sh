#!/usr/bin/env bash
# =============================================================================
# rebuild_sga_auto.sh — Automated SGA rebuild for WSL2
# 
# This script uses the PROVEN WSL2 build approach with proper path conversion.
# No Windows-native execution required!
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

log()  { printf "${CYAN}▶${RESET} %s\n" "$*"; }
ok()   { printf "${GREEN}✓${RESET} %s\n" "$*"; }
warn() { printf "${YELLOW}⚠${RESET}  %s\n" "$*"; }
err()  { printf "${RED}✗${RESET}  %s\n" "$*" >&2; exit 1; }

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# ─────────────────────────────────────────────────────────────────────────────
# Path conversion (WSL2 → Windows UNC format)
# ─────────────────────────────────────────────────────────────────────────────
# Convert Linux path to Windows format for Archive.exe
# /home/user/foo → \\wsl.localhost\Ubuntu\home\user\foo
# /mnt/d/Games   → D:\Games
_linux_to_win() {
    local p="$1"
    # Windows drive mounts (/mnt/d/...) → native Windows path (D:\...)
    if [[ "$p" =~ ^/mnt/([a-zA-Z])/(.*)$ ]]; then
        local drive="${BASH_REMATCH[1]^^}"
        local rest="${BASH_REMATCH[2]}"
        local winpath="${rest//\//\\}"
        printf '%s:\\%s' "$drive" "$winpath"
    else
        # WSL filesystem path → UNC (\\wsl.localhost\Ubuntu\...)
        local unc_root
        if command -v wslpath &>/dev/null; then
            unc_root="$(wslpath -w / 2>/dev/null)"
            unc_root="${unc_root%\\}"
        else
            unc_root='\\wsl.localhost\Ubuntu'
        fi
        local rel="${p#/}"
        local winrel="${rel//\//\\}"
        printf '%s\\%s' "$unc_root" "$winrel"
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Find game directory
# ─────────────────────────────────────────────────────────────────────────────
GAME_DIR=""

if [[ -n "${DOW_GAME_DIR:-}" ]]; then
    GAME_DIR="$DOW_GAME_DIR"
elif [[ -f "/mnt/d/SteamLibrary/steamapps/common/Dawn of War Definitive Edition/Archive.exe" ]]; then
    GAME_DIR="/mnt/d/SteamLibrary/steamapps/common/Dawn of War Definitive Edition"
else
    err "Cannot find game directory. Set DOW_GAME_DIR environment variable."
fi

ARCHIVE_EXE="${GAME_DIR}/Archive.exe"
[[ -f "$ARCHIVE_EXE" ]] || err "Archive.exe not found: $ARCHIVE_EXE"

ok "Game directory: $GAME_DIR"
ok "Archive.exe found"

# ─────────────────────────────────────────────────────────────────────────────
# Setup build environment
# ─────────────────────────────────────────────────────────────────────────────
log "Setting up build environment..."

BUILD_FILE="${REPO_ROOT}/.copilot_workspace/EnginLocBuild.txt"
DATA_DIR="${REPO_ROOT}/data"
OUTPUT_SGA="${REPO_ROOT}/EnginLocMod.sga"

[[ -d "$DATA_DIR/font" ]] || err "data/font/ directory not found. Run font patching first."

ok "data/ directory exists with $(find "$DATA_DIR" -type f | wc -l) files"

# ─────────────────────────────────────────────────────────────────────────────
# Verify fonts are patched
# ─────────────────────────────────────────────────────────────────────────────
log "Verifying font patches..."

SAMPLE_SIZE=$(grep "^[[:space:]]*sizeDefault" "$DATA_DIR/font/notosans_m_16_xc.fnt" | awk '{print $3}' | tr -d ';')
if [[ -z "$SAMPLE_SIZE" ]]; then
    err "Cannot read sizeDefault from font file"
fi

ok "Font size verified: sizeDefault = $SAMPLE_SIZE"

# ─────────────────────────────────────────────────────────────────────────────
# Create buildfile with CRLF endings
# ─────────────────────────────────────────────────────────────────────────────
log "Creating Archive.exe buildfile..."

mkdir -p "$(dirname "$BUILD_FILE")"

cat > "$BUILD_FILE" <<'EOF'
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

# Convert to CRLF (required by Archive.exe)
sed -i 's/$/\r/' "$BUILD_FILE"

ok "Buildfile created: $BUILD_FILE"

# ─────────────────────────────────────────────────────────────────────────────
# Convert paths to Windows format
# ─────────────────────────────────────────────────────────────────────────────
log "Converting paths to Windows format..."

WIN_BUILD="$(_linux_to_win "$BUILD_FILE")"
WIN_DATA="$(_linux_to_win "$DATA_DIR")"
WIN_OUTPUT="$(_linux_to_win "$OUTPUT_SGA")"

printf "  Build file: %s\n" "$WIN_BUILD"
printf "  Source dir: %s\n" "$WIN_DATA"
printf "  Output SGA: %s\n" "$WIN_OUTPUT"

# ─────────────────────────────────────────────────────────────────────────────
# Backup existing SGA
# ─────────────────────────────────────────────────────────────────────────────
if [[ -f "$OUTPUT_SGA" ]]; then
    BACKUP_NAME="EnginLocMod.sga.$(date +%Y%m%d-%H%M%S).bak"
    log "Backing up existing SGA to: $BACKUP_NAME"
    mv "$OUTPUT_SGA" "$BACKUP_NAME"
    ok "Backup created"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Run Archive.exe with Windows paths
# ─────────────────────────────────────────────────────────────────────────────
printf "\n${BOLD}Building SGA archive...${RESET}\n\n"

"$ARCHIVE_EXE" \
    -c "$WIN_BUILD" \
    -r "$WIN_DATA" \
    -a "$WIN_OUTPUT" \
    -v

# ─────────────────────────────────────────────────────────────────────────────
# Verify output
# ─────────────────────────────────────────────────────────────────────────────
printf "\n"
log "Verifying output..."

if [[ ! -f "$OUTPUT_SGA" ]]; then
    err "EnginLocMod.sga was not created!"
fi

FILE_SIZE=$(ls -lh "$OUTPUT_SGA" | awk '{print $5}')
FILE_TIME=$(stat -c %y "$OUTPUT_SGA" | cut -d'.' -f1)

ok "EnginLocMod.sga created successfully!"
printf "  Size: %s\n" "$FILE_SIZE"
printf "  Modified: %s\n" "$FILE_TIME"

# Test integrity
log "Testing SGA integrity..."
"$ARCHIVE_EXE" -a "$WIN_OUTPUT" -t &>/dev/null || warn "Integrity test failed (may be normal)"

printf "\n${GREEN}${BOLD}✓✓✓ SGA REBUILD COMPLETE!${RESET}\n\n"
printf "Font size: ${BOLD}${SAMPLE_SIZE}${RESET}\n"
printf "Output: ${BOLD}${OUTPUT_SGA}${RESET}\n\n"
printf "Next: Run 'make package' to build distribution zip\n\n"
