#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# fps-boost - CPU-core aggression for Space Marine 2 under Proton/Linux
#
# Applies to the running (or about-to-run) game:
#   1. Pins the game process to the physical cores 0-7 (disables SMT for it).
#   2. Switches the CPU governor to 'performance' (best-effort).
# Keeps public matchmaking (OS-level, invisible to the game/EAC).
#
# Usage: bash scripts/launch-sm2.sh [game_pid]
#   With no args it finds the game process itself (pgrep).
# ---------------------------------------------------------------------------
set -euo pipefail

GAME_NAME="Warhammer 40000 Space Marine 2 - Retail"
MASK_CPUS="0-7"   # physical cores on a typical 8-core/16-thread CPU under Linux

# 1. CPU governor -> performance (best-effort, needs root)
if command -v cpupower >/dev/null 2>&1 && [ "$(id -u)" -eq 0 ]; then
  cpupower frequency-set -g performance >/dev/null 2>&1 && echo "governor -> performance" || true
fi

# 2. affinity on the game pid
PID="${1:-}"
if [[ -z "$PID" ]]; then
  PID="$(pgrep -f "$GAME_NAME" | head -1 || true)"
fi
if [[ -n "$PID" ]]; then
  taskset -p -c "$MASK_CPUS" "$PID"
  echo "pinned PID $PID to CPUs $MASK_CPUS"
else
  echo "Game not running yet. Launch it (Steam -> Play), then re-run:"
  echo "  bash scripts/launch-sm2.sh"
  echo "Or start it pinned directly (game must not already be running):"
  echo "  taskset -c $MASK_CPUS \"<SteamLibrary>/Space Marine 2/Warhammer 40000 Space Marine 2.exe\""
fi