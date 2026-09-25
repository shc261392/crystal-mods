#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Over 40000 - DoW DE power-cheat mod - build (Linux / WSL2)
#
# Builds the COMPLETE release zip set (both variants) with NO content args:
#   dist/over-40000-v0.1.7.zip                  (resource cheat on)
#   dist/over-40000-v0.1.7-normal-resources.zip (no resource cheat)
#
# Deterministic per AGENTS.md hard rule 15: same commit + same game data
# always produce the same zips. This script only forwards infrastructure
# path overrides to `make build`; content args are forbidden.
#
# Usage: bash build.sh [--game-dir PATH] [--extract-root PATH]
# ---------------------------------------------------------------------------
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

GAME_DIR="${DOW_GAME_DIR:-}"
EXTRACT_ROOT="${EXTRACT_ROOT:-../../.copilot_workspace/extract}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --game-dir) GAME_DIR="$2"; shift 2 ;;
        --extract-root) EXTRACT_ROOT="$2"; shift 2 ;;
        *) echo "Unknown arg: $1 (only --game-dir / --extract-root allowed)" >&2; exit 2 ;;
    esac
done

MAKE_ARGS=("EXTRACT_ROOT=$EXTRACT_ROOT")
[[ -n "$GAME_DIR" ]] && MAKE_ARGS+=("GAME_DIR=$GAME_DIR")
make build "${MAKE_ARGS[@]}"