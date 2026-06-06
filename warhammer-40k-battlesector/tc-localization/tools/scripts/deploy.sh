#!/usr/bin/env bash
# deploy.sh — Build and deploy the zh-TW localization patch.
#
# On first run: creates a backup of every file we modify inside
#   $GAME_DIR/.zh-tw-mod-backup/  (mirroring the original directory layout),
#   plus a MANIFEST listing every tracked file with its SHA-256.
# On subsequent runs: reuses the backup as the pristine source for re-patching.
#
# The project tree never holds installation backups — only translator-editable
# source/ and patched/ files plus build output in dist/.
#
# Run from repo root:  bash tools/scripts/deploy.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
GAME_DIR="/mnt/d/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector"
GAME_DATA_REL="Warhammer 40K Battlesector_Data"
SA_REL="$GAME_DATA_REL/StreamingAssets"
LAUNCHER_REL="Launcher/Localization"

BUNDLE_NAME="unknownassets_assets_all_12cf1b4aeb7c9355f8487758e37a43d2.bundle"
MAPBUILDER_NAME="mapbuildertools_assets_all.bundle"

# All files the patch touches, paths RELATIVE to $GAME_DIR.
# Used by both deploy.sh (backup + restore-for-patching) and uninstall.sh.
TRACKED_FILES=(
    "$GAME_DATA_REL/sharedassets1.assets"
    "$GAME_DATA_REL/resources.assets"
    "$SA_REL/$BUNDLE_NAME"
    "$SA_REL/$MAPBUILDER_NAME"
    "$SA_REL/catalog.bin"
    "$SA_REL/catalog.hash"
    "$SA_REL/aa/catalog.bin"
    "$SA_REL/aa/catalog.hash"
    "$LAUNCHER_REL/stringsChinese.resx"
)

MOD_BACKUP_DIR="$GAME_DIR/.zh-tw-mod-backup"
MANIFEST="$MOD_BACKUP_DIR/MANIFEST"
DIST_DIR="$REPO_ROOT/translation/zh-TW/dist"

if [[ ! -d "$GAME_DIR" ]]; then
    echo "ERROR: Game directory not found: $GAME_DIR" >&2
    echo "       Edit GAME_DIR in tools/scripts/deploy.sh" >&2
    exit 1
fi

# Ensure UnityPy is available
if ! python3 -c "import UnityPy" 2>/dev/null; then
    echo "Installing UnityPy..." >&2
    pip install --quiet UnityPy
fi

# ── Phase 1: initialise / verify backup ──────────────────────────────────────
if [[ ! -f "$MANIFEST" ]]; then
    echo "=== First run: creating installation backup ==="
    echo "    $MOD_BACKUP_DIR"
    mkdir -p "$MOD_BACKUP_DIR"
    : > "$MANIFEST.tmp"
    for rel in "${TRACKED_FILES[@]}"; do
        src="$GAME_DIR/$rel"
        if [[ ! -f "$src" ]]; then
            echo "ERROR: Cannot back up missing game file: $rel" >&2
            echo "       Steam-verify the game and re-run." >&2
            rm -f "$MANIFEST.tmp"
            exit 1
        fi
        dst="$MOD_BACKUP_DIR/$rel"
        mkdir -p "$(dirname "$dst")"
        cp -p "$src" "$dst"
        sha="$(sha256sum "$src" | awk '{print $1}')"
        printf '%s  %s\n' "$sha" "$rel" >> "$MANIFEST.tmp"
        echo "  backed up: $rel"
    done
    mv "$MANIFEST.tmp" "$MANIFEST"
    echo "  wrote MANIFEST ($(wc -l < "$MANIFEST") entries)"
    echo ""
else
    echo "=== Reusing existing backup: $MOD_BACKUP_DIR ==="
    missing=0
    while read -r _sha rel; do
        if [[ ! -f "$MOD_BACKUP_DIR/$rel" ]]; then
            echo "ERROR: Backup file missing: $rel" >&2
            missing=1
        fi
    done < "$MANIFEST"
    if [[ $missing -ne 0 ]]; then
        echo "       Delete $MOD_BACKUP_DIR and re-run to rebuild backup." >&2
        exit 1
    fi
    echo ""
fi

