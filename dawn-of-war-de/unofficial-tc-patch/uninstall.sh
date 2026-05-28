#!/usr/bin/env bash
# =============================================================================
# uninstall.sh — WH40K DoW:DE Traditional Chinese Locale Mod reverter
#
# Restores the game to its pre-mod state by:
#   1. Reading the last deploy state from .copilot_workspace/last_deploy.env
#   2. Removing deployed data/ and Engine.ucs from the game's locale folder
#   3. Re-enabling EnginLoc.sga (renaming back from .disabled)
#   4. Optionally restoring from the timestamped backup
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
DEPLOY_MODE="loose"  # overwritten from last_deploy.env

DEPLOY_DIRS=(data)
DEPLOY_FILES=(Engine.ucs)
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

# ── 1. Manage EnginLoc.sga state ───────────────────────────────────────────
SGA_DISABLED="${LOCALE_TARGET}/EnginLoc.sga.disabled"
SGA_ACTIVE="${LOCALE_TARGET}/EnginLoc.sga"

if [[ "$DEPLOY_MODE" == "sga" ]]; then
    # sga mode: EnginLoc.sga was left active; nothing to do for SGA
    ok "EnginLoc.sga was active during sga-mode deploy — no rename needed"
else
    # loose mode: EnginLoc.sga was renamed .disabled; restore it
    if [[ -f "$SGA_DISABLED" ]]; then
        log "Re-enabling EnginLoc.sga..."
        if ! $DRY_RUN; then
            mv "$SGA_DISABLED" "$SGA_ACTIVE"
            ok "Renamed EnginLoc.sga.disabled → EnginLoc.sga"
        else
            warn "[DRY RUN] Would rename EnginLoc.sga.disabled → EnginLoc.sga"
        fi
    elif [[ -f "$SGA_ACTIVE" ]]; then
        ok "EnginLoc.sga already active (not renamed by deploy)"
    else
        warn "EnginLoc.sga not found in either state — skipping"
    fi
fi

# ── 2. Remove deployed data/ ───────────────────────────────────────────────
if [[ "$DEPLOY_MODE" == "sga" ]]; then
    # sga mode: no loose data/ was deployed; remove EnginLocMod.sga instead
    sga_mod="${LOCALE_TARGET}/EnginLocMod.sga"
    if [[ -f "$sga_mod" ]]; then
        log "Removing ${sga_mod}..."
        if ! $DRY_RUN; then
            rm -f "$sga_mod"
            ok "Removed ${sga_mod}"
        else
            warn "[DRY RUN] Would remove: ${sga_mod}"
        fi
    else
        warn "EnginLocMod.sga not found (already removed?): ${sga_mod}"
    fi

    # Remove entire data/ directory (art, sound, and any leftover font/ from
    # a previous loose deploy).  The game locale dir never has a data/ folder
    # natively — everything is in SGAs — so this is always safe.
    data_dir="${LOCALE_TARGET}/data"
    if [[ -d "$data_dir" ]]; then
        log "Removing deployed directory: ${data_dir}"
        if ! $DRY_RUN; then
            rm -rf "$data_dir"
            ok "Removed ${data_dir}"
        else
            warn "[DRY RUN] Would remove: ${data_dir}"
        fi
    fi
else
    for d in "${DEPLOY_DIRS[@]}"; do
        target="${LOCALE_TARGET}/${d}"
        if [[ -d "$target" ]]; then
            log "Removing deployed directory: ${target}"
            if ! $DRY_RUN; then
                rm -rf "$target"
                ok "Removed ${target}"
            else
                warn "[DRY RUN] Would remove: ${target}"
            fi
        else
            warn "Directory not found (already removed?): ${target}"
        fi
    done
fi

# ── 3. Remove deployed files ─────────────────────────────────────────────────
# Engine.ucs is required for the game to launch — only remove it when a backup
# exists to restore from.  Without a backup the file must be left in place.
for f in "${DEPLOY_FILES[@]}"; do
    target="${LOCALE_TARGET}/${f}"
    if [[ -f "$target" ]]; then
        if [[ -z "$BACKUP_DIR_STORED" || ! -f "${BACKUP_DIR_STORED}/${f}" ]]; then
            warn "Skipping removal of ${f} — no backup to restore; game requires this file"
            continue
        fi
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

# ── 4. Optionally restore from backup ────────────────────────────────────────
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
    warn "(EnginLoc.sga has been re-enabled; game should load original packed locale)"
fi

# ── 5. Clear stored deploy state ─────────────────────────────────────────────
if ! $DRY_RUN && [[ -f "$DEPLOY_STATE" ]]; then
    rm -f "$DEPLOY_STATE"
    ok "Deploy state cleared"
fi

printf "\n${GREEN}${BOLD}Uninstall complete!${RESET}\n"
printf "  The game will now load the original EnginLoc.sga locale archive.\n"
printf "  To re-deploy: bash deploy.sh  (or: make deploy)\n\n"
