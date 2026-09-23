#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# potato-marines - Space Marine 2 aggressive FPS mod - uninstall (Linux / WSL2)
#
# Removes potato-marines.pak from the game's mods folder and restores the
# previous pak_config.yaml (if one was backed up). Idempotent.
#
# Usage: ./uninstall.sh [--game-path DIR]
# Env:   SM2_GAME_PATH
# ---------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_ROOT="$SCRIPT_DIR/backup"
PAK_NAME="potato-marines.pak"

GAME_DIR=""
usage() { echo "usage: $0 [--game-path DIR]" >&2; exit 2; }
while [[ $# -gt 0 ]]; do
  case "$1" in
    --game-path) GAME_DIR="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "unknown arg: $1" >&2; usage ;;
  esac
done

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
  [[ -n "$GAME_DIR" ]] || { echo "ERROR: could not auto-detect Space Marine 2. Pass --game-path DIR." >&2; exit 1; }
fi
MODS_DIR="$GAME_DIR/client_pc/root/mods"

if [[ -f "$MODS_DIR/$PAK_NAME" ]]; then
  rm -f "$MODS_DIR/$PAK_NAME"
  echo "removed $MODS_DIR/$PAK_NAME"
else
  echo "$PAK_NAME not installed (nothing to remove)." >&2
fi

latest="$(ls -1t "$BACKUP_ROOT" 2>/dev/null | grep -E '^[0-9]{8}-[0-9]{6}$' | head -1)"
if [[ -n "$latest" && -f "$BACKUP_ROOT/$latest/pak_config.yaml.prev" ]]; then
  cp -f "$BACKUP_ROOT/$latest/pak_config.yaml.prev" "$MODS_DIR/pak_config.yaml"
  echo "restored $MODS_DIR/pak_config.yaml from backup $latest"
elif [[ -f "$MODS_DIR/pak_config.yaml" ]]; then
  if grep -q "$PAK_NAME" "$MODS_DIR/pak_config.yaml"; then
    rm -f "$MODS_DIR/pak_config.yaml"
    echo "removed our $MODS_DIR/pak_config.yaml"
  fi
fi

# game.cfg engine config
CFG="$GAME_DIR/client_pc/root/config/pc/game.cfg"
if [[ -n "$latest" && -f "$BACKUP_ROOT/$latest/game.cfg.prev" ]]; then
  cp -f "$BACKUP_ROOT/$latest/game.cfg.prev" "$CFG"
  echo "restored $CFG from backup $latest"
elif [[ -f "$CFG" ]]; then
  rm -f "$CFG"
  echo "removed our $CFG"
fi

echo "Done. Restart the game; private-lobby mode / watermark cleared."