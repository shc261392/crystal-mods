#!/usr/bin/env bash
# uninstall.sh — Restore every modded file from $GAME_DIR/.zh-tw-mod-backup/.
#
# Reads MANIFEST (written by deploy.sh on first install), restores each tracked
# file in-place, and verifies SHA-256 against the manifest entry. The backup is
# preserved so the mod can be re-installed without another Steam verify.

set -euo pipefail

GAME_DIR="/mnt/d/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector"
MOD_BACKUP_DIR="$GAME_DIR/.zh-tw-mod-backup"
MANIFEST="$MOD_BACKUP_DIR/MANIFEST"

if [[ ! -f "$MANIFEST" ]]; then
    echo "ERROR: No backup MANIFEST found at: $MANIFEST" >&2
    echo "       The mod was never installed via deploy.sh on this game install," >&2
    echo "       or the backup was deleted. Steam-verify the game to restore." >&2
    exit 1
fi

echo "=== Restoring files from $MOD_BACKUP_DIR ==="
restored=0
failed=0
while read -r sha rel; do
    [[ -z "${sha:-}" ]] && continue
    src="$MOD_BACKUP_DIR/$rel"
    dst="$GAME_DIR/$rel"
    if [[ ! -f "$src" ]]; then
        echo "  MISSING in backup: $rel" >&2
        failed=$((failed+1))
        continue
    fi
    mkdir -p "$(dirname "$dst")"
    cp -p "$src" "$dst"
    actual="$(sha256sum "$dst" | awk '{print $1}')"
    if [[ "$actual" != "$sha" ]]; then
        echo "  CHECKSUM MISMATCH after restore: $rel" >&2
        echo "    expected $sha" >&2
        echo "    got      $actual" >&2
        failed=$((failed+1))
        continue
    fi
    echo "  restored: $rel"
    restored=$((restored+1))
done < "$MANIFEST"

sync

echo ""
echo "Restored $restored file(s)."
if [[ $failed -ne 0 ]]; then
    echo "ERROR: $failed file(s) could not be restored — Steam-verify recommended." >&2
    exit 1
fi
echo "Backup preserved at: $MOD_BACKUP_DIR"
echo "Re-run  bash tools/scripts/deploy.sh  to re-install."
