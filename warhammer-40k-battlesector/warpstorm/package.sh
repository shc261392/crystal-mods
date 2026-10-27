#!/usr/bin/env bash
# Warpstorm — build the single deliverable:
#   dist/warpstorm-v<ver>.zip
#     BepInEx/plugins/Warpstorm/Warpstorm.dll              (BepInEx plugin)
#     BepInEx/plugins/Warpstorm/Warpstorm.Configurator.exe (self-contained tool)
#
# Both live under the mod's own folder, so installing via Vortex writes nothing
# extra to the game root. Env: BS_GAME_DIR overrides the game folder used to find
# the BepInEx/interop reference assemblies.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GAME_DIR="${BS_GAME_DIR:-/mnt/d/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector}"
VER="$(grep -oP '"version"\s*:\s*"\K[^"]+' "$HERE/modinfo.json")"
DIST="$HERE/dist"
STAGE="$HERE/.copilot_workspace/stage"
PLUGIN_DIR="$STAGE/BepInEx/plugins/Warpstorm"

rm -rf "$STAGE"
mkdir -p "$PLUGIN_DIR" "$DIST"

echo "[1/3] plugin -> Warpstorm.dll"
dotnet build "$HERE/plugin/Warpstorm.csproj" -c Release -p:GameDir="$GAME_DIR" >/dev/null
cp "$HERE/plugin/bin/Release/Warpstorm.dll" "$PLUGIN_DIR/"

# Bundle the catalog images once (needs uv + pillow + network). If they are
# already present, or the tools are unavailable, packaging still works — the
# UI simply shows no thumbnails.
if [ ! -d "$HERE/configurator/assets/units" ] && command -v uv >/dev/null 2>&1; then
  echo "[1.5/2] bundling unit/weapon images"
  uv run --no-project --with pillow python "$HERE/configurator/scripts/bundle-images.py" \
    || echo "      warning: image bundling failed; continuing without images"
fi

echo "[2/3] configurator -> Warpstorm.Configurator.exe (single-file, self-contained)"
PUB="$STAGE/_publish"
# Single-file / compression / icon / version settings live in the csproj only.
dotnet publish "$HERE/configurator/Warpstorm.Configurator.csproj" -c Release -r win-x64 \
  --self-contained true -o "$PUB" >/dev/null
cp "$PUB/Warpstorm.Configurator.exe" "$PLUGIN_DIR/"
rm -rf "$PUB"

echo "[3/3] scheme packs -> curated portraits (tools/SchemeBuilder)"
dotnet build "$HERE/tools/SchemeBuilder/SchemeBuilder.csproj" -c Release >/dev/null
for scheme in "$HERE"/schemes/*/; do
  [ -f "$scheme/scheme.json" ] || continue   # skip caches/scratch folders
  id="$(basename "$scheme")"
  dotnet "$HERE/tools/SchemeBuilder/bin/Release/net10.0/SchemeBuilder.dll" build "$scheme" "$PLUGIN_DIR/schemes/$id"
done

# Deterministic zip (AGENTS.md rule 15): fixed timestamps, sorted entries, no
# extra attributes, so the same inputs always give a byte-identical archive.
ZIP="$DIST/warpstorm-v$VER.zip"
rm -f "$ZIP"
find "$STAGE/BepInEx" -exec touch -h -d '1980-01-01 00:00:00' {} +
( cd "$STAGE" && find BepInEx | LC_ALL=C sort | zip -qX -D "$ZIP" -@ )

# Each scheme pack also as its own shareable zip (import it in the configurator).
for packdir in "$PLUGIN_DIR"/schemes/*/; do
  id="$(basename "$packdir")"
  pver="$(grep -oP '"version"\s*:\s*"\K[^"]+' "$packdir/scheme.json")"
  PZIP="$DIST/scheme-$id-v$pver.zip"
  rm -f "$PZIP"
  ( cd "$packdir" && find . -type f | sed 's|^\./||' | LC_ALL=C sort | zip -qX -D "$PZIP" -@ )
  echo "pack -> $PZIP"
done
echo "done -> $ZIP"
unzip -l "$ZIP"
sha256sum "$ZIP" "$PLUGIN_DIR"/*.dll "$PLUGIN_DIR"/*.exe "$DIST"/scheme-*.zip
