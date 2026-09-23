#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Easy Reinforcement - DoW DE standalone mod - build (Linux / WSL2)
# ---------------------------------------------------------------------------
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

echo "== Easy Reinforcement - build (Linux/WSL2) =="
make -s build
echo "Done."