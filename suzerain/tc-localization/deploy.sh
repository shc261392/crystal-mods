#!/usr/bin/env bash
# =============================================================================
# deploy.sh — Suzerain zh-TW localisation deployer (Linux / WSL2)
#
# Replaces the EntityTextAssets bundle in the game's Addressables folder with
# the patched (translated) bundle from ./build/. Backs up the original bundle
# to ./backup/<stamp>/ before overwriting so uninstall.sh can restore it.
#
# Build the patched bundle first:  make build   (or it is built on demand here)
#
# Usage:
#   bash deploy.sh [--game-dir PATH] [--bundle PATH] [--dry-run] [--no-backup]
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
GAME_FOLDER_NAME="Suzerain"
AA_REL="Suzerain_Data/StreamingAssets/aa/StandaloneWindows64"
BUNDLE_NAME="defaultlocalgroup_assets_assets_database_entitytextassets.asset_7658ed792f0c4924d06b11829a6c36d1.bundle"

GAME_DIR="${SUZERAIN_GAME_DIR:-}"
PATCHED_BUNDLE="${REPO_ROOT}/build/${BUNDLE_NAME}"
DRY_RUN=false
NO_BACKUP=false

usage() {
    cat <<EOF
Usage: bash deploy.sh [OPTIONS]

Options:
  --game-dir PATH     Override auto-detected Suzerain install
  --bundle PATH       Patched bundle to deploy (default: ./build/<bundle>)
  --dry-run           Show actions without writing
  --no-backup         Skip backup (not recommended)
  --help              Show this help

Environment:
  SUZERAIN_GAME_DIR   Same as --game-dir
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --game-dir)  GAME_DIR="$2"; shift 2 ;;
        --bundle)    PATCHED_BUNDLE="$2"; shift 2 ;;
        --dry-run)   DRY_RUN=true; shift ;;
        --no-backup) NO_BACKUP=true; shift ;;
        --help|-h)   usage; exit 0 ;;
        *)           die "Unknown arg: $1 (try --help)" ;;
    esac
done

# ── Game discovery (WSL-aware) ───────────────────────────────────────────────
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
    die "Could not auto-detect '${GAME_FOLDER_NAME}'. Use --game-dir."
}

GAME_DIR="$(discover_game)"
ok "Game: ${GAME_DIR}"

TARGET_DIR="${GAME_DIR}/${AA_REL}"
TARGET_BUNDLE="${TARGET_DIR}/${BUNDLE_NAME}"
[[ -d "${TARGET_DIR}" ]] || die "Addressables dir missing: ${TARGET_DIR}"
[[ -f "${TARGET_BUNDLE}" ]] || die "Original bundle not found: ${TARGET_BUNDLE}"

# ── Ensure patched bundle exists (build on demand) ───────────────────────────
if [[ ! -f "${PATCHED_BUNDLE}" ]]; then
    warn "Patched bundle missing: ${PATCHED_BUNDLE}"
    log  "Building it now (make build)…"
    if ${DRY_RUN}; then
        log "[dry-run] would run: make build GAME_DIR=${GAME_DIR}"
    else
        ( cd "${REPO_ROOT}" && make build GAME_DIR="${GAME_DIR}" )
    fi
fi
[[ -f "${PATCHED_BUNDLE}" || ${DRY_RUN} == true ]] || die "Build did not produce ${PATCHED_BUNDLE}"

# ── Backup ───────────────────────────────────────────────────────────────────
if ! ${NO_BACKUP}; then
    STAMP="$(date +%Y%m%d-%H%M%S)"
    BACKUP_DIR="${REPO_ROOT}/backup/${STAMP}"
    if ${DRY_RUN}; then
        log "[dry-run] would backup original → ${BACKUP_DIR}/${BUNDLE_NAME}"
    else
        mkdir -p "${BACKUP_DIR}"
        cp -p "${TARGET_BUNDLE}" "${BACKUP_DIR}/${BUNDLE_NAME}"
        # Record where it came from so uninstall can restore even without --game-dir.
        printf '%s\n' "${TARGET_BUNDLE}" > "${BACKUP_DIR}/origin.txt"
        ok "Backup → ${BACKUP_DIR}/${BUNDLE_NAME}"
    fi
fi

# ── Deploy ───────────────────────────────────────────────────────────────────
if ${DRY_RUN}; then
    log "[dry-run] cp ${PATCHED_BUNDLE} → ${TARGET_BUNDLE}"
else
    cp -p "${PATCHED_BUNDLE}" "${TARGET_BUNDLE}"
    ok "Deployed patched bundle → ${TARGET_BUNDLE}"
fi

ok "Done. Launch Suzerain and verify the Traditional Chinese text."
warn "If text appears blank/garbled or reverts to English, the Addressables"
warn "catalogue may verify bundle CRC. Run uninstall.sh to restore, and report it."
