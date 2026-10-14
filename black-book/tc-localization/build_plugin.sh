#!/usr/bin/env bash
# Build the Black Book TC Font BepInEx plugin.
#
# Downloads the pinned BepInEx reference assemblies into .bepinex-refs/ (gitignored)
# and compiles plugin/ against them and the game's own Managed folder.
#
# Usage:
#   bash build_plugin.sh [--game-path PATH]
#
# Requires: dotnet SDK (any version able to target netstandard2.0), curl, unzip.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$SCRIPT_DIR/plugin"
REF_DIR="$SCRIPT_DIR/.bepinex-refs"

BEPINEX_VERSION="5.4.23.5"
BEPINEX_URL="https://github.com/BepInEx/BepInEx/releases/download/v${BEPINEX_VERSION}/BepInEx_win_x64_${BEPINEX_VERSION}.zip"
# Pinned so the reference build is reproducible (AGENTS.md rule 15).
BEPINEX_SHA256="82f9878551030f54657792c0740d9d51a09500eeae1fba21106b0c441e6732c4"

GAME_DIR="${GAME_PATH:-}"

STEAM_ROOTS=(
  "$HOME/.steam/steam"
  "/mnt/c/Program Files (x86)/Steam"
  "/mnt/d/SteamLibrary"
  "/mnt/e/SteamLibrary"
  "/mnt/g/SteamLibrary"
)

log() { echo "[$(date '+%H:%M:%S')] $*"; }
die() { echo "[ERROR] $*" >&2; exit 1; }

locate_game() {
  if [[ -n "$GAME_DIR" ]]; then
    [[ -d "$GAME_DIR/Black Book_Data/Managed" ]] || die "Not a Black Book folder: $GAME_DIR"
    echo "$GAME_DIR"; return
  fi
  local root path
  for root in "${STEAM_ROOTS[@]}"; do
    [[ -d "$root" ]] || continue
    for path in "$root/steamapps/common/Black Book" "$root/steamapps/common/black-book"; do
      if [[ -f "$path/Black Book.exe" ]]; then echo "$path"; return; fi
    done
  done
  die "Black Book not found. Pass --game-path or set GAME_PATH."
}

main() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --game-path) GAME_DIR="${2:?}"; shift 2 ;;
      *) die "Unknown option: $1" ;;
    esac
  done

  command -v dotnet >/dev/null || die "dotnet SDK not found on PATH"
  command -v curl   >/dev/null || die "curl not found"
  command -v unzip  >/dev/null || die "unzip not found"

  local game; game="$(locate_game)"
  log "Game: $game"

  if [[ ! -f "$REF_DIR/BepInEx/core/BepInEx.dll" ]]; then
    log "Fetching BepInEx ${BEPINEX_VERSION} reference assemblies..."
    mkdir -p "$REF_DIR"
    local tmp="$REF_DIR/bepinex.zip"
    curl -fsSL -o "$tmp" "$BEPINEX_URL"

    local actual
    actual="$(sha256sum "$tmp" | cut -d' ' -f1)"
    if [[ "$actual" != "$BEPINEX_SHA256" ]]; then
      rm -f "$tmp"
      die "BepInEx archive checksum mismatch (expected $BEPINEX_SHA256, got $actual)"
    fi
    log "  checksum OK"

    rm -rf "$REF_DIR/BepInEx" "$REF_DIR/winhttp.dll" "$REF_DIR/doorstop_config.ini"
    unzip -oq "$tmp" -d "$REF_DIR"
    rm -f "$tmp"
  fi

  log "Compiling plugin..."
  dotnet build "$PLUGIN_DIR/TcFontPlugin.csproj" \
    -c Release --nologo \
    -p:BepInExCore="$REF_DIR/BepInEx/core" \
    -p:GameManaged="$game/Black Book_Data/Managed"

  local dll="$PLUGIN_DIR/bin/Release/BlackBookTcFont.dll"
  [[ -f "$dll" ]] || die "Build produced no DLL at $dll"
  log "Built: $dll ($(stat -c%s "$dll") bytes)"
}

main "$@"