#!/usr/bin/env bash
# Fetch + resize a candidate gameart.png for the Vortex extension.
#
# Vortex spec: 640x360 PNG, <= 1 MB, no text overlay, dark-bg-safe.
# Source: Steam header image for Warhammer 40,000: Battlesector (AppID 1295500).
# This is intended as a "quick start" — you should still hand-pick / curate
# before Nexus submission.
#
# Requires: curl, imagemagick (`convert`) OR python+Pillow as fallback.

set -euo pipefail

here="$(cd "$(dirname "$0")/.." && pwd)"
out="${here}/gameart.png"
tmp="${here}/.gameart-src.jpg"

# Steam header is 460x215; library hero is 1920x620. We use library_600x900
# cropped to 16:9. Alternative source: SteamGridDB (better, requires API key).
url="https://cdn.akamai.steamstatic.com/steam/apps/1295500/header.jpg"

echo "Downloading: $url"
curl -fsSL "$url" -o "$tmp"

if command -v convert >/dev/null 2>&1; then
  echo "Resizing with ImageMagick → 640x360"
  convert "$tmp" -resize 640x360^ -gravity center -extent 640x360 "$out"
elif command -v python3 >/dev/null 2>&1; then
  echo "Resizing with Python/Pillow → 640x360"
  python3 - "$tmp" "$out" <<'PY'
import sys
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGB")
im = im.resize((640, 360), Image.LANCZOS)
im.save(dst, "PNG", optimize=True)
PY
else
  echo "ERROR: need either imagemagick or python3+Pillow" >&2
  rm -f "$tmp"
  exit 1
fi

rm -f "$tmp"

# Size guard: Nexus rejects > 1 MB.
size=$(stat -c%s "$out" 2>/dev/null || stat -f%z "$out")
if [ "$size" -gt 1048576 ]; then
  echo "WARNING: gameart.png is ${size} bytes (>1 MB). Re-export with stronger compression." >&2
fi

echo "Wrote $out (${size} bytes)"
echo ""
echo "Verify with: file $out"
echo "Reminder: hand-review before Nexus submission (must be dark-bg-safe, no text)."
