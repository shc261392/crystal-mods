#!/usr/bin/env bash
# Fetch + resize a candidate gameart.jpg for the Black Book Vortex extension.
#
# Vortex spec: 640x360, <= 1 MB, no text overlay, dark-bg-safe.
# Source: Steam header image for Black Book (AppID 1138660). 460x215, so it is
# scaled to cover 16:9 and centre-cropped.
# This is intended as a "quick start" — you should still hand-pick / curate
# before Nexus submission.
#
# Requires: curl, plus one of ImageMagick (`convert`), ffmpeg, or python+Pillow.

set -euo pipefail

here="$(cd "$(dirname "$0")/.." && pwd)"
out="${here}/gameart.jpg"
tmp="${here}/.gameart-src.jpg"

# Steam header is 460x215. Alternative source: SteamGridDB (better, needs API key).
url="https://cdn.akamai.steamstatic.com/steam/apps/1138660/header.jpg"

echo "Downloading: $url"
curl -fsSL "$url" -o "$tmp"

if command -v convert >/dev/null 2>&1; then
  echo "Resizing with ImageMagick -> 640x360"
  convert "$tmp" -resize 640x360^ -gravity center -extent 640x360 -quality 90 "$out"
elif command -v ffmpeg >/dev/null 2>&1; then
  echo "Resizing with ffmpeg -> 640x360"
  ffmpeg -hide_banner -loglevel error -y -i "$tmp" \
    -vf "scale=640:360:force_original_aspect_ratio=increase,crop=640:360" \
    -q:v 3 "$out"
elif command -v python3 >/dev/null 2>&1 && python3 -c "import PIL" >/dev/null 2>&1; then
  echo "Resizing with Python/Pillow -> 640x360"
  python3 - "$tmp" "$out" <<'PY'
import sys
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGB")
# cover + centre crop to 16:9
scale = max(640 / im.width, 360 / im.height)
im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
left = (im.width - 640) // 2
top = (im.height - 360) // 2
im = im.crop((left, top, left + 640, top + 360))
im.save(dst, "JPEG", quality=90, optimize=True)
PY
else
  echo "ERROR: need ImageMagick, ffmpeg, or python3+Pillow" >&2
  rm -f "$tmp"
  exit 1
fi

rm -f "$tmp"

# Size guard: Nexus rejects > 1 MB.
size=$(stat -c%s "$out" 2>/dev/null || stat -f%z "$out")
if [ "$size" -gt 1048576 ]; then
  echo "WARNING: gameart.jpg is ${size} bytes (>1 MB). Re-export with stronger compression." >&2
fi

echo "Wrote $out (${size} bytes)"
echo ""
echo "Verify with: file $out"
echo "Reminder: hand-review before Nexus submission (must be 640x360, dark-bg-safe, no text)."
