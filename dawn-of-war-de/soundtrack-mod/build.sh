#!/usr/bin/env bash
# Build the Faction Soundtrack mod into a Vortex-installable ZIP in dist/.
#
# For each faction, place source audio (mp3/wav/flac/ogg) in:  music/<race>/
# If a faction has no source audio, a distinct TEST TONE is generated so the
# mechanism can be validated in-game before real music is curated.
#
# Output: dist/faction-soundtrack-v<VERSION>.zip
#
# Requires: ffmpeg, zip.  Cross-platform companion: build.ps1

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="0.2"
MOD_NAME="FactionSoundtrack"

# Scratch staging lives OUTSIDE the repo deliverable path (gitignored).
STAGE="$HERE/.copilot_workspace/stage"
DIST="$HERE/dist"
SRC="$HERE/src"
MUSIC_SRC="$HERE/music"

# Engine-supported target format (verified from seInterface.dll): 44100 Hz, 16-bit, stereo WAV.
AR=44100

# Faction token (as used in SoundPlaylistFE_<Token>.lua) : test-tone frequency (Hz)
FACTIONS=(
  "Space:523"      # Space Marines
  "Chaos:415"      # Chaos Space Marines
  "Ork:196"        # Orks
  "Eldar:659"      # Eldar
  "Guard:294"      # Imperial Guard
  "Necron:233"     # Necrons
  "Tau:784"        # Tau Empire
  "Sisters:880"    # Sisters of Battle
  "Dark_Eldar:466" # Dark Eldar
)

command -v ffmpeg >/dev/null || { echo "ERROR: ffmpeg not found"; exit 1; }
command -v zip    >/dev/null || { echo "ERROR: zip not found"; exit 1; }

echo "==> Cleaning staging"
rm -rf "$STAGE"
# Distribution layout (matches the official Mod Assistant structure):
#   <ModName>/<ModName>.module
#   <ModName>/pipeline.ini
#   <ModName>/Mod/Data/...        (ModFolder=Mod, DataFolder.1=Data)
MODROOT="$STAGE/$MOD_NAME"
DATA="$MODROOT/Mod/Data"
MUSIC_OUT="$DATA/Sound/Music"
mkdir -p "$MUSIC_OUT"
mkdir -p "$DIST"

# Copy the module definition and pipeline config into the mod's own folder.
cp "$SRC/$MOD_NAME.module" "$MODROOT/$MOD_NAME.module"
cp "$SRC/pipeline.ini" "$MODROOT/pipeline.ini"

for entry in "${FACTIONS[@]}"; do
  token="${entry%%:*}"
  freq="${entry##*:}"
  lc="$(echo "$token" | tr '[:upper:]' '[:lower:]')"

  # Collect this faction's tracks (either real source audio or a generated tone).
  tracks=()
  srcdir="$MUSIC_SRC/$lc"
  if [ -d "$srcdir" ] && compgen -G "$srcdir/*" >/dev/null; then
    i=0
    for f in "$srcdir"/*; do
      case "${f,,}" in
        *.mp3|*.wav|*.flac|*.ogg|*.m4a|*.aac) ;;
        *) continue ;;
      esac
      i=$((i+1))
      name="mod_${lc}_$(printf '%02d' "$i")"
      echo "==> [$token] converting $(basename "$f") -> $name.wav"
      ffmpeg -y -loglevel error -i "$f" -ar "$AR" -ac 2 -sample_fmt s16 "$MUSIC_OUT/$name.wav"
      tracks+=("$name")
    done
  fi

  if [ "${#tracks[@]}" -eq 0 ]; then
    name="mod_${lc}_testtone"
    echo "==> [$token] no source audio; generating test tone ${freq}Hz -> $name.wav"
    ffmpeg -y -loglevel error \
      -f lavfi -i "sine=frequency=${freq}:duration=12" \
      -af "tremolo=f=4:d=0.6,volume=0.5" \
      -ar "$AR" -ac 2 -sample_fmt s16 "$MUSIC_OUT/$name.wav"
    tracks+=("$name")
  fi

  # Emit the per-faction FRONT-END (menu) playlist that overrides the base game.
  pl="$DATA/SoundPlaylistFE_${token}.lua"
  {
    echo "-- Faction Soundtrack: front-end (menu) playlist for ${token}"
    echo "playlist ="
    echo "{"
    echo "	tracks ="
    echo "	{"
    for t in "${tracks[@]}"; do
      echo "		\"${t}\","
    done
    echo "	},"
    echo ""
    echo "	silence_min = 4.0,"
    echo "	silence_max = 12.0,"
    echo ""
    echo "	order = false,"
    echo "}"
  } > "$pl"
done

echo "==> Packaging ZIP"
OUT="$DIST/faction-soundtrack-v${VERSION}.zip"
rm -f "$OUT"
( cd "$STAGE" && zip -r -q "$OUT" "$MOD_NAME" )

echo ""
echo "Built: $OUT"
echo "Contents:"
( cd "$STAGE" && find . -type f | sed 's#^\./#  #' | sort )
