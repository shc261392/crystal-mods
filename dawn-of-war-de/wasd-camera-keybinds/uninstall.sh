#!/usr/bin/env bash
# uninstall.sh — restore most recent backup taken by deploy.sh
set -euo pipefail

CYAN='\033[0;36m'; GREEN='\033[0;32m'; RED='\033[0;31m'; RESET='\033[0m'
log() { printf "${CYAN}▶${RESET} %s\n" "$*"; }
ok()  { printf "${GREEN}✓${RESET} %s\n" "$*"; }
die() { printf "${RED}✗${RESET}  %s\n" "$*" >&2; exit 1; }

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GAME_FOLDER_NAME="Dawn of War Definitive Edition"
GAME_DIR="${DOW_GAME_DIR:-${1:-}}"

discover_game() {
    [[ -n "${GAME_DIR}" ]] && { echo "${GAME_DIR}"; return; }
    local mnt c
    for mnt in /mnt/c /mnt/d /mnt/e /mnt/f /mnt/g; do
        [[ -d "${mnt}" ]] || continue
        for c in "${mnt}/Program Files (x86)/Steam/steamapps/common/${GAME_FOLDER_NAME}" \
                 "${mnt}/SteamLibrary/steamapps/common/${GAME_FOLDER_NAME}" \
                 "${mnt}/Steam/steamapps/common/${GAME_FOLDER_NAME}"; do
            [[ -d "${c}" ]] && { echo "${c}"; return; }
        done
    done
    die "Cannot find game; pass path as first arg or set DOW_GAME_DIR."
}

GAME_DIR="$(discover_game)"
TARGET_DIR="${GAME_DIR}/Engine/defprofile"

LATEST="$(ls -1dt "${REPO_ROOT}/backup"/*/ 2>/dev/null | head -1 || true)"
[[ -n "${LATEST}" ]] || die "No backups found under ${REPO_ROOT}/backup/"
log "Restoring from ${LATEST}"

shopt -s nullglob
for f in "${LATEST}"*.lua; do
    name="$(basename "$f")"
    cp -p "$f" "${TARGET_DIR}/${name}"
    ok "Restored ${name}"
done

ok "Done."
