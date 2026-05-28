#!/usr/bin/env bash
# =============================================================================
# deploy.sh — DoW:DE WSAD Camera Keybind deployer (Linux / WSL2)
#
# Installs one of three presets to <game>/Engine/defprofile/:
#   • vanilla            → keydefaults.lua  (stock DoW:DE Classic preset)
#   • wasd-camera        → keydefaults.lua  (replace Classic)
#   • wasd-camera-ingame → keydefaults_modern.lua  (replace Modern slot)
#
# Backs up existing files to ./backup/<stamp>/ before overwriting.
# Idempotent — re-running with the same preset re-applies cleanly.
#
# Usage:
#   bash deploy.sh [--preset NAME] [--game-dir PATH] [--dry-run] [--no-backup]
#   bash deploy.sh --help
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; RESET='\033[0m'
log()  { printf "${CYAN}▶${RESET} %s\n" "$*"; }
ok()   { printf "${GREEN}✓${RESET} %s\n" "$*"; }
warn() { printf "${YELLOW}⚠${RESET}  %s\n" "$*"; }
die()  { printf "${RED}✗${RESET}  %s\n" "$*" >&2; exit 1; }

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GAME_FOLDER_NAME="Dawn of War Definitive Edition"
PRESET="wasd-camera"
GAME_DIR="${DOW_GAME_DIR:-}"
DRY_RUN=false
NO_BACKUP=false

usage() {
    cat <<EOF
Usage: bash deploy.sh [OPTIONS]

Options:
  --preset NAME       vanilla | wasd-camera | wasd-camera-ingame  (default: wasd-camera)
  --game-dir PATH     Override auto-detected game install
  --dry-run           Show actions without writing
  --no-backup         Skip backup (not recommended)
  --help              Show this help

Environment:
  DOW_GAME_DIR        Same as --game-dir
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --preset)    PRESET="$2"; shift 2 ;;
        --game-dir)  GAME_DIR="$2"; shift 2 ;;
        --dry-run)   DRY_RUN=true; shift ;;
        --no-backup) NO_BACKUP=true; shift ;;
        --help|-h)   usage; exit 0 ;;
        *)           die "Unknown arg: $1 (try --help)" ;;
    esac
done

PRESET_DIR="${REPO_ROOT}/presets/${PRESET}"
[[ -d "${PRESET_DIR}" ]] || die "Preset not found: ${PRESET} (expected ${PRESET_DIR})"

# ── Game discovery (WSL-aware) ───────────────────────────────────────────────
discover_game() {
    [[ -n "${GAME_DIR}" ]] && { echo "${GAME_DIR}"; return; }
    local candidates=()
    local mnt
    for mnt in /mnt/c /mnt/d /mnt/e /mnt/f /mnt/g; do
        [[ -d "${mnt}" ]] || continue
        candidates+=(
            "${mnt}/Program Files (x86)/Steam/steamapps/common/${GAME_FOLDER_NAME}"
            "${mnt}/SteamLibrary/steamapps/common/${GAME_FOLDER_NAME}"
            "${mnt}/Steam/steamapps/common/${GAME_FOLDER_NAME}"
        )
    done
    candidates+=(
        "${HOME}/.steam/steam/steamapps/common/${GAME_FOLDER_NAME}"
        "${HOME}/.local/share/Steam/steamapps/common/${GAME_FOLDER_NAME}"
    )
    local c
    for c in "${candidates[@]}"; do
        [[ -d "${c}" ]] && { echo "${c}"; return; }
    done
    die "Could not auto-detect '${GAME_FOLDER_NAME}'. Use --game-dir."
}

GAME_DIR="$(discover_game)"
ok "Game: ${GAME_DIR}"

TARGET_DIR="${GAME_DIR}/Engine/defprofile"
[[ -d "${TARGET_DIR}" ]] || die "Target dir missing: ${TARGET_DIR}"

# ── Plan files to deploy ─────────────────────────────────────────────────────
mapfile -t SRC_FILES < <(find "${PRESET_DIR}/Engine/defprofile" -maxdepth 1 -type f -name '*.lua')
[[ ${#SRC_FILES[@]} -gt 0 ]] || die "No .lua files under ${PRESET_DIR}/Engine/defprofile"

log "Preset: ${PRESET}  (${#SRC_FILES[@]} file(s))"
for f in "${SRC_FILES[@]}"; do echo "    - $(basename "$f")"; done

# ── Backup ───────────────────────────────────────────────────────────────────
if ! ${NO_BACKUP}; then
    STAMP="$(date +%Y%m%d-%H%M%S)"
    BACKUP_DIR="${REPO_ROOT}/backup/${STAMP}"
    if ${DRY_RUN}; then
        log "[dry-run] would backup to ${BACKUP_DIR}"
    else
        mkdir -p "${BACKUP_DIR}"
        for f in "${SRC_FILES[@]}"; do
            target="${TARGET_DIR}/$(basename "$f")"
            [[ -f "${target}" ]] && cp -p "${target}" "${BACKUP_DIR}/" || true
        done
        ok "Backup → ${BACKUP_DIR}"
    fi
fi

# ── Deploy ───────────────────────────────────────────────────────────────────
for f in "${SRC_FILES[@]}"; do
    name="$(basename "$f")"
    if ${DRY_RUN}; then
        log "[dry-run] cp $f → ${TARGET_DIR}/${name}"
    else
        cp -p "$f" "${TARGET_DIR}/${name}"
        ok "Deployed ${name}"
    fi
done

ok "Done. Launch the game and verify the WSAD bindings."
[[ "${PRESET}" == "wasd-camera-ingame" ]] && \
    log "In-game: Options → Hotkeys → Preset → 'Modern Hotkeys' to activate."
