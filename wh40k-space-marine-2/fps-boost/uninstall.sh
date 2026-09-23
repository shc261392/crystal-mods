#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# fps-boost - Space Marine 2 potato-mode config - uninstall (Linux / WSL2)
#
# Reverts the OS-level changes deploy.sh applied (best effort):
#   - Windows power plan -> Balanced (High performance).
# No game files are touched.
# ---------------------------------------------------------------------------
set -euo pipefail

if command -v powershell.exe >/dev/null 2>&1; then
  if powershell.exe -NoProfile -Command 'powercfg /setactive 381b4222-f694-41f0-9685-ff5bb260df2e' >/dev/null 2>&1; then
    echo "Windows power plan -> Balanced (reverted)."
  else
    echo "Could not revert power plan (run as Administrator)."
  fi
else
  echo "No Windows power plan to revert (native Linux)."
fi
echo "fps-boost deployed no game files, so nothing else to undo."
echo "In-game rows: revert in Options -> Graphics if desired."