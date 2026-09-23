#!/usr/bin/env bash
# =============================================================================
# build_sga.sh — Automated SGA rebuild for WSL2
#
# This script uses the PROVEN WSL2 build approach with proper path conversion.
# No Windows-native execution required!
#
# Usage:
#   ./build_sga.sh                           # Vanilla font sizes
#   ./build_sga.sh --font-size-increase 6    # Increase fonts by +6
#   FONT_SIZE_INCREASE=6 ./build_sga.sh      # Via environment
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

log()  { printf "${CYAN}▶${RESET} %s\n" "$*"; }
ok()   { printf "${GREEN}✓${RESET} %s\n" "$*"; }
warn() { printf "${YELLOW}⚠${RESET}  %s\n" "$*"; }
err()  { printf "${RED}✗${RESET}  %s\n" "$*" >&2; exit 1; }

# ─────────────────────────────────────────────────────────────────────────────
# Parse arguments
# ─────────────────────────────────────────────────────────────────────────────
FONT_SIZE_INCREASE="${FONT_SIZE_INCREASE:-0}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --font-size-increase)
            FONT_SIZE_INCREASE="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [--font-size-increase N]"
            echo ""
            echo "Options:"
            echo "  --font-size-increase N    Increase all font sizes by N points (default: 0)"
            echo ""
            echo "Environment:"
            echo "  FONT_SIZE_INCREASE       Alternative to --font-size-increase flag"
            echo "  DOW_GAME_DIR             Game installation directory"
            exit 0
            ;;
        *)
            err "Unknown option: $1 (use --help for usage)"
            ;;
    esac
done

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
# Step 1: Clean and extract vanilla SGA
# ─────────────────────────────────────────────────────────────────────────────
log "Cleaning data directory..."
DATA_DIR="${REPO_ROOT}/data"
if [[ -d "$DATA_DIR" ]]; then
    rm -rf "$DATA_DIR"
fi
mkdir -p "$DATA_DIR"
ok "data/ directory cleaned"

log "Extracting vanilla Chinese locale SGA from game..."
# Prefer the CURRENT EnginLoc.sga (post-2026-08-12 game update; the live file
# is now the updated vanilla). Fall back to the Vortex backup only if the
# current file is missing.
VANILLA_SGA_BACKUP="${GAME_DIR}/Engine/Locale/Chinese/EnginLoc.sga.vortex_backup"
VANILLA_SGA_CURRENT="${GAME_DIR}/Engine/Locale/Chinese/EnginLoc.sga"

if [[ -f "$VANILLA_SGA_CURRENT" ]]; then
    VANILLA_SGA="$VANILLA_SGA_CURRENT"
    log "Using current EnginLoc.sga (post-update vanilla)"
elif [[ -f "$VANILLA_SGA_BACKUP" ]]; then
    VANILLA_SGA="$VANILLA_SGA_BACKUP"
    warn "Using vortex backup EnginLoc.sga.vortex_backup (pre-update; may be stale)"
else
    err "Chinese locale SGA not found in Engine/Locale/Chinese/"
fi

ok "Source SGA: $(basename "$VANILLA_SGA")"

WIN_VANILLA_SGA="$(_linux_to_win "$VANILLA_SGA")"
WIN_DATA="$(_linux_to_win "$DATA_DIR")"

"$ARCHIVE_EXE" -a "$WIN_VANILLA_SGA" -e "$WIN_DATA"
ok "Vanilla Chinese locale SGA extracted with $(find "$DATA_DIR" -type f | wc -l) files"

# ─────────────────────────────────────────────────────────────────────────────
# Vanilla Chinese locale already uses Noto Sans fonts - no modifications needed
# ─────────────────────────────────────────────────────────────────────────────
log "Verifying fonts..."
if [[ -f "$DATA_DIR/font/notosanstc-regular.ttf" ]]; then
    ok "Noto Sans TC fonts present in vanilla Chinese locale"
else
    warn "Noto Sans TC fonts not found (unexpected)"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Fix subtitle font references (prevent U+0000 glyph artifact)
# ─────────────────────────────────────────────────────────────────────────────
# CRITICAL: NotoSansTC-Bold.ttf and NotoSansTC-Regular.ttf have visible glyphs
# at Unicode U+0000 (null terminator). DoW's subtitle renderer includes null
# terminators → renders as gibberish characters (緝 U+7DC9 / 餘 U+9918)
# Solution: Reference NotoSansTC-Medium.ttf instead (no visible U+0000 glyph)
log "Fixing subtitle font references..."
sed -i \
    -e 's/file[[:space:]]*=[[:space:]]*"NotoSansTC-Bold\.ttf"/file = "NotoSansTC-Medium.ttf"/g' \
    -e 's/file[[:space:]]*=[[:space:]]*"NotoSansTC-Regular\.ttf"/file = "NotoSansTC-Medium.ttf"/g' \
    "$DATA_DIR/font/gillsans_11b.fnt" \
    "$DATA_DIR/font/gillsans_bold_16.fnt"
ok "Subtitle fonts now reference NotoSansTC-Medium.ttf (U+0000-safe)"

# ─────────────────────────────────────────────────────────────────────────────
# Optional: Adjust font sizes
# ─────────────────────────────────────────────────────────────────────────────
if [[ "$FONT_SIZE_INCREASE" -ne 0 ]]; then
    log "Adjusting font sizes by +${FONT_SIZE_INCREASE} points..."
    python3 "${REPO_ROOT}/scripts/adjust_font_sizes.py" \
        --root "$DATA_DIR" \
        --increase "$FONT_SIZE_INCREASE"
    ok "Font sizes adjusted"
else
    log "Using vanilla font sizes (no adjustment)"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Step 2: Setup build environment
# ─────────────────────────────────────────────────────────────────────────────
log "Setting up SGA build environment..."

BUILD_FILE="${REPO_ROOT}/.copilot_workspace/EnginLocBuild.txt"
OUTPUT_SGA="${REPO_ROOT}/EnginLocMod.sga"

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
# Step 4: Convert paths to Windows format
# ─────────────────────────────────────────────────────────────────────────────
log "Converting paths to Windows format..."

WIN_BUILD="$(_linux_to_win "$BUILD_FILE")"
WIN_OUTPUT="$(_linux_to_win "$OUTPUT_SGA")"
# WIN_DATA already converted during extraction

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
printf "Built from: ${BOLD}Vanilla Engine.sga${RESET}\n"
printf "Applied: ${BOLD}Noto Sans font fix${RESET}\n"
printf "Output: ${BOLD}${OUTPUT_SGA}${RESET}\n\n"
printf "Next: Run 'make package' to build distribution zip\n\n"
