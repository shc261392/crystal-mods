#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# fps-boost - Space Marine 2 potato-mode config (Linux / WSL2)
#
# Non-mod configuration that keeps public matchmaking. Applies:
#   1. Windows power plan -> Ultimate Performance (when running under WSL2;
#      needs powershell.exe available).
#   2. Prints the in-game + CPU-core config guide.
#   3. Provides scripts/launch-sm2.sh for CPU affinity/governor under Proton.
#
# No game files are modified. Nothing is installed into the game folder.
#
# Usage: ./deploy.sh [--game-path DIR]
# Env:   SM2_GAME_PATH
# ---------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

GAME_DIR=""
usage() { echo "usage: $0 [--game-path DIR]" >&2; exit 2; }
while [[ $# -gt 0 ]]; do
  case "$1" in
    --game-path) GAME_DIR="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "unknown arg: $1" >&2; usage ;;
  esac
done

# ── game install detection (informational) ────────────────────────────────
STEAM_DIRS=(
  "$HOME/.steam/steam"
  "$HOME/.local/share/Steam"
  "$HOME/.var/app/com.valvesoftware.Steam/.local/share/Steam"
  "/mnt/c/Program Files (x86)/Steam"
  "/mnt/d/SteamLibrary"
  "/mnt/e/SteamLibrary"
)
detect_game_dir() {
  local steam_dir vdf lib cand
  for steam_dir in "${STEAM_DIRS[@]}"; do
    vdf="$steam_dir/steamapps/libraryfolders.vdf"
    if [[ -f "$vdf" ]]; then
      while IFS= read -r lib; do
        cand="$lib/steamapps/common/Space Marine 2"
        [[ -d "$cand/client_pc" ]] && { echo "$cand"; return 0; }
      done < <(grep -oE '"path"[[:space:]]+"[^"]+"' "$vdf" | sed -E 's/.*"path"[[:space:]]+"([^"]+)"/\1/; s|\\\\|/|g')
    fi
    cand="$steam_dir/steamapps/common/Space Marine 2"
    [[ -d "$cand/client_pc" ]] && { echo "$cand"; return 0; }
  done
  return 1
}
if [[ -n "$GAME_DIR" ]]; then
  [[ -d "$GAME_DIR/client_pc" ]] || { echo "game dir not found: $GAME_DIR" >&2; exit 1; }
elif [[ -n "${SM2_GAME_PATH:-}" ]]; then
  GAME_DIR="$SM2_GAME_PATH"
  [[ -d "$GAME_DIR/client_pc" ]] || { echo "SM2_GAME_PATH invalid: $GAME_DIR" >&2; exit 1; }
else
  GAME_DIR="$(detect_game_dir || true)"
  [[ -n "$GAME_DIR" ]] || { echo "could not auto-detect the game (informational only)." >&2; GAME_DIR=""; }
fi
[[ -n "$GAME_DIR" ]] && echo "Game install:  $GAME_DIR"

# ── power plan (WSL2 -> Windows) ──────────────────────────────────────────
if command -v powershell.exe >/dev/null 2>&1; then
  if powershell.exe -NoProfile -Command 'powercfg /setactive e9a42b02-d5df-448d-aa00-03f14749eb61' >/dev/null 2>&1; then
    echo "Windows power plan -> Ultimate Performance (best effort)."
  else
    echo "Could not set Ultimate Performance power plan (run this terminal as Administrator once)."
  fi
else
  echo "powershell.exe not found (running native Linux?). Use 'cpupower frequency-set -g performance' for the governor."
fi

cat <<EOF

===============================================================
 fps-boost - potato-mode config (keeps public matchmaking)
===============================================================
IN-GAME (Options -> Graphics):
  Upscaling          = DLSS Quality
  Frame Generation   = FSR 3 ON      <- the 120 lever on a CPU-pinned rig
  FPS cap            = 120
  Dynamic Resolution = ON, target 120
  Details/Effects/Fog Volume = Low, Swarm/Physics/Cloth = Low
  NVIDIA Reflex      = On

CPU CORE AGGRESSION (OS-level, EAC-safe):
  Windows: while the game runs -> admin PowerShell:
      .\\scripts\\apply-affinity.ps1        (pins to physical cores, High priority)
  Proton : bash scripts/launch-sm2.sh        (taskset physical cores + governor)

OPTIONAL - Lossless Scaling (you own it): LSFG 3.0 frame-gen on top,
  instead of the game's FSR3 FG (not both).

Expected on 5800X + 3090: ~90-120 displayed FPS in full swarms.
Docs: docs/settings-preset.md, docs/engine-analysis.md
===============================================================
EOF