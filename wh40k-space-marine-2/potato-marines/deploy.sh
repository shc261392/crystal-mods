#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# potato-marines - Space Marine 2 aggressive FPS mod - deploy (Linux / WSL2)
#
# Builds dist/potato-marines.pak (if missing) and installs it into the game's
# official mods folder (client_pc/root/mods/), writing pak_config.yaml.
#
# NOTE: any mod disables public matchmaking (private lobbies only, separate
# progression, "MODS DETECTED" watermark). This mod is accepted as such.
#
# Usage: ./deploy.sh [--game-path DIR]
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
[[ -d "$MODS_DIR" ]] || { echo "mods dir not found: $MODS_DIR" >&2; exit 1; }
echo "Game install:  $GAME_DIR"
echo "Mods dir:      $MODS_DIR"

# ── build pak if missing ──────────────────────────────────────────────────
PAK="$SCRIPT_DIR/dist/$PAK_NAME"
if [[ ! -f "$PAK" ]]; then
  echo "$PAK_NAME missing - building..."
  ( cd "$SCRIPT_DIR" && python3 scripts/build_pak.py )
fi

# ── backup existing game-side artifacts (non-destructive) ─────────────────
CFG_DIR="$GAME_DIR/client_pc/root/config/pc"
CFG="$CFG_DIR/game.cfg"
TS="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$BACKUP_ROOT/$TS"
mkdir -p "$BACKUP_DIR"
MANIFEST="$BACKUP_DIR/MANIFEST.txt"
echo "# potato-marines deploy backup $TS" > "$MANIFEST"
echo "# source: $MODS_DIR" >> "$MANIFEST"
if [[ -f "$MODS_DIR/$PAK_NAME" ]]; then
  cp -f "$MODS_DIR/$PAK_NAME" "$BACKUP_DIR/$PAK_NAME.prev"
  echo "$PAK_NAME" >> "$MANIFEST"
fi
if [[ -f "$MODS_DIR/pak_config.yaml" ]]; then
  cp -f "$MODS_DIR/pak_config.yaml" "$BACKUP_DIR/pak_config.yaml.prev"
  echo "pak_config.yaml" >> "$MANIFEST"
fi
if [[ -f "$CFG" ]]; then
  cp -f "$CFG" "$BACKUP_DIR/game.cfg.prev"
  echo "game.cfg" >> "$MANIFEST"
fi

# ── install pak ───────────────────────────────────────────────────────────
cp -f "$PAK" "$MODS_DIR/$PAK_NAME"
echo "installed $MODS_DIR/$PAK_NAME"

CONFIG="$MODS_DIR/pak_config.yaml"
if [[ ! -f "$CONFIG" ]]; then
  printf -- "- pak: %s\n" "$PAK_NAME" > "$CONFIG"
elif ! grep -q "$PAK_NAME" "$CONFIG"; then
  printf -- "- pak: %s\n" "$PAK_NAME" >> "$CONFIG"
fi
echo "pak_config.yaml ready: $CONFIG"

# ── install engine config (game.cfg) ──────────────────────────────────────
mkdir -p "$CFG_DIR"
cp -f "$SCRIPT_DIR/data/game.cfg" "$CFG"
echo "installed engine config: $CFG"

cat <<EOF

===============================================================
 potato-marines installed - aggressive FPS (poor-PC) config
===============================================================
PAK (verified loading): swarm 0.7->0.2, gibs 23/43->6/12, ragdolls
  5/15->0/2, corpses 40->8, gore 65->12.

ENGINE CONFIG (game.cfg - experimental): disables SSAO/SSR/RTAO/DOF/
  water-sim/covering/capsule+screen-space shadows/dissolve/distortion,
  floors FogVolume+Lightshaft+Shadow+Effects+Details quality, caps
  engine workers to 8, enables anim/morpheme batching.

> VERIFY: if game.cfg is parsed, the scene looks flat (no AO), no
> depth-of-field, harsher shadows. If the game looks UNCHANGED, the
> game.cfg format wasn't read (delete it and tell us).
> Revert anytime: rm "$CFG" and ./uninstall.sh

IN-GAME also set: SSAO=OFF, SSR=OFF, Motion Blur=OFF (the menu allows
OFF for SSAO/SSR), Quality Preset=Low, Dynamic Resolution ON target
120, Frame Generation FSR3 ON.

> Mod active: private lobbies only, separate progression, watermark.
===============================================================
EOF