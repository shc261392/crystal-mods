#!/usr/bin/env bash
# =============================================================================
# uninstall.sh — WH40K DoW:DE Traditional Chinese Locale Mod reverter
#
# Restores the game to its pre-mod state by:
#   1. Reading the last deploy state from .copilot_workspace/last_deploy.env
#   2. Removing deployed EnginLocMod.sga and Engine.ucs from the game's locale folder
#   3. Optionally restoring from the timestamped backup
#
# Usage:
#   bash uninstall.sh [--game-dir PATH] [--dry-run] [--help]
#   make uninstall
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_STATE="${REPO_ROOT}/.copilot_workspace/last_deploy.env"

GAME_DIR=""
DRY_RUN=false

DEPLOY_FILES=(EnginLocMod.sga Engine.ucs)
LOCALE_SUBPATH="Engine/Locale/Chinese"

log()  { printf "${CYAN}▶${RESET} %s\n" "$*"; }
ok()   { printf "${GREEN}✓${RESET} %s\n" "$*"; }
warn() { printf "${YELLOW}⚠${RESET}  %s\n" "$*"; }
err()  { printf "${RED}✗${RESET}  %s\n" "$*" >&2; }
die()  { err "$*"; exit 1; }

usage() {
    cat <<EOF
Usage: bash uninstall.sh [OPTIONS]

Reverts a previous mod deployment. Reads deploy state from
.copilot_workspace/last_deploy.env (written by deploy.sh).

Options:
  --game-dir PATH   Override the stored game directory
  --dry-run         Show what would be removed without writing anything
  --help            Show this help message
EOF
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --game-dir)  GAME_DIR="$2"; shift 2 ;;
        --dry-run)   DRY_RUN=true; shift ;;
        --help|-h)   usage; exit 0 ;;
        *) die "Unknown option: $1 (use --help)" ;;
    esac
done

printf "\n${BOLD}WH40K DoW:DE — Traditional Chinese Locale Mod Uninstaller${RESET}\n\n"

# ── Load stored deploy state ─────────────────────────────────────────────────
BACKUP_STAMP=""
BACKUP_DIR_STORED=""

if [[ -f "$DEPLOY_STATE" ]]; then
    # shellcheck disable=SC1090
    source "$DEPLOY_STATE"
    BACKUP_STAMP="${BACKUP_STAMP:-}"
    BACKUP_DIR_STORED="${BACKUP_DIR:-}"
    DEPLOY_MODE="${DEPLOY_MODE:-loose}"
    [[ -z "$GAME_DIR" ]] && GAME_DIR="${GAME_DIR:-}"  # already set from state
    log "Loaded deploy state: ${DEPLOY_STATE} (mode=${DEPLOY_MODE})"
else
    warn "No deploy state found at ${DEPLOY_STATE}"
    warn "Falling back to DOW_GAME_DIR env var or --game-dir flag."
fi

# Allow CLI / env override
[[ -n "${DOW_GAME_DIR:-}" && -z "$GAME_DIR" ]] && GAME_DIR="$DOW_GAME_DIR"

if [[ -z "$GAME_DIR" ]]; then
    err "Could not determine game directory."
    err "Either re-run deploy.sh first, or pass --game-dir PATH."
    exit 1
fi

LOCALE_TARGET="${GAME_DIR}/${LOCALE_SUBPATH}"
[[ -d "$LOCALE_TARGET" ]] || die "Locale directory not found: $LOCALE_TARGET"

printf "Target: %s\n" "$LOCALE_TARGET"
$DRY_RUN && printf "${YELLOW}[DRY RUN — no files will be written]${RESET}\n"
printf "\n"

# ── 0. Sync TC mod progress back to SC state slots (before removing mod) ─────
#    If the user made progress while the TC mod was active, this copies it
#    back into the original SC (Simplified Chinese) campaign state files so
#    progress is not lost when returning to the vanilla locale.
log "Syncing TC campaign progress back to SC state slots..."
_run_reverse_migration() {
    local py_runner
    if command -v uv &>/dev/null; then
        py_runner="uv run python"
    elif command -v python3 &>/dev/null; then
        py_runner="python3"
    else
        warn "No Python interpreter found; skipping campaign state sync."
        warn "Run manually: python scripts/migrate_campaign_states.py --reverse"
        return 0
    fi

    local extra_flags=(--reverse)
    $DRY_RUN && extra_flags+=(--dry-run)

    $py_runner "${REPO_ROOT}/scripts/migrate_campaign_states.py" \
        --profile Profile1 \
        "${extra_flags[@]}" \
        2>&1 | while IFS= read -r line; do printf "    %s\n" "$line"; done
}
if ! _run_reverse_migration; then
    warn "Campaign state sync returned a non-zero exit — check output above."
    warn "Your save files are unchanged; uninstall will continue."
fi

# ── 1. Remove deployed files ─────────────────────────────────────────────────
for f in "${DEPLOY_FILES[@]}"; do
    target="${LOCALE_TARGET}/${f}"
    if [[ -f "$target" ]]; then
        log "Removing deployed file: ${target}"
        if ! $DRY_RUN; then
            rm -f "$target"
            ok "Removed ${target}"
        else
            warn "[DRY RUN] Would remove: ${target}"
        fi
    else
        warn "File not found (already removed?): ${target}"
    fi
done

# ── 2. Optionally restore from backup ────────────────────────────────────────
if [[ -n "$BACKUP_DIR_STORED" && -d "$BACKUP_DIR_STORED" ]]; then
    log "Restoring backup from ${BACKUP_DIR_STORED} ..."
    if ! $DRY_RUN; then
        rsync -a "${BACKUP_DIR_STORED}/" "${LOCALE_TARGET}/"
        ok "Backup restored to ${LOCALE_TARGET}"
    else
        warn "[DRY RUN] Would restore from ${BACKUP_DIR_STORED}"
    fi
else
    warn "No backup directory found — skipping restore step"
    warn "(Game will load vanilla EnginLoc.sga)"
fi

# ── 3. Clear stored deploy state ─────────────────────────────────────────────
if ! $DRY_RUN && [[ -f "$DEPLOY_STATE" ]]; then
    rm -f "$DEPLOY_STATE"
    ok "Deploy state cleared"
fi

printf "\n${GREEN}${BOLD}Uninstall complete!${RESET}\n"
printf "  The game will now load the original EnginLoc.sga locale archive.\n"
printf "  To re-deploy: bash uninstall.sh  (or: make deploy)\n\n"
