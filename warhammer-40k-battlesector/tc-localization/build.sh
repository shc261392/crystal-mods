#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# build.sh — Rebuild the Traditional Chinese localization for Battlesector 1.8.0
# and package the Vortex ZIP. Idempotent: every step starts from a pristine
# game file, so the same game build always produces the same assets.
#
# Pipeline:
#   1. TCFix plugin                     dotnet build
#   2. build_text_180.py                SC text -> TC text in resources.assets
#   3. bake_font_180.py (sharedassets2) NotoSansCJKjp-Regular SDF, atlas 1
#   4. bake_font_180.py (startup)       Generated fallback font
#      + add_font_fallback.py            other boot fonts fall back to it
#   5. bake_font_180.py (mapbuilder)    map editor CJK font
#   6. patch_launcher.py                launcher strings SC -> TC
#   7. package                          dist/<mod>.zip
#
# Env:
#   MOD_GAME_DIR     game root (default: Steam library path)
#   MOD_PY           python interpreter with UnityPy/freetype/scipy/opencc
#   MOD_TC_OTF       Noto Sans CJK TC OTF used for missing glyphs
#   MOD_ZIP_OUT      output zip path
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$PWD"
GAME_DIR="${MOD_GAME_DIR:-/mnt/d/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector}"
DATA="Warhammer 40K Battlesector_Data"
GAME_DATA="$GAME_DIR/$DATA"

PY="${MOD_PY:-$ROOT/../../.agent_workspace/battlesector-data/venv/bin/python}"
[ -x "$PY" ] || PY=python3
OTF="${MOD_TC_OTF:-$ROOT/../../.agent_workspace/fonts/NotoSansCJKtc-Regular.otf}"
export MOD_TC_OTF="$OTF"

DIST="$ROOT/translation/zh-TW/dist"
WS="$ROOT/.agent_workspace"
ZIP_OUT="${MOD_ZIP_OUT:-$ROOT/../dist/wh40k-battlesector-tc-localization-v0.3.0.zip}"
TCFIX="$ROOT/bepinex/TCFix/bin/Release/TCFix.dll"

[ -f "$GAME_DATA/resources.assets" ] || { echo "game data not found: $GAME_DATA"; exit 1; }
[ -f "$OTF" ] || { echo "CJK font not found: $OTF (set MOD_TC_OTF)"; exit 1; }
command -v dotnet >/dev/null || { echo "dotnet not found"; exit 1; }

mkdir -p "$DIST"

echo "==> 1. TCFix plugin"
dotnet build "$ROOT/bepinex/TCFix/TCFix.csproj" -c Release >/dev/null

echo "==> 2. Text: SC -> TC in resources.assets"
MOD_VANILLA_RES="$GAME_DATA/resources.assets" MOD_DIST_DIR="$DIST" \
  "$PY" tools/scripts/build_text_180.py

echo "==> 3. Fonts: sharedassets2 (main UI + description CJK font)"
cp "$GAME_DATA/sharedassets2.assets" "$DIST/sharedassets2.assets"
MOD_FONT_OTF="$OTF" "$PY" tools/scripts/bake_font_180.py "$DIST/sharedassets2.assets" 370 1

echo "==> 4. Fonts: startup bundle (boot/loading fallback)"
cp "$GAME_DATA/StreamingAssets/startup_assets_all.bundle" "$DIST/startup_assets_all.bundle"
MOD_FONT_OTF="$OTF" "$PY" tools/scripts/bake_font_180.py \
  "$DIST/startup_assets_all.bundle" -6634277187469610597 0
"$PY" tools/scripts/add_font_fallback.py "$DIST/startup_assets_all.bundle" \
  -6634277187469610597 2045931099826710272 6858071789788628647 7178690147649604500

echo "==> 5. Fonts: mapbuilder bundle (map editor CJK font)"
cp "$GAME_DATA/StreamingAssets/mapbuilder-tools_assets_all.bundle" "$DIST/mapbuilder-tools_assets_all.bundle"
MOD_FONT_OTF="$OTF" "$PY" tools/scripts/bake_font_180.py \
  "$DIST/mapbuilder-tools_assets_all.bundle" -3782840183126329981 1

echo "==> 6. Launcher strings SC -> TC"
MOD_GAME_DIR="$GAME_DIR" MOD_DIST_DIR="$DIST" "$PY" tools/scripts/patch_launcher.py

echo "==> 7. Package ZIP"
S="$WS/stage"; rm -rf "$S"
mkdir -p "$S/BepInEx/plugins" "$S/$DATA/StreamingAssets" "$S/Launcher/Localization"
cp "$TCFIX" "$S/BepInEx/plugins/TCFix.dll"
cp "$DIST/resources.assets" "$DIST/sharedassets2.assets" "$S/$DATA/"
cp "$DIST/startup_assets_all.bundle" "$DIST/mapbuilder-tools_assets_all.bundle" "$S/$DATA/StreamingAssets/"
cp "$DIST/stringsChinese.resx" "$S/Launcher/Localization/"
# modinfo.json + README.md are repo metadata, NOT game files. Never stage them
# into the deployable archive — the Vortex extension deploys every archive path.
mkdir -p "$(dirname "$ZIP_OUT")"
rm -f "$ZIP_OUT"
find "$S" -exec touch -h -d '1980-01-01 00:00:00' {} +
( cd "$S" && find . -type f | sed 's|^\./||' | LC_ALL=C sort | zip -qX -D "$ZIP_OUT" -@ )
rm -rf "$S"
echo "    wrote $ZIP_OUT"
echo "==> Done. sha256:"; sha256sum "$ZIP_OUT"
unzip -l "$ZIP_OUT"
