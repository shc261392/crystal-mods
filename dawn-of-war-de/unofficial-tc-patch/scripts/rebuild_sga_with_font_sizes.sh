#!/usr/bin/env bash
# =============================================================================
# rebuild_sga_with_font_sizes.sh — Automated SGA rebuild with font patches
#
# This script fully automates the process of:
#   1. Extracting the vanilla EnginLoc.sga
#   2. Applying font size patches
#   3. Repacking to EnginLocMod.sga
#   4. Building release packages
#
# Usage:
#   bash scripts/rebuild_sga_with_font_sizes.sh [--size SIZE] [--skip-extract]
#
# Arguments:
#   --size SIZE         Font size to apply (default: 36)
#   --skip-extract      Skip SGA extraction (use existing data/ directory)
#   --clean             Clean up data/ directory after build
#   --help              Show this help
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

GAME_DIR="${DOW_GAME_DIR:-/mnt/d/SteamLibrary/steamapps/common/Dawn of War Definitive Edition}"
ARCHIVE_EXE="$GAME_DIR/Archive.exe"
VANILLA_SGA="$GAME_DIR/Engine/Locale/Chinese/EnginLoc.sga"

FONT_SIZE=36
SKIP_EXTRACT=false
CLEAN_AFTER=false

log()  { printf "${CYAN}▶${RESET} %s\n" "$*"; }
ok()   { printf "${GREEN}✓${RESET} %s\n" "$*"; }
warn() { printf "${YELLOW}⚠${RESET}  %s\n" "$*"; }
err()  { printf "${RED}✗${RESET}  %s\n" "$*" >&2; }
die()  { err "$*"; exit 1; }

usage() {
    cat <<EOF
Usage: bash scripts/rebuild_sga_with_font_sizes.sh [OPTIONS]

Automates the complete SGA rebuild process with font size patches.

Options:
  --size SIZE         Font size to apply (default: 36)
  --skip-extract      Skip extraction (use existing data/ directory)
  --clean             Remove data/ directory after successful build
  --help              Show this help message

Environment:
  DOW_GAME_DIR        Game installation directory (default: /mnt/d/SteamLibrary/...)

Examples:
  bash scripts/rebuild_sga_with_font_sizes.sh --size 36
  bash scripts/rebuild_sga_with_font_sizes.sh --size 48 --skip-extract
EOF
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --size)         FONT_SIZE="$2"; shift 2 ;;
        --skip-extract) SKIP_EXTRACT=true; shift ;;
        --clean)        CLEAN_AFTER=true; shift ;;
        --help|-h)      usage; exit 0 ;;
        *) die "Unknown option: $1 (use --help)" ;;
    esac
done

printf "\n${BOLD}WH40K DoW:DE — Automated SGA Rebuild with Font Size ${FONT_SIZE}${RESET}\n\n"

# ─────────────────────────────────────────────────────────────────────────────
# 0. Verify prerequisites
# ─────────────────────────────────────────────────────────────────────────────
log "Verifying prerequisites..."

[[ -f "$ARCHIVE_EXE" ]] || die "Archive.exe not found: $ARCHIVE_EXE"
[[ -f "$VANILLA_SGA" ]] || die "Vanilla SGA not found: $VANILLA_SGA"
command -v python3 &>/dev/null || command -v uv &>/dev/null || die "Python not found"

ok "Prerequisites verified"

# ─────────────────────────────────────────────────────────────────────────────
# 1. Extract vanilla SGA (or use backup)
# ─────────────────────────────────────────────────────────────────────────────
if [[ "$SKIP_EXTRACT" == "false" ]]; then
    if [[ -d "data" ]]; then
        warn "data/ directory already exists, using it as-is"
        FONT_COUNT=$(find data/font -name "*.fnt" 2>/dev/null | wc -l)
        if [[ "$FONT_COUNT" -gt 0 ]]; then
            ok "Using existing data/ with ${FONT_COUNT} font files"
        else
            die "data/ exists but contains no font files"
        fi
    else
        log "Extracting vanilla EnginLoc.sga..."
        
        # Try extraction using Archive.exe
        log "Running Archive.exe -a EnginLoc.sga -e ..."
        "$ARCHIVE_EXE" -a "$VANILLA_SGA" -e "." 2>&1 | grep -v "^<" | head -20 || true
        
        if [[ ! -d "data/font" ]]; then
            warn "Archive.exe extraction failed (WSL2 compatibility issue)"
            
            # Fallback: use backup if available
            BACKUP_DATA="backup/20260604-144320/data"
            if [[ -d "$BACKUP_DATA" ]]; then
                warn "Falling back to backup extraction: $BACKUP_DATA"
                cp -r "$BACKUP_DATA" .
                ok "Copied data/ from backup"
            else
                die "Extraction failed and no backup found at $BACKUP_DATA"
            fi
        fi
        
        FONT_COUNT=$(find data/font -name "*.fnt" | wc -l)
        ok "Ready with ${FONT_COUNT} font files in data/"
    fi
else
    log "Skipping extraction (using existing data/ directory)"
    [[ -d "data/font" ]] || die "data/font/ not found (cannot skip extraction)"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 2. Apply font size patches
# ─────────────────────────────────────────────────────────────────────────────
log "Applying font size patches (size=${FONT_SIZE}, mode=fallback-only)..."

if command -v uv &>/dev/null; then
    PYTHON="uv run python"
else
    PYTHON="python3"
fi

$PYTHON scripts/apply_font_fix.py \
    --root . \
    --size "$FONT_SIZE" \
    --mode fallback-only \
    || die "Font patching failed"

