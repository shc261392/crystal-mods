#!/usr/bin/env bash
# Package the BepInEx Framework mod as a Vortex-installable zip.
#
# Reuses the already-built framework binaries if present; otherwise downloads the
# official BepInEx Bleeding-Edge build and verifies its SHA-256 before packaging.
# The binaries themselves are NOT committed — only this script is.
#
# Output: ../dist/bepinex-framework-v1.0.0.zip  (game-root layout: winhttp.dll,
# doorstop_config.ini, .doorstop_version, BepInEx/, dotnet/ + modinfo.json)
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
DIST="$HERE/../dist"
VERSION="$(grep -oP '"version"\s*:\s*"\K[^"]+' "$HERE/modinfo.json")"
OUT="$DIST/bepinex-framework-v$VERSION.zip"

# Reuse the existing repackaged framework zip if it is here (fast path)…
PREBUILT="$DIST/wh40k-battlesector-bepinex6-il2cpp-be785.zip"
# …otherwise download the official artifact and verify it.
OFFICIAL_URL="https://builds.bepinex.dev/projects/bepinex_be/785/BepInEx-Unity.IL2CPP-win-x64-6.0.0-be.785+6abdba4.zip"
OFFICIAL_SHA256="2a7cbf74d26abe4765c3e662db1721b923bac39849ebfef2ca5dc7de7e2d9b7f"

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

SRC_ZIP=""
if [ -f "$PREBUILT" ]; then
  echo "[1/3] reusing existing framework binaries: $(basename "$PREBUILT")"
  SRC_ZIP="$PREBUILT"
else
  echo "[1/3] downloading official BepInEx build (be.785)…"
  DL="$STAGE/bepinex-official.zip"
  curl -fsSL "$OFFICIAL_URL" -o "$DL"
  echo "      verifying SHA-256…"
  echo "$OFFICIAL_SHA256  $DL" | sha256sum -c - || { echo "SHA-256 mismatch — aborting" >&2; exit 1; }
  SRC_ZIP="$DL"
fi

echo "[2/3] stage framework + modinfo"
mkdir -p "$STAGE/pkg"
unzip -qo "$SRC_ZIP" -d "$STAGE/pkg"
cp "$HERE/modinfo.json" "$STAGE/pkg/modinfo.json"

echo "[3/3] zip -> dist/$(basename "$OUT")"
mkdir -p "$DIST"
rm -f "$OUT"
( cd "$STAGE/pkg" && zip -rqX "$OUT" . )
echo "packaged -> $OUT ($(du -h "$OUT" | cut -f1))"
unzip -l "$OUT" | awk '{print $4}' | grep -E '^[^/]+/?$|winhttp|doorstop|modinfo' | head
