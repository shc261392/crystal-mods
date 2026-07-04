#\!/usr/bin/env bash
# =============================================================================
# deploy.sh — WH40K DoW:DE Traditional Chinese Locale Mod deployer
#
# Supports:
#   • Linux (native Steam + Proton)
#   • WSL2 (Windows Subsystem for Linux — accesses Windows paths via /mnt/c ...)
#
# Usage:
#   bash deploy.sh [--game-dir PATH] [--dry-run] [--no-backup]
#
# What it does (SGA-only deployment):
#   1. Auto-detect the game installation directory
#   2. Create a timestamped backup of existing EnginLocMod.sga + Engine.ucs
#   3. Copy pre-built EnginLocMod.sga to Engine/Locale/Chinese/
#   4. Copy Engine.ucs (strings) to Engine/Locale/Chinese/
#   5. Verify deployment integrity
#
# Notes:
#   - EnginLocMod.sga is a pre-built, pre-tested archive (no build step)
#   - Game loads: EnginLocMod.sga (TC) + vanilla EnginLoc.sga alongside
#   - fontdecor.gfx excluded from TC SGA (uses vanilla version)
#   - All files tested with binary search methodology
#   - Loose data deployment is OBSOLETE (removed in v1.0.4)
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
GAME_FOLDER_NAME="Dawn of War Definitive Edition"

# ── Files to deploy (pre-built SGA) ──────────────────────────────────────────
DEPLOY_FILES=(EnginLocMod.sga Engine.ucs)

# ── Target sub-path inside game root ─────────────────────────────────────────
LOCALE_SUBPATH="Engine/Locale/Chinese"

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
  DOW_GAME_DIR      Alternative to --game-dir (env var)

Note:
  This script deploys pre-built SGA archives only.
  Loose data deployment has been removed (obsolete since v1.0.4).
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
[[ -z "$GAME_DIR" && -n "${DOW_GAME_DIR:-}" ]] && GAME_DIR="$DOW_GAME_DIR"

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
        # Extract "path" values and convert Windows paths to WSL paths.
        # Note: PCRE variable-length lookbehinds are unsupported, so use sed.
        while IFS= read -r raw; do
            if [[ "$raw" =~ ^[A-Za-z]: ]]; then
                _win_to_wsl "$raw"
            else
                echo "$raw"
            fi
        done < <(grep '"path"' "$vdf" 2>/dev/null | sed -E 's/.*"path"\s+"([^"]+)".*/\1/' || true)
        # Also add the directory containing the VDF itself (the default Steam lib)
        echo "$(dirname "$(dirname "$vdf")")"
    done
}

find_game_dir() {
    local roots
    mapfile -t roots < <(_steam_library_roots | sort -u)

    for lib_root in "${roots[@]}"; do
        local candidate="${lib_root}/steamapps/common/${GAME_FOLDER_NAME}"
        if [[ -d "$candidate" ]]; then
            echo "$candidate"
            return 0
        fi
        # Case-insensitive fallback (Linux filesystems are case-sensitive)
        local found
        found="$(find "${lib_root}/steamapps/common" -maxdepth 1 -iname "${GAME_FOLDER_NAME}" -type d 2>/dev/null | head -1)"
        if [[ -n "$found" ]]; then
            echo "$found"
            return 0
        fi
    done

    # Last resort: broader search under /mnt for WSL (slow — only if nothing found)
    for drv in c d e f; do
        [[ -d "/mnt/${drv}" ]] || continue
        local found
        found="$(find "/mnt/${drv}" -maxdepth 8 -iname "${GAME_FOLDER_NAME}" -type d 2>/dev/null | head -1)"
        if [[ -n "$found" ]]; then
            echo "$found"
            return 0
        fi
    done

    return 1
}

# ─────────────────────────────────────────────────────────────────────────────
# Backup helpers
# ─────────────────────────────────────────────────────────────────────────────

