#!/usr/bin/env bash
# =============================================================================
# deploy.sh — WH40K DoW:DE Traditional Chinese Locale Mod deployer
#
# Supports:
#   • Linux (native Steam + Proton)
#   • WSL2 (Windows Subsystem for Linux — accesses Windows paths via /mnt/c ...)
#
# Usage:
#   bash deploy.sh [--game-dir PATH] [--dry-run] [--no-backup] [--mode MODE] [--help]
#
# Modes (--mode):
#   loose   (default) Copy data/ loose files + disable EnginLoc.sga
#   sga              Build EnginLocMod.sga from data/font/ and deploy alongside
#                    EnginLoc.sga (no loose files; tests engine SGA priority)
#
# What it does:
#   1. Auto-detect the game installation directory
#   2. Create a timestamped backup of existing mod targets + EnginLoc.sga
#   3. Apply font-fix via Python (writes patched .fnt files to data/font/)
#   [loose] 4. Copy data/, Engine.ucs to the game's Engine/Locale/Chinese/
#   [loose] 5. Disable EnginLoc.sga (rename to .disabled) so game loads data/
#   [sga]   4. Build EnginLocMod.sga from data/font/ using Archive.exe
#   [sga]   5. Copy EnginLocMod.sga to Engine/Locale/Chinese/ (EnginLoc.sga stays enabled)
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
DEPLOY_MODE="loose"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="${REPO_ROOT}/backup"
MANIFEST_FILE="${BACKUP_DIR}/deploy_manifest_${STAMP}.txt"

# ── Game folder name (case-insensitive search) ────────────────────────────────
GAME_FOLDER_NAME="Dawn of War Definitive Edition"

# ── Files / dirs to deploy (relative to repo root) ───────────────────────────
DEPLOY_DIRS=(data)
DEPLOY_FILES=(Engine.ucs)

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
  --mode MODE       Deployment mode: loose (default) or sga
  --help            Show this help message

Modes:
  loose  Copy data/ loose files; disable EnginLoc.sga  (default)
  sga    Build EnginLocMod.sga; keep EnginLoc.sga active (side-by-side test)

Environment:
  DOW_GAME_DIR      Alternative to --game-dir (env var)
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
        --mode)      DEPLOY_MODE="$2"; shift 2 ;;
        --help|-h)   usage; exit 0 ;;
        *) die "Unknown option: $1 (use --help)" ;;
    esac
done

# Validate mode
case "$DEPLOY_MODE" in
    loose|sga) ;;
    *) die "Invalid --mode '${DEPLOY_MODE}'. Valid values: loose, sga" ;;
esac

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
# WSL path helpers
# ─────────────────────────────────────────────────────────────────────────────

# Convert an absolute Linux path to a Windows UNC path (WSL2 only).
# /home/user/foo → \\wsl.localhost\Ubuntu\home\user\foo
_linux_to_win() {
    local p="$1"
    # Windows drive mounts (/mnt/d/...) → native Windows path (D:\...)
    if [[ "$p" =~ ^/mnt/([a-zA-Z])/(.*)$ ]]; then
        local drive="${BASH_REMATCH[1]^^}"   # uppercase drive letter
        local rest="${BASH_REMATCH[2]}"
        local winpath="${rest//\//\\}"
        printf '%s:\\%s' "$drive" "$winpath"
    else
        # WSL filesystem path → UNC (\\wsl.localhost\Ubuntu\...)
        local unc_root
        if command -v wslpath &>/dev/null; then
            unc_root="$(wslpath -w / 2>/dev/null)"
            unc_root="${unc_root%\\}"   # strip trailing backslash
        else
            unc_root='\\wsl.localhost\Ubuntu'
        fi
        local rel="${p#/}"
        local winrel="${rel//\//\\}"
        # Use printf to avoid zsh echo interpreting \U, \t, etc.
        printf '%s\\%s' "$unc_root" "$winrel"
    fi
}

