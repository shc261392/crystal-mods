# Faction Soundtrack — Dawn of War: Definitive Edition

A mod that gives **each faction its own music playlist**. Built on the fact that
the DoW:DE engine loads standard `.wav` audio directly and selects music
playlists per race by filename convention.

Status: **prototype** — validating the mechanism in-game with test tones before
curating real music.

## How it works (verified against the game install)

- The engine loads music playlists from plain-text Lua files by hard-coded name:
  - `Data/SoundPlaylistFE_<Race>.lua` — **front-end (menu) music, per race** (native).
  - `Data/SoundPlaylistMusic.lua` — in-game music (one shared shuffle list in vanilla).
  - `Data/SoundPlaylistVictory_<Race>.lua` — victory music, per race.
- A playlist file looks like:
  ```lua
  playlist = {
    tracks = { "track_name", ... },   -- resolved to Sound/Music/<name>.<ext>
    silence_min = 4.0, silence_max = 12.0,
    order = false,                    -- false = shuffle, true = sequential
  }
  ```
- The sound engine (`seInterface.dll`) accepts `.wav`, `.wave`, `.aif`, `.aiff`,
  and `.fda`. So custom tracks can ship as **`.wav`** — no proprietary FDA
  conversion required.
- This mod is a standalone, selectable module (`FactionSoundtrack.module`) that
  requires the base game modules and overrides only the per-race menu playlists.

Race tokens: `Space`, `Chaos`, `Ork`, `Eldar`, `Guard`, `Necron`, `Tau`,
`Sisters`, `Dark_Eldar`.

## Curate music

Drop source audio (mp3/wav/flac/ogg/m4a) into a per-faction folder:

```
music/
  ork/     song1.mp3  song2.mp3 ...   (5–10 tracks recommended)
  space/   ...
  eldar/   ...
```

Any faction folder left empty gets a distinct **test tone** instead, so the mod
always builds and can be validated.

## Build

```bash
./build.sh        # Linux / WSL / macOS
./build.ps1       # Windows PowerShell
```

Output: `dist/faction-soundtrack-v<version>.zip` — install with Vortex (or unzip
into the game root). Then select **Faction Soundtrack** in the game's mod
selector.

## Roadmap

1. **[current] Front-end (menu) per-faction playlists** — native, no scripting.
2. **In-game per-faction music** — a win-condition script using the engine's
   `Sound_Playlist*` Lua API to swap the playlist based on the local player's
   race.