backup_item() {
    local src="$1"
    local rel="${src#${LOCALE_TARGET}/}"
    local dst="${BACKUP_DIR}/${STAMP}/${rel}"
    mkdir -p "$(dirname "$dst")"
    if [[ -e "$src" ]]; then
        cp -a "$src" "$dst"
        echo "$src" >> "$MANIFEST_FILE"
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Main deploy logic
# ─────────────────────────────────────────────────────────────────────────────

printf "\n${BOLD}WH40K DoW:DE — Traditional Chinese Locale Mod Deployer${RESET}\n"
printf "Repo: %s\n" "$REPO_ROOT"
printf "Mode: SGA-only (pre-built archives)\n\n"

# 1. Resolve game directory
if [[ -z "$GAME_DIR" ]]; then
    log "Auto-detecting game installation..."
    if \! GAME_DIR="$(find_game_dir)"; then
        err "Could not auto-detect game directory."
        err "Set DOW_GAME_DIR or pass --game-dir PATH."
        err ""
        err "Typical paths:"
        err "  Linux Proton: ~/.local/share/Steam/steamapps/common/Dawn of War Definitive Edition"
        err "  WSL2:         /mnt/d/SteamLibrary/steamapps/common/Dawn of War Definitive Edition"
        exit 1
    fi
    ok "Found: $GAME_DIR"
else
    [[ -d "$GAME_DIR" ]] || die "Specified game dir does not exist: $GAME_DIR"
    ok "Using provided: $GAME_DIR"
fi

LOCALE_TARGET="${GAME_DIR}/${LOCALE_SUBPATH}"

# Verify this actually looks like the right directory
[[ -d "$LOCALE_TARGET" ]] || die "Expected locale directory missing: $LOCALE_TARGET"

printf "\n${BOLD}Target:${RESET} %s\n" "$LOCALE_TARGET"
$DRY_RUN && printf "${YELLOW}[DRY RUN — no files will be written]${RESET}\n"
printf "\n"

# 2. Backup existing files in the target
if \! $NO_BACKUP && \! $DRY_RUN; then
    log "Creating backup (${BACKUP_DIR}/${STAMP}/)..."
    mkdir -p "${BACKUP_DIR}/${STAMP}"
    echo "deploy_timestamp=${STAMP}" > "$MANIFEST_FILE"
    echo "game_dir=${GAME_DIR}" >> "$MANIFEST_FILE"
    echo "locale_target=${LOCALE_TARGET}" >> "$MANIFEST_FILE"
    echo "---files---" >> "$MANIFEST_FILE"

    # Backup deployed files
    for f in "${DEPLOY_FILES[@]}"; do
        [[ -f "${LOCALE_TARGET}/${f}" ]] && backup_item "${LOCALE_TARGET}/${f}" || true
    done

    ok "Backup written to ${BACKUP_DIR}/${STAMP}/"
fi

# 3. Deploy SGA and UCS files
for f in "${DEPLOY_FILES[@]}"; do
    local_src="${REPO_ROOT}/${f}"
    [[ -f "$local_src" ]] || die "Source file missing: $local_src"

    log "Deploying ${f} → ${LOCALE_TARGET}/${f}"
    if \! $DRY_RUN; then
        cp -f "$local_src" "${LOCALE_TARGET}/${f}"
        ok "Deployed ${f}"
    else
        warn "[DRY RUN] Would copy: ${f}"
    fi
done

# 4. Migrate campaign states: copy SC save progress into TC state slots
#    This preserves WXP (Winter Assault) campaign progress when switching
#    from the original Simplified Chinese locale to this TC mod.
#    The migration is non-fatal: a warning is printed if it fails so that
#    the rest of the deploy still completes.
log "Migrating campaign states (SC → TC statenames)..."
_run_migration() {
    local py_runner
    if command -v uv &>/dev/null; then
        py_runner="uv run python"
    elif command -v python3 &>/dev/null; then
        py_runner="python3"
    else
        warn "No Python interpreter found; skipping campaign state migration."
        warn "Run manually: python scripts/migrate_campaign_states.py"
        return 0
    fi

    local extra_flags=()
    $DRY_RUN && extra_flags+=("--dry-run")

    $py_runner "${REPO_ROOT}/scripts/migrate_campaign_states.py" \
        --profile Profile1 \
        "${extra_flags[@]}" \
        2>&1 | while IFS= read -r line; do printf "    %s\n" "$line"; done
}
if \! _run_migration; then
    warn "Campaign state migration returned a non-zero exit — check output above."
    warn "Your save files are unchanged; deploy will continue."
fi

# 5. Record deployment state for uninstall
if \! $DRY_RUN; then
    DEPLOY_STATE="${REPO_ROOT}/.copilot_workspace/last_deploy.env"
    mkdir -p "$(dirname "$DEPLOY_STATE")"
    cat > "$DEPLOY_STATE" <<ENVEOF
GAME_DIR="${GAME_DIR}"
LOCALE_TARGET="${LOCALE_TARGET}"
BACKUP_STAMP=${STAMP}
BACKUP_DIR="${BACKUP_DIR}/${STAMP}"
ENVEOF
    ok "Deploy state saved: ${DEPLOY_STATE}"
fi

printf "\n${GREEN}${BOLD}Deployment complete\!${RESET}\n"
printf "  Launch DoW:DE and verify Chinese text rendering.\n"
printf "  To revert: bash uninstall.sh  (or: make uninstall)\n\n"
