#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# build.sh — Rebuild the TC localization from source (text + glossary) and
# package the Vortex ZIP. Idempotent: text is rebuilt from vanilla each run, and
# any new glyphs introduced by glossary/punctuation are baked automatically.
#
# Steps:
#   1. build_text.py         vanilla -> s2tw -> glossary -> punctuation -> text bins
#   2. FontTool replace      inject the 7 TextAssets into resources.assets
#   3. bake_font_generic     add any missing glyphs to fonts 785 (sa0) + 3644 (sa1)
#   4. package               assemble dist/<mod>.zip
#
# The fonts' Traditional glyph re-render, bold-weight and static conversions are
# already baked into the dist sharedassets; this script preserves them and only
# adds newly-needed glyphs. Full font rebuilds are separate scripts.
#
# Env:
#   MOD_VANILLA_RES  vanilla resources.assets (see build_text.py)
#   MOD_PY           python interpreter (default: venv in .copilot_workspace)
#   MOD_FT           fonttool.dll path
#   MOD_TC_OTF       Traditional OTF for new glyphs (NotoSansCJKtc)
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$PWD"

PY="${MOD_PY:-$ROOT/.copilot_workspace/venv/bin/python3}"
FT="${MOD_FT:-$ROOT/.copilot_workspace/csharp/FontTool/bin/Release/net10.0/fonttool.dll}"
OTF="${MOD_TC_OTF:-$ROOT/.copilot_workspace/fonts/NotoSansCJKtc-Regular.otf}"
DIST="$ROOT/translation/zh-TW/dist"
WS="$ROOT/.copilot_workspace"
TEXT_OUT="$ROOT/.build/text"
DATA="Warhammer 40K Battlesector_Data"
ZIP_OUT="${MOD_ZIP_OUT:-$ROOT/../dist/wh40k-battlesector-tc-localization-v0.2.2.zip}"
TCFIX="$ROOT/bepinex/TCFix/bin/Release/TCFix.dll"

command -v dotnet >/dev/null || { echo "dotnet not found"; exit 1; }
[ -f "$FT" ] || { echo "FontTool not built: $FT"; exit 1; }

echo "==> 1. Build text (s2tw + glossary + punctuation)"
"$PY" tools/scripts/build_text.py

echo "==> 2. Inject text into resources.assets"
cp "$DIST/resources.assets" "$WS/res_in.assets"
while IFS=$'\t' read -r pid bin; do
  [ -z "$pid" ] && continue
  dotnet "$FT" replace "$WS/res_in.assets" "$WS/res_out.assets" "$pid" "$bin" >/dev/null
  mv "$WS/res_out.assets" "$WS/res_in.assets"
done < "$TEXT_OUT/manifest.txt"
mv "$WS/res_in.assets" "$DIST/resources.assets"
echo "    resources.assets updated"

echo "==> 3. Bake any new glyphs into fonts 785 (sa0) + 3644 (sa1)"
MOD_FONT_OTF="$OTF" "$PY" tools/scripts/bake_font_generic.py "$DIST/sharedassets0.assets" 785 build_sa0
if [ -f "$WS/build_sa0/tex_295.bin" ]; then
  dotnet "$FT" replace "$DIST/sharedassets0.assets" "$WS/sa0.assets" 785 "$WS/build_sa0/font_785.bin" >/dev/null
  dotnet "$FT" replace "$WS/sa0.assets" "$DIST/sharedassets0.assets" 295 "$WS/build_sa0/tex_295.bin" >/dev/null
fi
MOD_FONT_OTF="$OTF" "$PY" tools/scripts/bake_font_generic.py "$DIST/sharedassets1.assets" 3644 build_sa1
if [ -f "$WS/build_sa1/font_3644.bin" ]; then
  dotnet "$FT" replace "$DIST/sharedassets1.assets" "$WS/sa1.assets" 3644 "$WS/build_sa1/font_3644.bin" >/dev/null
  mv "$WS/sa1.assets" "$DIST/sharedassets1.assets"
  [ -f "$WS/build_sa1/sharedassets1.assets.resS" ] && cp "$WS/build_sa1/sharedassets1.assets.resS" "$DIST/sharedassets1.assets.resS"
fi
echo "    fonts updated"

echo "==> 4. Package ZIP"
S="$WS/stage"; rm -rf "$S"
mkdir -p "$S/BepInEx/plugins" "$S/$DATA/StreamingAssets" "$S/Launcher/Localization"
cp "$TCFIX" "$S/BepInEx/plugins/TCFix.dll"
cp "$DIST/resources.assets" "$DIST/sharedassets0.assets" "$DIST/sharedassets1.assets" "$DIST/sharedassets1.assets.resS" "$S/$DATA/"
cp "$DIST/startup_assets_all.bundle" "$DIST/mapbuilder-tools_assets_all.bundle" "$S/$DATA/StreamingAssets/"
cp "$DIST/stringsChinese.resx" "$S/Launcher/Localization/"
cp modinfo.json README.md "$S/"
mkdir -p "$(dirname "$ZIP_OUT")"
rm -f "$ZIP_OUT"
( cd "$S" && zip -r -X -q -1 "$ZIP_OUT" . )
rm -rf "$S"
echo "    wrote $ZIP_OUT"
echo "==> Done. sha256:"; sha256sum "$ZIP_OUT"