# ── Phase 2: prime dist/ from pristine backup ────────────────────────────────
echo "=== Priming dist/ from backup ==="
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"
for rel in "${TRACKED_FILES[@]}"; do
    case "$rel" in
        */aa/catalog.bin|*/aa/catalog.hash)
            # aa/ copies are identical to the StreamingAssets/ copies; one dist
            # file gets deployed to both locations.
            continue
            ;;
    esac
    cp -p "$MOD_BACKUP_DIR/$rel" "$DIST_DIR/$(basename "$rel")"
done
echo "  primed $(ls "$DIST_DIR" | wc -l) files into dist/"
echo ""

# ── Phase 3: run the patch pipeline ──────────────────────────────────────────
export MOD_BACKUP_DIR
export MOD_DIST_DIR="$DIST_DIR"
export MOD_GAME_DIR="$GAME_DIR"

echo "=== Step 1: Extract language blocks from sharedassets1.assets ==="
python3 "$SCRIPT_DIR/extract_loc.py"

echo ""
echo "=== Step 2: Build TC patch (OpenCC s2twp) ==="
python3 "$SCRIPT_DIR/build_patch.py"

echo ""
echo "=== Step 3: Inject TC into zh-CN slot (assets + bundle + catalog) ==="
python3 "$SCRIPT_DIR/inject_loc.py"

echo ""
echo "=== Step 4: Patch resources.assets (SC→TC via UnityPy) ==="
python3 "$SCRIPT_DIR/patch_resources.py"

echo ""
echo "=== Step 5: Patch TMP fonts in unknownassets bundle ==="
python3 "$SCRIPT_DIR/patch_font.py"

echo ""
echo "=== Step 6: Patch mapbuildertools TMP font ==="
python3 "$SCRIPT_DIR/patch_mapbuilder_font.py"

echo ""
echo "=== Step 7: Patch launcher TC strings ==="
python3 "$SCRIPT_DIR/patch_launcher.py"

# ── Phase 4: deploy dist → game ──────────────────────────────────────────────
echo ""
echo "=== Step 8: Deploy patched files to game ==="
deploy_file() {
    local src="$1" dst="$2"
    if [[ ! -f "$src" ]]; then
        echo "ERROR: missing build output: $src" >&2
        exit 1
    fi
    mkdir -p "$(dirname "$dst")"
    cp -p "$src" "$dst"
    echo "  deployed: $dst"
}
deploy_file "$DIST_DIR/sharedassets1.assets"          "$GAME_DIR/$GAME_DATA_REL/sharedassets1.assets"
deploy_file "$DIST_DIR/resources.assets"              "$GAME_DIR/$GAME_DATA_REL/resources.assets"
deploy_file "$DIST_DIR/$BUNDLE_NAME"                  "$GAME_DIR/$SA_REL/$BUNDLE_NAME"
deploy_file "$DIST_DIR/$MAPBUILDER_NAME"              "$GAME_DIR/$SA_REL/$MAPBUILDER_NAME"
deploy_file "$DIST_DIR/catalog.bin"                   "$GAME_DIR/$SA_REL/catalog.bin"
deploy_file "$DIST_DIR/catalog.bin"                   "$GAME_DIR/$SA_REL/aa/catalog.bin"
deploy_file "$DIST_DIR/catalog.hash"                  "$GAME_DIR/$SA_REL/catalog.hash"
deploy_file "$DIST_DIR/catalog.hash"                  "$GAME_DIR/$SA_REL/aa/catalog.hash"
deploy_file "$DIST_DIR/stringsChinese.resx"           "$GAME_DIR/$LAUNCHER_REL/stringsChinese.resx"

# ── Clear Unity asset cache to force fresh bundle load ──────────────────────
# Without cache clearing, Unity loads cached bundle on next launch instead of
# the freshly deployed patched version, causing stale TC character rendering.
CACHE_DIR="/mnt/c/Users/shado/AppData/LocalLow/Black Lab Games/Warhammer 40,000 Battlesector/Unity"
if [[ -d "$CACHE_DIR" ]]; then
    echo ""
    echo "=== Clearing Unity asset cache for fresh bundle load ==="
    find "$CACHE_DIR" -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} + 2>/dev/null || true
    echo "  Cache cleared: $CACHE_DIR"
fi

sync
echo ""
echo "Done. Launch the game and select Chinese (简体中文/繁體中文) for Traditional Chinese."
echo "To revert:  bash tools/scripts/uninstall.sh"