# Build EnginLocMod.sga from data/font/ and place it in the locale target.
build_and_deploy_sga() {
    local archive_exe="${GAME_DIR}/Archive.exe"
    [[ -f "$archive_exe" ]] || die "Archive.exe not found: ${archive_exe}\nPlease pass --game-dir to point at the DoW DE installation."

    local build_file="${REPO_ROOT}/.copilot_workspace/EnginLocMod.txt"
    local sga_out="${LOCALE_TARGET}/EnginLocMod.sga"
    local font_src="${REPO_ROOT}/data"

    mkdir -p "$(dirname "$build_file")"

    # Write build file with CRLF line endings (required by Archive.exe)
    printf 'Archive\r\nTOCStart alias="data" relativeroot="."\r\nFileSettingsStart  defcompression="1"\r\n    Override wildcard=".*(fnt)$" minsize="-1" maxsize="-1" ct="2"\r\nFileSettingsEnd\r\nTOCEnd\r\n' > "$build_file"

    local win_build win_src win_out
    win_build="$(_linux_to_win "$build_file")"
    win_src="$(_linux_to_win "$font_src")"
    win_out="$(_linux_to_win "$sga_out")"

    log "Building EnginLocMod.sga from data/font/ ..."
    if ! $DRY_RUN; then
        "$archive_exe" -c "$win_build" -r "$win_src" -a "$win_out" -v
        ok "Built and deployed: ${sga_out}"
    else
        warn "[DRY RUN] Would build: ${font_src}/font/*.fnt → ${sga_out}"
    fi
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
printf "Mode: %s\n\n" "$DEPLOY_MODE"

# 1. Resolve game directory
if [[ -z "$GAME_DIR" ]]; then
    log "Auto-detecting game installation..."
    if ! GAME_DIR="$(find_game_dir)"; then
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

# 2. Apply font-fix patches to repo's data/font/ (writes .fnt files locally)
log "Applying font-fix patches (data/font/*.fnt)..."
if ! $DRY_RUN; then
    if command -v uv &>/dev/null; then
        uv run python "${REPO_ROOT}/scripts/apply_font_fix.py" \
            --root "${REPO_ROOT}" \
            --restore-from-bak \
            --mode fallback-only \
            --size 34
    elif command -v python3 &>/dev/null; then
        python3 "${REPO_ROOT}/scripts/apply_font_fix.py" \
            --root "${REPO_ROOT}" \
            --restore-from-bak \
            --mode fallback-only \
            --size 34
    else
        warn "No Python interpreter found; skipping font-fix patch step."
        warn "Install uv or python3, then re-run deploy."
    fi
else
    uv run python "${REPO_ROOT}/scripts/apply_font_fix.py" \
        --root "${REPO_ROOT}" \
        --restore-from-bak \
        --mode fallback-only \
        --size 34 \
        --dry-run 2>/dev/null || true
fi

# 3. Backup existing files in the target
if ! $NO_BACKUP && ! $DRY_RUN; then
    log "Creating backup (${BACKUP_DIR}/${STAMP}/)..."
    mkdir -p "${BACKUP_DIR}/${STAMP}"
    echo "deploy_timestamp=${STAMP}" > "$MANIFEST_FILE"
    echo "game_dir=${GAME_DIR}" >> "$MANIFEST_FILE"
    echo "locale_target=${LOCALE_TARGET}" >> "$MANIFEST_FILE"
    echo "---files---" >> "$MANIFEST_FILE"

    # Backup deployed dirs
    for d in "${DEPLOY_DIRS[@]}"; do
        [[ -d "${LOCALE_TARGET}/${d}" ]] && backup_item "${LOCALE_TARGET}/${d}" || true
    done
    # Backup deployed files
    for f in "${DEPLOY_FILES[@]}"; do
        [[ -f "${LOCALE_TARGET}/${f}" ]] && backup_item "${LOCALE_TARGET}/${f}" || true
    done
    # Backup EnginLoc.sga if present (will be disabled)
    for sga_name in EnginLoc.sga EnginLoc.sga.disabled; do
        [[ -f "${LOCALE_TARGET}/${sga_name}" ]] && backup_item "${LOCALE_TARGET}/${sga_name}" || true
    done

    ok "Backup written to ${BACKUP_DIR}/${STAMP}/"
fi

# 4 / 5. Mode-dependent file deployment
if [[ "$DEPLOY_MODE" == "loose" ]]; then
    # 4. Copy mod directories (loose files)
    for d in "${DEPLOY_DIRS[@]}"; do
        local_src="${REPO_ROOT}/${d}"
        [[ -d "$local_src" ]] || { warn "Source dir missing, skipping: $local_src"; continue; }

        log "Deploying ${d}/ → ${LOCALE_TARGET}/${d}/"
        if ! $DRY_RUN; then
            rsync -a --exclude="*.bak" "${local_src}/" "${LOCALE_TARGET}/${d}/"
        else
            rsync -a --dry-run --exclude="*.bak" "${local_src}/" "${LOCALE_TARGET}/${d}/" | grep -v "^sending" || true
        fi
    done

    # 5. Copy mod files
    for f in "${DEPLOY_FILES[@]}"; do
        local_src="${REPO_ROOT}/${f}"
        [[ -f "$local_src" ]] || { warn "Source file missing, skipping: $local_src"; continue; }

        log "Deploying ${f} → ${LOCALE_TARGET}/${f}"
        if ! $DRY_RUN; then
            cp -f "$local_src" "${LOCALE_TARGET}/${f}"
        fi
    done
elif [[ "$DEPLOY_MODE" == "sga" ]]; then
    # 4. Build + deploy EnginLocMod.sga from data/font/ (fonts only in SGA)
    build_and_deploy_sga

    # Also deploy non-font data/ subdirs (art, sound) as loose files
    for subdir in art sound; do
        local_src="${REPO_ROOT}/data/${subdir}"
        [[ -d "$local_src" ]] || continue
        log "Deploying data/${subdir}/ → ${LOCALE_TARGET}/data/${subdir}/"
        if ! $DRY_RUN; then
            mkdir -p "${LOCALE_TARGET}/data/${subdir}"
            rsync -a --exclude="*.bak" "${local_src}/" "${LOCALE_TARGET}/data/${subdir}/"
        else
            rsync -a --dry-run --exclude="*.bak" "${local_src}/" "${LOCALE_TARGET}/data/${subdir}/" | grep -v "^sending" || true
        fi
    done

    # Deploy Engine.ucs (always needed, regardless of mode)
    for f in "${DEPLOY_FILES[@]}"; do
        local_src="${REPO_ROOT}/${f}"
        [[ -f "$local_src" ]] || { warn "Source file missing, skipping: $local_src"; continue; }
        log "Deploying ${f} → ${LOCALE_TARGET}/${f}"
        if ! $DRY_RUN; then
            cp -f "$local_src" "${LOCALE_TARGET}/${f}"
        fi
    done
fi

# 6. Migrate campaign states: copy SC save progress into TC state slots
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
if ! _run_migration; then
    warn "Campaign state migration returned a non-zero exit — check output above."
    warn "Your save files are unchanged; deploy will continue."
fi

# 7. Manage EnginLoc.sga state based on deploy mode
SGA_PATH="${LOCALE_TARGET}/EnginLoc.sga"
SGA_DISABLED="${LOCALE_TARGET}/EnginLoc.sga.disabled"

if [[ "$DEPLOY_MODE" == "loose" ]]; then
    # Disable original SGA so game loads loose data/ files instead
    if [[ -f "$SGA_PATH" ]]; then
        log "Disabling ${SGA_PATH} (renaming to .disabled)..."
        if ! $DRY_RUN; then
            mv "$SGA_PATH" "$SGA_DISABLED"
            ok "Renamed EnginLoc.sga → EnginLoc.sga.disabled"
        else
            warn "[DRY RUN] Would rename: EnginLoc.sga → EnginLoc.sga.disabled"
        fi
    elif [[ -f "$SGA_DISABLED" ]]; then
        ok "EnginLoc.sga already disabled (EnginLoc.sga.disabled exists)"
    else
        warn "EnginLoc.sga not found — game may still load stale packed locale"
    fi
elif [[ "$DEPLOY_MODE" == "sga" ]]; then
    # Ensure EnginLoc.sga is active (our SGA runs alongside it)
    if [[ -f "$SGA_DISABLED" ]]; then
        log "Re-enabling EnginLoc.sga for sga mode..."
        if ! $DRY_RUN; then
            mv "$SGA_DISABLED" "$SGA_PATH"
            ok "Renamed EnginLoc.sga.disabled → EnginLoc.sga"
        else
            warn "[DRY RUN] Would rename: EnginLoc.sga.disabled → EnginLoc.sga"
        fi
    elif [[ -f "$SGA_PATH" ]]; then
        ok "EnginLoc.sga already active"
    else
        warn "EnginLoc.sga not found in either state"
    fi
fi

# 8. Record deployment state for uninstall
if ! $DRY_RUN; then
    DEPLOY_STATE="${REPO_ROOT}/.copilot_workspace/last_deploy.env"
    mkdir -p "$(dirname "$DEPLOY_STATE")"
    cat > "$DEPLOY_STATE" <<ENVEOF
GAME_DIR="${GAME_DIR}"
LOCALE_TARGET="${LOCALE_TARGET}"
BACKUP_STAMP=${STAMP}
BACKUP_DIR="${BACKUP_DIR}/${STAMP}"
DEPLOY_MODE=${DEPLOY_MODE}
ENVEOF
    ok "Deploy state saved: ${DEPLOY_STATE}"
fi

printf "\n${GREEN}${BOLD}Deployment complete!${RESET}\n"
printf "  Launch DoW:DE and verify Chinese text rendering.\n"
printf "  To revert: bash uninstall.sh  (or: make uninstall)\n\n"
