#!/usr/bin/env bash
# Build Red Laser Lasgun and package it as a Vortex-installable zip.
#
# The zip lays the plugin at BepInEx/plugins/RedLaserLasgun.dll — the Battlesector
# Vortex extension recognises BepInEx/ as a game-root dir (Layout A) and deploys
# it to <game>/BepInEx/plugins/. BepInEx core itself is NOT shipped; install the
# BepInEx Framework mod first (it provides the runtime).
#
# Usage: ./package.sh   (override GameDir for the interop refs if needed)
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
DIST="$HERE/../dist"
VERSION="$(grep -oP '"version"\s*:\s*"\K[^"]+' "$HERE/modinfo.json")"
NAME="red-laser-lasgun"

echo "[1/3] dotnet build -c Release"
dotnet build "$HERE/RedLaserLasgun.csproj" -c Release >/dev/null

DLL="$HERE/bin/Release/RedLaserLasgun.dll"
[ -f "$DLL" ] || { echo "build produced no DLL at $DLL" >&2; exit 1; }

echo "[2/3] stage Vortex layout"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/BepInEx/plugins"
cp "$DLL" "$STAGE/BepInEx/plugins/RedLaserLasgun.dll"
cp "$HERE/modinfo.json" "$STAGE/modinfo.json"

echo "[3/3] zip -> dist/$NAME-v$VERSION.zip"
mkdir -p "$DIST"
OUT="$DIST/$NAME-v$VERSION.zip"
rm -f "$OUT"
( cd "$STAGE" && zip -rq "$OUT" BepInEx modinfo.json )
echo "packaged -> $OUT"
unzip -l "$OUT"