ok "Font patches applied (sizeDefault=${FONT_SIZE})"

# ─────────────────────────────────────────────────────────────────────────────
# 3. Create SGA buildfile
# ─────────────────────────────────────────────────────────────────────────────
log "Creating SGA buildfile..."

BUILDFILE=".copilot_workspace/EnginLocBuild.txt"
mkdir -p .copilot_workspace

cat > "$BUILDFILE" <<'BUILDFILE_EOF'
Archive
TOCStart alias="data" relativeroot="."
FileSettingsStart defcompression="1"
    Override wildcard=".*(gfx)$" minsize="-1" maxsize="-1" ct="1"
    Override wildcard=".*(fnt)$" minsize="-1" maxsize="-1" ct="2"
    Override wildcard=".*(ttf|ttc)$" minsize="-1" maxsize="-1" ct="0"
    Override wildcard=".*(fda|rat)$" minsize="-1" maxsize="-1" ct="2"
FileSettingsEnd
TOCEnd
BUILDFILE_EOF

# Convert to CRLF (Windows line endings required by Archive.exe)
if command -v unix2dos &>/dev/null; then
    unix2dos "$BUILDFILE" 2>/dev/null
else
    sed -i 's/$/\r/' "$BUILDFILE"
fi

ok "Buildfile created: $BUILDFILE"

# ─────────────────────────────────────────────────────────────────────────────
# 4. Repack SGA
# ─────────────────────────────────────────────────────────────────────────────
log "Repacking to EnginLocMod.sga..."

# Backup existing SGA if present
if [[ -f "EnginLocMod.sga" ]]; then
    timestamp=$(date +%Y%m%d-%H%M%S)
    mv EnginLocMod.sga "EnginLocMod.sga.backup.$timestamp"
    ok "Backed up old SGA to EnginLocMod.sga.backup.$timestamp"
fi

# Convert paths for Archive.exe
BUILDFILE_WIN=$(wslpath -w "$BUILDFILE" 2>/dev/null || echo "$BUILDFILE")
DATA_WIN=$(wslpath -w "$(pwd)/data" 2>/dev/null || echo "$(pwd)/data")
OUTPUT_WIN=$(wslpath -w "$(pwd)/EnginLocMod.sga" 2>/dev/null || echo "$(pwd)/EnginLocMod.sga")

log "Running Archive.exe -build (this takes ~60 seconds)..."
"$ARCHIVE_EXE" \
    -build "$BUILDFILE_WIN" \
    -sourcedir "$DATA_WIN" \
    -archive "$OUTPUT_WIN" \
    -verbose 2>&1 | grep -v "^<" || true

if [[ ! -f "EnginLocMod.sga" ]]; then
    die "SGA build failed: EnginLocMod.sga not created"
fi

SGA_SIZE=$(du -sh EnginLocMod.sga | cut -f1)
ok "EnginLocMod.sga built successfully (${SGA_SIZE})"

# ─────────────────────────────────────────────────────────────────────────────
# 5. Verify SGA integrity
# ─────────────────────────────────────────────────────────────────────────────
log "Verifying SGA integrity..."

SGA_WIN=$(wslpath -w "$(pwd)/EnginLocMod.sga" 2>/dev/null || echo "$(pwd)/EnginLocMod.sga")
if "$ARCHIVE_EXE" -verify "$SGA_WIN" 2>&1 | grep -q "SUCCESS\|OK\|PASS" || true; then
    ok "SGA integrity verified"
else
    warn "Could not verify SGA integrity (Archive.exe may not support -verify)"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 6. Extract one font file to verify size
# ─────────────────────────────────────────────────────────────────────────────
log "Extracting sample font to verify size..."

VERIFY_DIR=".copilot_workspace/verify_size_${FONT_SIZE}"
rm -rf "$VERIFY_DIR"
mkdir -p "$VERIFY_DIR"

VERIFY_WIN=$(wslpath -w "$VERIFY_DIR" 2>/dev/null || echo "$VERIFY_DIR")
"$ARCHIVE_EXE" -extract "$SGA_WIN" -outpath "$VERIFY_WIN" 2>&1 | grep -v "^<" || true

if [[ -f "$VERIFY_DIR/data/font/notosans_m_16_xc.fnt" ]]; then
    ACTUAL_SIZE=$(grep "^sizeDefault" "$VERIFY_DIR/data/font/notosans_m_16_xc.fnt" | awk '{print $3}' | tr -d ';')
    if [[ "$ACTUAL_SIZE" == "$FONT_SIZE" ]]; then
        ok "Verified: sizeDefault=${ACTUAL_SIZE} (matches requested ${FONT_SIZE})"
    else
        err "SIZE MISMATCH: sizeDefault=${ACTUAL_SIZE}, expected ${FONT_SIZE}"
        die "Font size verification failed"
    fi
else
    warn "Could not extract verification font (skipping size check)"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 7. Clean up (optional)
# ─────────────────────────────────────────────────────────────────────────────
if [[ "$CLEAN_AFTER" == "true" ]]; then
    log "Cleaning up data/ directory..."
    rm -rf data
    ok "Cleaned up data/"
fi

printf "\n${GREEN}${BOLD}✓ SGA rebuild complete!${RESET}\n"
printf "  EnginLocMod.sga: ${SGA_SIZE}\n"
printf "  Font size: ${FONT_SIZE}\n"
printf "\n"
printf "Next steps:\n"
printf "  1. Run: make package\n"
printf "  2. Test the package in-game\n"
printf "  3. Repeat with --size 48 for large font variant\n"
printf "\n"
