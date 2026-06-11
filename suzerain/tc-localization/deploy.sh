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
SCENE_GLOB="scenes_scenes_assets_scenes_*.bundle"

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

shopt -s nullglob
PATCHED_SCENE_BUNDLES=("${REPO_ROOT}/build/"${SCENE_GLOB})
TARGET_SCENE_BUNDLES=("${TARGET_DIR}/"${SCENE_GLOB})
shopt -u nullglob

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
if [[ ${#PATCHED_SCENE_BUNDLES[@]} -eq 0 && ${DRY_RUN} == false ]]; then
    die "Build output is missing scene bundles under ${REPO_ROOT}/build/${SCENE_GLOB}"
fi

# ── Backup ───────────────────────────────────────────────────────────────────
if ! ${NO_BACKUP}; then
    STAMP="$(date +%Y%m%d-%H%M%S)"
    BACKUP_DIR="${REPO_ROOT}/backup/${STAMP}"
    if ${DRY_RUN}; then
        log "[dry-run] would backup original → ${BACKUP_DIR}/${BUNDLE_NAME}"
        for scene in "${TARGET_SCENE_BUNDLES[@]}"; do
            [[ -f "${scene}" ]] || continue
            log "[dry-run] would backup original → ${BACKUP_DIR}/$(basename "${scene}")"
        done
    else
        mkdir -p "${BACKUP_DIR}"
        cp -p "${TARGET_BUNDLE}" "${BACKUP_DIR}/${BUNDLE_NAME}"
        for scene in "${TARGET_SCENE_BUNDLES[@]}"; do
            [[ -f "${scene}" ]] || continue
            cp -p "${scene}" "${BACKUP_DIR}/$(basename "${scene}")"
        done
        # Record the target directory so uninstall can restore all bundles.
        printf '%s\n' "${TARGET_DIR}" > "${BACKUP_DIR}/origin-dir.txt"
        ok "Backup → ${BACKUP_DIR}/${BUNDLE_NAME}"
    fi
fi

# ── Deploy ───────────────────────────────────────────────────────────────────
if ${DRY_RUN}; then
    log "[dry-run] cp ${PATCHED_BUNDLE} → ${TARGET_BUNDLE}"
    for scene in "${PATCHED_SCENE_BUNDLES[@]}"; do
        log "[dry-run] cp ${scene} → ${TARGET_DIR}/$(basename "${scene}")"
    done
else
    cp -p "${PATCHED_BUNDLE}" "${TARGET_BUNDLE}"
    for scene in "${PATCHED_SCENE_BUNDLES[@]}"; do
        cp -p "${scene}" "${TARGET_DIR}/$(basename "${scene}")"
    done
    ok "Deployed patched bundle → ${TARGET_BUNDLE}"
    ok "Deployed patched scene bundles → ${TARGET_DIR}/${SCENE_GLOB}"
fi

# ── Clear Addressables cache ─────────────────────────────────────────────────
CACHE_DIR="${TARGET_DIR}/Cache"
if [[ -d "${CACHE_DIR}" ]]; then
    if ${DRY_RUN}; then
        log "[dry-run] would delete cache: ${CACHE_DIR}"
    else
        rm -rf "${CACHE_DIR}"
        ok "Cleared Addressables cache → ${CACHE_DIR}"
    fi
fi

# ── Clear Unity/Il2CPP runtime cache (platform-specific) ─────────────────────
GAME_DATA_DIR="${GAME_DIR}/Suzerain_Data"
if [[ -d "${GAME_DATA_DIR}" ]]; then
    BUNDLE_CACHE="${GAME_DATA_DIR}/StreamingAssets/aa/AssetBundleCache"
    if [[ -d "${BUNDLE_CACHE}" ]]; then
        if ${DRY_RUN}; then
            log "[dry-run] would delete: ${BUNDLE_CACHE}"
        else
            rm -rf "${BUNDLE_CACHE}"
            ok "Cleared AssetBundleCache → ${BUNDLE_CACHE}"
        fi
    fi
fi

ok "Done. Launch Suzerain and verify the Traditional Chinese text."
warn "Cache was cleared. Game will reload bundles on next start."
