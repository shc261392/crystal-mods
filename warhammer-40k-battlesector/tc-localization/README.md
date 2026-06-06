# WH40K Battlesector — Traditional Chinese Localization Mod

Community Traditional Chinese (zh-TW) localization mod for **Warhammer 40,000: Battlesector** (Black Lab Games / Slitherine).

## How It Works

This mod directly patches the game's `sharedassets1.assets` binary file — no third-party mod loader required. Traditional Chinese strings replace the Simplified Chinese slot in the asset file.

**In-game:** Select **Chinese (Simplified)** to display Traditional Chinese text.

The font work is focused on achieving full TC glyph coverage directly in the TextMesh Pro font assets.

## Status

| Component | Status |
|---|---|
| Auto-generated baseline (SC→TC) | ✅ Completed |
| Terminology glossary | 🔧 In progress |
| Manual review pass | 🔧 In progress |
| Font pipeline (TC-only render target) | 🔧 In progress |

## Requirements

- Warhammer 40,000: Battlesector (Steam / GOG)
- **For script-based deployment:**
  - Python 3.8+ with [UnityPy](https://github.com/K0lb3/UnityPy)
  - Bash (Linux/WSL2) or PowerShell 5.0+ (Windows)

## Installation

### Option A: Vortex Mod Manager (Recommended)

1. **Install the Vortex extension** *(first time only)*
   - Download from Nexus Mods
   - Drag onto Vortex **Extensions** tab → **Enable**

2. **Add the mod**
   - Drag this mod zip onto Vortex

3. **Deploy** — click *Deploy Mods*
   - Vortex automatically backs up `sharedassets1.assets`
   - Files deploy to `Warhammer 40K Battlesector_Data/`

4. **Launch the game** — in-game, select **Chinese (Simplified)** locale

**To uninstall:** Click *Purge Mods* in Vortex. Original `sharedassets1.assets` is restored.

### Option B: Script Install (Windows / Linux / WSL2)

#### Windows (PowerShell)

```powershell
# From repo root:
.\deploy.ps1
```

#### Linux / WSL2

```bash
# From repo root:
bash deploy.sh
```

Both scripts:
- Auto-detect game installation via Steam
- Create timestamped backups in `./backup/`
- Deploy translation files
- Verify integrity

**To uninstall:**

```powershell
# Windows
.\uninstall.ps1

# Linux / WSL2
bash uninstall.sh
```

### Option C: Manual Install

1. **Locate game folder**
   - Steam: Right-click **Warhammer 40,000: Battlesector** → **Manage** → **Browse local files**
   - Common path: `C:\Program Files (x86)\Steam\steamapps\common\Warhammer 40K Battlesector\`

2. **Backup the original**
   ```
   Warhammer 40K Battlesector_Data/sharedassets1.assets
   → Warhammer 40K Battlesector_Data/sharedassets1.assets.backup
   ```

3. **Deploy the patched asset file**
   - Copy `dist/sharedassets1.assets` to `Warhammer 40K Battlesector_Data/`

4. **Launch the game** → select **Chinese (Simplified)** locale

**To uninstall:**
1. Delete `Warhammer 40K Battlesector_Data/sharedassets1.assets`
2. Rename `sharedassets1.assets.backup` → `sharedassets1.assets`

---

## Building from Source

If you want to rebuild the patched asset file:

### Requirements

```bash
pip install UnityPy
```

### Full Pipeline

```bash
# Extract → build → inject → deploy to game
bash tools/scripts/deploy.sh
```

### Manual Build Steps

```bash
# 1. Extract game assets
python3 tools/scripts/extract_assets.py

# 2. Build TC translations
python3 tools/scripts/build_translations.py

# 3. Inject into assets
python3 tools/scripts/inject_strings.py

# 4. Verify output
python3 tools/scripts/verify_build.py
```

---

## Project Structure

```
tc-localization/
├── dist/                      # Built/patched assets (ready to deploy)
├── source/                    # Extracted game asset sources
│   ├── zh-CN/                # (reference) Simplified Chinese
│   ├── zh-TW/                # Traditional Chinese source
│   ├── en-US/
│   ├── de-DE/
│   ├── es-ES/
│   ├── fr-FR/
│   ├── ko-KR/
│   ├── pl-PL/
│   ├── pt-BR/
│   └── ru-RU/
├── config/                    # Build configuration
├── tools/
│   └── scripts/              # Python build & deploy tools
├── README.md
├── modinfo.json
└── deploy.{sh,ps1}
```

---

## Contributing

Corrections, terminology improvements, and font enhancements welcome!

- **Translation issues?** Check `glossary/` and contribute fixes
- **Font glyphs missing?** Report via Issues with screenshot
- **Build tools?** See `tools/scripts/` for improvement suggestions

---

## License & Attribution

- **Game:** © Black Lab Games / Slitherine
- **Mod:** Community contribution under [MIT License](../../../LICENSE)
- **Font assets:** TextMesh Pro (© Unity Technologies)

