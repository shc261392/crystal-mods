#!/usr/bin/env bash
set -euo pipefail

# Deploy one generated bisect SGA as EnginLoc.sga, keeping backups in backup/bisect/<timestamp>/
# Usage:
#   bash scripts/deploy_bisect_sga.sh 03_gfx_only
#   bash scripts/deploy_bisect_sga.sh 00_baseline_moducs_modsound_vanilla_font_art

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKSPACE_ROOT="$(cd "${REPO_ROOT}/../.." && pwd)"
BISECT_DIR="${WORKSPACE_ROOT}/.copilot_workspace/dowde_campaign_bisect_20260608/sga"

CASE_NAME="${1:-}"
if [[ -z "${CASE_NAME}" ]]; then
  echo "Usage: bash scripts/deploy_bisect_sga.sh <case-name>"
  echo "Available SGAs in: ${BISECT_DIR}"
  ls -1 "${BISECT_DIR}" 2>/dev/null || true
  exit 1
fi

SGA_SRC="${BISECT_DIR}/EnginLocBisect_${CASE_NAME}.sga"
[[ -f "${SGA_SRC}" ]] || { echo "Missing case SGA: ${SGA_SRC}"; exit 1; }

find_game_dir() {
  local paths=(
    "/mnt/d/SteamLibrary/steamapps/common/Dawn of War Definitive Edition"
    "/mnt/c/Program Files (x86)/Steam/steamapps/common/Dawn of War Definitive Edition"
    "$HOME/.local/share/Steam/steamapps/common/Dawn of War Definitive Edition"
    "$HOME/.steam/steamapps/common/Dawn of War Definitive Edition"
  )
  for p in "${paths[@]}"; do
    [[ -d "$p" ]] && { echo "$p"; return 0; }
  done
  return 1
}

GAME_DIR="${DOW_GAME_DIR:-}"
if [[ -z "${GAME_DIR}" ]]; then
  GAME_DIR="$(find_game_dir)" || { echo "Cannot auto-detect game dir. Set DOW_GAME_DIR."; exit 1; }
fi

LOCALE_DIR="${GAME_DIR}/Engine/Locale/Chinese"
[[ -d "${LOCALE_DIR}" ]] || { echo "Missing locale dir: ${LOCALE_DIR}"; exit 1; }

STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="${REPO_ROOT}/backup/bisect/${STAMP}_${CASE_NAME}"
mkdir -p "${BACKUP_DIR}"

# Backup current live files in Chinese locale only
[[ -f "${LOCALE_DIR}/EnginLoc.sga" ]] && cp -a "${LOCALE_DIR}/EnginLoc.sga" "${BACKUP_DIR}/EnginLoc.sga"
[[ -f "${LOCALE_DIR}/Engine.ucs" ]] && cp -a "${LOCALE_DIR}/Engine.ucs" "${BACKUP_DIR}/Engine.ucs"

# Deploy bisect SGA + mod Engine.ucs baseline requirement
cp -f "${SGA_SRC}" "${LOCALE_DIR}/EnginLoc.sga"
cp -f "${REPO_ROOT}/Engine.ucs" "${LOCALE_DIR}/Engine.ucs"

echo "Deployed case: ${CASE_NAME}"
echo "  SGA: ${SGA_SRC} -> ${LOCALE_DIR}/EnginLoc.sga"
echo "  UCS: ${REPO_ROOT}/Engine.ucs -> ${LOCALE_DIR}/Engine.ucs"
echo "  Backup: ${BACKUP_DIR}"
