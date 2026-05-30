#!/usr/bin/env bash
# =============================================================================
# uninstall.sh — Suzerain zh-TW localisation uninstaller (Linux / WSL2)
#
# Restores the original EntityTextAssets bundle from the most recent backup
# created by deploy.sh. Use --backup to restore a specific stamped backup.
#
# Usage:
#   bash uninstall.sh [--game-dir PATH] [--backup STAMP] [--dry-run]
#   bash uninstall.sh --help
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; RESET='\033[0m'
log()  { printf "${CYAN}▶${RESET} %s\n" "$*"; }
ok()   { printf "${GREEN}✓${RESET} %s\n" "$*"; }
warn() { printf "${YELLOW}⚠${RESET}  %s\n" "$*"; }
die()  { printf "${RED}✗${RESET}  %s\n" "$*" >&2; exit 1; }

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GAME_FOLDER_NAME="Suzerain"
AA_REL="Suzerain_Data/StreamingAssets/aa/StandaloneWindows64"
BUNDLE_NAME="defaultlocalgroup_assets_assets_database_entitytextassets.asset_7658ed792f0c4924d06b11829a6c36d1.bundle"
SCENE_GLOB="scenes_scenes_assets_scenes_*.bundle"

GAME_DIR="${SUZERAIN_GAME_DIR:-}"
BACKUP_STAMP=""
DRY_RUN=false

usage() {
    cat <<EOF
Usage: bash uninstall.sh [OPTIONS]

Options:
  --game-dir PATH   Override auto-detected Suzerain install
  --backup STAMP    Restore a specific backup/<STAMP> (default: most recent)
  --dry-run         Show actions without writing
  --help            Show this help

Environment:
  SUZERAIN_GAME_DIR Same as --game-dir
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --game-dir) GAME_DIR="$2"; shift 2 ;;
        --backup)   BACKUP_STAMP="$2"; shift 2 ;;
        --dry-run)  DRY_RUN=true; shift ;;
        --help|-h)  usage; exit 0 ;;
        *)          die "Unknown arg: $1 (try --help)" ;;
    esac
done

# ── Locate backup ────────────────────────────────────────────────────────────
BACKUP_ROOT="${REPO_ROOT}/backup"
[[ -d "${BACKUP_ROOT}" ]] || die "No backups found under ${BACKUP_ROOT}. Nothing to restore."

if [[ -n "${BACKUP_STAMP}" ]]; then
    BACKUP_DIR="${BACKUP_ROOT}/${BACKUP_STAMP}"
else
    BACKUP_DIR="$(find "${BACKUP_ROOT}" -mindepth 1 -maxdepth 1 -type d | sort | tail -1)"
fi
[[ -n "${BACKUP_DIR}" && -d "${BACKUP_DIR}" ]] || die "Backup dir not found: ${BACKUP_DIR}"
BACKUP_BUNDLE="${BACKUP_DIR}/${BUNDLE_NAME}"
[[ -f "${BACKUP_BUNDLE}" ]] || die "Backup bundle missing: ${BACKUP_BUNDLE}"
ok "Backup: ${BACKUP_DIR}"

# ── Determine target (prefer recorded origin, else discover) ─────────────────
discover_game() {
    [[ -n "${GAME_DIR}" ]] && { echo "${GAME_DIR}"; return; }
    local mnt c
    local candidates=()
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
    for c in "${candidates[@]}"; do
        [[ -d "${c}" ]] && { echo "${c}"; return; }
    done
    echo ""
}

if [[ -z "${GAME_DIR}" && -f "${BACKUP_DIR}/origin-dir.txt" ]]; then
    TARGET_DIR="$(< "${BACKUP_DIR}/origin-dir.txt")"
else
    GD="$(discover_game)"
    [[ -n "${GD}" ]] || die "Could not determine game dir. Use --game-dir."
    TARGET_DIR="${GD}/${AA_REL}"
fi
TARGET_BUNDLE="${TARGET_DIR}/${BUNDLE_NAME}"
[[ -d "${TARGET_DIR}" ]] || die "Target dir missing: ${TARGET_DIR}"

# ── Restore ──────────────────────────────────────────────────────────────────
if ${DRY_RUN}; then
    log "[dry-run] cp ${BACKUP_BUNDLE} → ${TARGET_BUNDLE}"
    shopt -s nullglob
    for scene in "${BACKUP_DIR}/"${SCENE_GLOB}; do
        log "[dry-run] cp ${scene} → ${TARGET_DIR}/$(basename "${scene}")"
    done
    shopt -u nullglob
else
    cp -p "${BACKUP_BUNDLE}" "${TARGET_BUNDLE}"
    shopt -s nullglob
    for scene in "${BACKUP_DIR}/"${SCENE_GLOB}; do
        cp -p "${scene}" "${TARGET_DIR}/$(basename "${scene}")"
    done
    shopt -u nullglob
    ok "Restored original bundle → ${TARGET_BUNDLE}"
    ok "Restored original scene bundles → ${TARGET_DIR}/${SCENE_GLOB}"
fi

ok "Done. Suzerain is back to its original (English) text."
