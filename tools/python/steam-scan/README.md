# `steam-scan` — Steam library + installed-game discovery

Cross-platform scanner that locates every Steam library on the system and
enumerates installed games (via `appmanifest_*.acf`).

Detects:

- **Windows**: registry (`HKLM\…\Valve\Steam\InstallPath`) + common drive
  letters (`C:`–`G:`) + `SteamLibrary\` folders.
- **WSL2**: same Windows paths via `/mnt/<letter>/`.
- **Linux native**: `~/.steam/steam`, `~/.local/share/Steam`, Flatpak
  (`~/.var/app/com.valvesoftware.Steam/.local/share/Steam`).
- **Library aggregation**: parses each Steam root's
  `steamapps/libraryfolders.vdf` to discover additional library drives.

## Usage

From the repo root:

```bash
uv run steam-scan                       # human-readable table
uv run steam-scan --json                # machine-readable JSON
uv run steam-scan --name "digimon"      # filter by substring
uv run steam-scan --appid 1390590       # filter by Steam App ID
```

## Output (JSON)

```json
{
  "libraries": [
    {"path": "/mnt/c/Program Files (x86)/Steam", "platform": "wsl"}
  ],
  "games": [
    {
      "appid": "1390590",
      "name": "Digimon Survive",
      "installdir": "Digimon Survive",
      "install_path": "/mnt/c/Program Files (x86)/Steam/steamapps/common/Digimon Survive",
      "library_path": "/mnt/c/Program Files (x86)/Steam",
      "size_on_disk": 3500000000
    }
  ]
}
```
