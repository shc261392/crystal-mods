#!/usr/bin/env bash
# Package the Black Book BepInEx 5 (Mono, x64) framework mod as a
# Vortex-installable zip.
#
# Reuses an already-downloaded copy of the pinned upstream archive if present;
# otherwise downloads the official BepInEx 5.4.23.5 win-x64 release and verifies
# its SHA-256 before packaging. The framework binaries are NOT committed — only
# this script is.
#
# Black Book is a Unity 2018.4 Mono title, so it needs BepInEx 5 (x64), NOT
# BepInEx 6 IL2CPP. Do not change the pin without also updating modinfo.json and
# tc-localization/build_plugin.sh, which verify the same archive.
#
# Output: ../dist/bepinex-framework-v1.0.0.zip
# Layout (game root): winhttp.dll, doorstop_config.ini, .doorstop_version,
#                    changelog.txt, BepInEx/core/*, modinfo.json
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
DIST="$HERE/../dist"
VERSION="$(grep -oP '"version"\s*:\s*"\K[^"]+' "$HERE/modinfo.json" | head -1)"
OUT="$DIST/bepinex-framework-v$VERSION.zip"

# Pinned upstream artifact (BepInEx 5.4.23.5, win-x64).
BEPINEX_VERSION="5.4.23.5"
OFFICIAL_URL="https://github.com/BepInEx/BepInEx/releases/download/v${BEPINEX_VERSION}/BepInEx_win_x64_${BEPINEX_VERSION}.zip"
OFFICIAL_SHA256="82f9878551030f54657792c0740d9d51a09500eeae1fba21106b0c441e6732c4"

# Fast path: reuse a previously downloaded upstream archive (e.g. one the user
# dropped in dist/, or a prior run's download). Its SHA-256 is verified below
# either way, so a tampered cache cannot be packaged.
CACHED="$DIST/BepInEx_win_x64_${BEPINEX_VERSION}.zip"

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

SRC_ZIP=""
if [ -f "$CACHED" ]; then
  echo "[1/3] reusing cached upstream archive: $(basename "$CACHED")"
  SRC_ZIP="$CACHED"
else
  echo "[1/3] downloading official BepInEx ${BEPINEX_VERSION} (win-x64)…"
  DL="$STAGE/bepinex-official.zip"
  curl -fsSL "$OFFICIAL_URL" -o "$DL"
  SRC_ZIP="$DL"
fi

echo "      verifying SHA-256…"
echo "$OFFICIAL_SHA256  $SRC_ZIP" | sha256sum -c - || { echo "SHA-256 mismatch — aborting" >&2; exit 1; }

# Cache the verified archive so later runs take the reuse path above.
if [ "$SRC_ZIP" != "$CACHED" ]; then
  mkdir -p "$DIST"
  cp -f "$SRC_ZIP" "$CACHED"
fi

echo "[2/3] stage framework + modinfo"
mkdir -p "$STAGE/pkg"
unzip -qo "$SRC_ZIP" -d "$STAGE/pkg"
cp "$HERE/modinfo.json" "$STAGE/pkg/modinfo.json"

# Deterministic archive (AGENTS.md rule 15): normalise every staged mtime to the
# earliest timestamp the zip format can represent, then add the files in a fixed
# (byte-sorted) order with no directory entries and no extra attributes.
find "$STAGE/pkg" -exec touch -h -t 198001010000 {} +

echo "[3/3] zip -> dist/$(basename "$OUT")"
mkdir -p "$DIST"
rm -f "$OUT"
( cd "$STAGE/pkg" && find . -type f -printf '%P\n' | LC_ALL=C sort | zip -qX "$OUT" -@ )
echo "packaged -> $OUT ($(du -h "$OUT" | cut -f1))"
unzip -l "$OUT" | awk 'NR>3 {print $4}' | grep -E 'winhttp|doorstop|modinfo' | head
