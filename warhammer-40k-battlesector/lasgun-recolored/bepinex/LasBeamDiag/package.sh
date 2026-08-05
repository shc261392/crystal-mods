#!/usr/bin/env bash
# Build LasBeamDiag and package it as a Vortex-installable zip.
#
# The zip lays the plugin at BepInEx/plugins/LasBeamDiag.dll — the Battlesector
# Vortex extension recognises BepInEx/ as a game-root dir (Layout A) and deploys
# it to <game>/BepInEx/plugins/. BepInEx core itself is NOT shipped; it is
# assumed already installed (it ships with the TC Localization mod).
#
# Usage: ./package.sh   (override GameDir for the interop refs if needed)
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
DIST="$HERE/../../dist"
VERSION="$(grep -oP '"version"\s*:\s*"\K[^"]+' "$HERE/modinfo.json")"
NAME="lasgun-laser-diag"

echo "[1/3] dotnet build -c Release"
dotnet build "$HERE/LasBeamDiag.csproj" -c Release >/dev/null

DLL="$HERE/bin/Release/LasBeamDiag.dll"
[ -f "$DLL" ] || { echo "build produced no DLL at $DLL" >&2; exit 1; }

echo "[2/3] stage Vortex layout"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/BepInEx/plugins"
cp "$DLL" "$STAGE/BepInEx/plugins/LasBeamDiag.dll"
cp "$HERE/modinfo.json" "$STAGE/modinfo.json"

echo "[3/3] zip -> dist/$NAME-v$VERSION.zip"
mkdir -p "$DIST"
OUT="$DIST/$NAME-v$VERSION.zip"
rm -f "$OUT"
( cd "$STAGE" && zip -rq "$OUT" BepInEx modinfo.json )
echo "packaged -> $OUT"
unzip -l "$OUT"
