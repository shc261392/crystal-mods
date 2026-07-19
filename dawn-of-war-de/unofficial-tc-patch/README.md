# WH40K: Dawn of War DE — Unofficial Traditional Chinese Patch

Unofficial Traditional Chinese patch for **Warhammer 40,000: Dawn of War – Definitive Edition**.  
Fixes font size/weight, subtitle artifacts, and applies text corrections to `Engine.ucs`.

> 本模組為《戰鎚40,000：破曉之戰 決定版》的非官方繁體中文補丁，修正字型大小、字重、字幕殘字問題，並校正 `Engine.ucs` 的文字內容。  
> **中文安裝說明請見下方 [繁體中文安裝說明](#繁體中文安裝說明)。**

> **Download:** [GitHub Releases](https://github.com/shc261392/wh40k-dow-de-tc-mod/releases/latest) · [Nexus Mods](https://www.nexusmods.com/warhammerdawnofwardefinitiveedition/mods/41) — grab `wh40k-dow-de-tc-mod-v*.zip` (mod) from Releases and the Vortex extension from Nexus Mods.

---

## Installing the Mod

> **Finding your game folder:** In Steam, right-click **Dawn of War Definitive Edition** → **Manage** → **Browse local files**.  
> Common paths: `C:\Program Files (x86)\Steam\steamapps\common\Dawn of War Definitive Edition\` or `D:\SteamLibrary\steamapps\common\Dawn of War Definitive Edition\`

### Option A — Vortex Mod Manager (recommended)

1. **Install the game extension** — download `vortex-ext-game-warhammer40kdawnofwar-v*.zip` from [Nexus Mods](https://www.nexusmods.com/site/mods/1934), then drag it onto the Vortex **Extensions** tab and click *Enable*.  
  *(Only needed once. The extension is still under Vortex review, so drag-and-drop install is required for now.)*

2. **Add the mod** — drag `wh40k-dow-de-tc-mod-v*.zip` onto Vortex.

3. **Deploy** — click *Deploy Mods* in Vortex.  
   Vortex automatically renames `EnginLoc.sga` → `EnginLoc.sga.disabled` so the patched files take priority.

4. **Launch the game.** Chinese text should now render correctly.

To uninstall: click *Purge Mods* in Vortex. The original `EnginLoc.sga` is restored automatically.

---

### Option B — Manual install (Windows)

1. Download `wh40k-dow-de-tc-mod-v*.zip` from [Releases](https://github.com/shc261392/wh40k-dow-de-tc-mod/releases/latest).
2. Find your game folder (see above), open the `Engine\Locale\Chinese\` subfolder, and extract the zip there.
3. Launch the game. Done!

**To uninstall:**
1. Go to your game's `Engine\Locale\Chinese\` folder.
2. Delete `EnginLocMod.sga` and `Engine.ucs` (the files from this mod).

---

### Option C — Script install (Linux / WSL2 / Windows native)

Clone or download the repo, then run one command from the repo root:

**Linux / WSL2:**
```bash
bash deploy.sh
```

**Windows (PowerShell):**
```powershell
.\deploy.ps1
```

Both scripts auto-detect your Steam installation, create a backup, patch font
files, and deploy. To revert:

```bash
bash uninstall.sh   # Linux / WSL2
.\uninstall.ps1     # Windows
```

---

## 繁體中文安裝說明

> **下載：** [GitHub Releases](https://github.com/shc261392/wh40k-dow-de-tc-mod/releases/latest) · [Nexus Mods](https://www.nexusmods.com/warhammerdawnofwardefinitiveedition/mods/41) — 模組壓縮檔從 Releases 下載，Vortex 擴充套件則從 Nexus Mods 下載。

### 如何找到遊戲資料夾

在 Steam 的遊戲庫中，對《破曉之戰 決定版》**點右鍵 → 管理 → 瀏覽本機檔案**，即可開啟遊戲根目錄。

常見安裝路徑：
- `C:\Program Files (x86)\Steam\steamapps\common\Dawn of War Definitive Edition\`
- `D:\SteamLibrary\steamapps\common\Dawn of War Definitive Edition\`

---

### 方式 A — Vortex Mod Manager（建議）

1. **安裝遊戲擴充套件** — 將 `vortex-ext-game-warhammer40kdawnofwar-v*.zip` 拖入 Vortex 的 **Extensions** 分頁，點選啟用。  
   *（只需執行一次，讓 Vortex 知道 DoW DE 的安裝位置。）*

2. **新增模組** — 將 `wh40k-dow-de-tc-mod-v*.zip` 拖入 Vortex。

3. **部署** — 在 Vortex 中點選 *Deploy Mods*。  
   Vortex 會自動將 `EnginLoc.sga` 重新命名為 `EnginLoc.sga.disabled`，讓補丁檔案取得優先權。

4. **啟動遊戲。** 繁體中文文字應已正常顯示。

解除安裝：在 Vortex 中點選 *Purge Mods*，原始 `EnginLoc.sga` 將自動還原。

---

### 方式 B — 手動安裝（Windows）

1. 從 [Releases](https://github.com/shc261392/wh40k-dow-de-tc-mod/releases/latest) 下載 `wh40k-dow-de-tc-mod-v*.zip`。
2. 使用上方說明找到遊戲根目錄，進入 `Engine\Locale\Chinese\` 子資料夾，將壓縮檔解壓縮至此處。
3. 啟動遊戲，完成！

**解除安裝：**
1. 回到遊戲的 `Engine\Locale\Chinese\` 資料夾。
2. 刪除 `EnginLocMod.sga` 以及 `Engine.ucs`（本模組的檔案）。

---

### 方式 C — 腳本安裝（Linux / WSL2 / Windows）

Clone 或下載本 repo 後，在 repo 根目錄執行：

**Linux / WSL2：**
```bash
bash deploy.sh
```

**Windows（PowerShell）：**
```powershell
.\deploy.ps1
```

腳本會自動偵測 Steam 安裝路徑、建立備份並部署。還原方式：

```bash
bash uninstall.sh   # Linux / WSL2
.\uninstall.ps1     # Windows
```

---

## Companion: Keybinding Overhaul mod

A separate, standalone mod for fixing DoW:DE's stock key layout — most
notably enabling **plain `W`/`A`/`S`/`D` camera pan** without the awkward
`Shift+` requirement. Ships as preset zips (`vanilla`, `wasd-camera`) plus an
auto-generated hotkey cheat sheet per preset. See
[mod/keybinds/README.md](mod/keybinds/README.md) for details and
[scripts/build_keybind_presets.py](scripts/build_keybind_presets.py) for the
generator.

```bash
make keybinds-build        # regenerate presets from stock keydefaults.lua
make package-keybinds      # build a zip per preset in dist/
```

---

## Development Setup (Linux only)

Requires [uv](https://docs.astral.sh/uv/) and `make`.

```bash
make setup          # create .venv, install Python env
make help           # list all targets
```

### Common dev commands

| Command | What it does |
|---------|-------------|
| `make dry-run` | Preview font-fix without writing |
| `make apply` | Apply font-fix to `data/font/*.fnt` |
| `make dry-run-tc` | Preview TC text corrections |
| `make apply-tc` | Apply TC text corrections to `Engine.ucs` |
| `make deploy` | Full deploy to game installation |
| `make uninstall` | Revert deployment |
| `make restore-bak` | Restore `.fnt` files from `.bak` snapshots |

Override defaults:
```bash
make apply FONT=noto-serif-tc SIZE=36 MODE=all
make deploy --game-dir /path/to/game
```

---

## What the mod does

- **`data/font/*.fnt`** — Patches `sizeDefault` (and optionally all size keys) in
  every font configuration file to fix text clipping on high-DPI displays.
- **`Engine.ucs`** — Applies targeted Traditional Chinese text corrections
  (punctuation, typos, missing sentence endings).
- **Font switching** — Lets you choose between Noto Sans TC, Noto Serif TC, or
  Microsoft YaHei for CJK text rendering.

---

## Repository Layout

```
wh40k-dow-de-tc-mod/
├── data/
│   ├── font/          ← .fnt configs + bundled TTF/TTC fonts
│   ├── art/           ← UI/glyph flash assets
│   └── sound/         ← (placeholder; reserved for audio overrides)
├── mod/
│   ├── info.json      ← Nexus Mods metadata
│   ├── installInfo.json
│   └── modinfo.json
├── reference/
│   ├── en/Engine.en.ucs   ← English reference for i18n comparison
│   └── compare/           ← Side-by-side diff TSVs
├── scripts/
│   ├── apply_font_fix.py       ← Core font patcher (uv run)
│   ├── apply_tc_corrections.py ← TC text corrections (uv run)
│   ├── setup_relic_tool.ps1    ← Relic SGA tool installer (Windows)
│   ├── unpack_chinese_locale.ps1
│   └── repack_chinese_locale.ps1
├── Engine.ucs         ← Patched TC localization strings
├── deploy.sh          ← Linux / WSL2 deploy (1 command)
├── uninstall.sh       ← Linux / WSL2 uninstall / revert
├── deploy.ps1         ← Windows native deploy (1 command)
├── uninstall.ps1      ← Windows native uninstall / revert
├── Makefile           ← Dev workflow (uv, make)
└── pyproject.toml     ← uv project definition
```

---

## Deployment Details

### Auto-detection

Both deploy scripts detect the Steam installation automatically:

- **Linux**: scans `~/.local/share/Steam`, `~/.steam/steam`, Flatpak paths, and
  all Steam library roots found in `libraryfolders.vdf`.
- **WSL2**: additionally scans `/mnt/c`, `/mnt/d`, etc. for Windows Steam paths.
- **Windows**: reads the registry (`HKLM\SOFTWARE\Valve\Steam`), common default
  paths, and all library roots from `libraryfolders.vdf`.

Override with `--game-dir PATH` (bash) or `-GameDir PATH` (PowerShell), or set
the `DOW_GAME_DIR` environment variable.

### Backup

Every deployment creates a timestamped backup in `backup/<YYYYMMDD-HHmmss>/`
containing the overwritten files. `uninstall.sh` / `uninstall.ps1` reads the
last deploy state from `.copilot_workspace/last_deploy*.env` and uses it to
restore from the correct backup automatically.

### How the mod loads

The game's locale system checks `Engine/Locale/Chinese/data/` **before** the
packed `.sga` archive. The deploy scripts rename `EnginLoc.sga` → `EnginLoc.sga.disabled`
so the patched `data/` folder takes precedence. Uninstall renames it back.

---

## Vortex Mod Manager

The DoW DE Vortex extension is still under Vortex review, so install it by dragging the zip onto Vortex's **Extensions** tab.

1. Download `vortex-ext-game-warhammer40kdawnofwar-v*.zip` from [Nexus Mods](https://www.nexusmods.com/site/mods/1934).
2. Open Vortex, drag the zip onto the **Extensions** tab, and click *Enable*.
3. Re-open Vortex, enable **Warhammer 40,000: Dawn of War - Definitive Edition**, then install `wh40k-dow-de-tc-mod-v*.zip` and click *Deploy Mods*.

---

## Font Options

```bash
make list-fonts      # show all font presets
make list-profiles   # show size profiles (1080p, 4k)

make apply FONT=noto-sans-tc   SIZE=34   # default
make apply FONT=noto-serif-tc  SIZE=36
make apply FONT=msyh           MODE=all
```

---

## Advanced: SGA Repacking (Windows only)

To repack a modified `data/` into a new `.sga` archive (optional):

1. Install SGA tools: `make setup-sga` (or `.\scripts\setup_relic_tool.ps1`)
2. Unpack: `.\scripts\unpack_chinese_locale.ps1`
3. Apply patches: `make apply`
4. Repack: `.\scripts\repack_chinese_locale.ps1`

See `FONT_FIX_README.md` for technical research notes.

---

## Platform Support

| Task | Linux | WSL2 | Windows |
|------|-------|------|---------|
| Python font patching | ✅ | ✅ | ✅ |
| TC text corrections | ✅ | ✅ | ✅ |
| Auto-deploy (`deploy.sh`) | ✅ | ✅ | — |
| Auto-deploy (`deploy.ps1`) | — | ✅ | ✅ |
| SGA unpack/repack | ❌ | ✅ | ✅ |
| `make` / uv (dev) | ✅ | ✅ | — |

---

## Known Issues / Troubleshooting

### Tutorial prompt appears after first deploy

**Symptom:** After running `deploy.sh` / `deploy.ps1` for the first time, the
game shows the "Do you want to play the tutorial?" prompt when clicking Campaign.

**Cause:** The game's locale-change detection reads
`Profiles/Profile1/playercfg.lua` and may reset
`Tutorial_DoWDE.HasClickedCampaign` to `false` when it detects modified locale
files. This is game-internal behaviour; no script in this mod writes to
`playercfg.lua`.

**Fix:** Simply dismiss the tutorial prompt — the flag is set back to `true`
immediately. The prompt will not appear again on subsequent launches with the
same locale files.

---

### "緝" character appended to WA campaign subtitles

**Symptom:** Voiced dialogue subtitles in the Winter Assault campaign show an
extra character (緝, U+7DC9) at the end of each line.

**Root cause (investigated and fixed):** `notosanstc-bold.ttf` has a glyph
mapped at codepoint U+0000 (the null terminator). DoW's subtitle renderer reads
the string including the null terminator and renders the font's glyph for that
codepoint. Because `gillsans_11b.fnt` (the dialogue subtitle font) previously
referenced `notosanstc-bold.ttf`, every subtitle ended with 緝.

**Fix applied (commit `7055d8b`):** `gillsans_11b.fnt` and `gillsans_bold_16.fnt`
now reference `notosanstc-medium.ttf`, which does not have a visible glyph at
U+0000. The artifact is gone.

If future font experiments re-introduce this file, avoid `notosanstc-bold.ttf`
for any font definition that is used to render subtitle or in-game dialogue text.

---

## Baseline Hash Verification

**IMPORTANT:** Use these hashes to verify the original/vanilla state of the locale files.  
Any backup or deployment state **not matching these hashes** is considered "touched" (TC-modified) and should not be used as a restore baseline.

### Original Vanilla Files (Clean Baseline)

These hashes represent the **unmodified original Chinese locale files** as shipped by Steam with the Definitive Edition:

| File | Size | SHA256 |
|------|------|--------|
| `Engine/Locale/Chinese/EnginLoc.sga` | 190M | `9174735668f20090bc5f1cbe443050b68a6e559aff288786f3b830e9e077cb4a` |
| `Engine/Locale/Chinese/Engine.ucs` | 1.6M | `215baacd2846db80229b5763723b4b998642f197507dec752d65ce473f22ff02` |

### Verification

To verify your files match the baseline:

**Linux / WSL2 / macOS:**
```bash
sha256sum "$GAME_DIR/Engine/Locale/Chinese/EnginLoc.sga" "$GAME_DIR/Engine/Locale/Chinese/Engine.ucs"
```

**Windows (PowerShell):**
```powershell
Get-FileHash -Algorithm SHA256 -Path "$env:GAME_DIR\Engine\Locale\Chinese\EnginLoc.sga", "$env:GAME_DIR\Engine\Locale\Chinese\Engine.ucs"
```

If your hashes **do not match**, the files have been modified. Restore from the original Steam installation or verify the game files via Steam's integrity check:
- Right-click **Dawn of War Definitive Edition** in Steam
- Select **Manage** → **Verify integrity of game files**

### Backup Interpretation

When `uninstall.sh` / `uninstall.ps1` restore from a timestamped backup, it uses the **most recent backup before the current session**.  
**If that backup's hashes do not match the baseline above, the backup is TC-modified** and should only be used for reverting an incomplete or broken TC deployment—not as a canonical source.

To force restoration to the true vanilla state, either:
1. Verify files via Steam (see above), or
2. Manually compare backup hashes against the table above and reject non-matching entries.

---

## For Developers: Building from Source

**Complete build documentation:** [`docs/BUILD_GUIDE.md`](docs/BUILD_GUIDE.md)

The build guide provides step-by-step instructions for reproducing the standard build process, including:
- Font size adjustment system (new in v1.0.6)
- Unified build workflow via `make build`
- SGA repacking with Archive.exe (WSL2 environment)
- Creating distribution packages
- Troubleshooting sandbox and WSL interop issues
- Build verification checklist

**Quick build:**
```bash
cd /home/shado/crystal-mods/dawn-of-war-de/unofficial-tc-patch

# Standard build (size 36, matches v1.0.5)
make build

# Vanilla fonts (size 32)
make build FONT_SIZE_INCREASE=0

# Large fonts (size 38)
make build FONT_SIZE_INCREASE=6
```

**Output:** `dist/wh40k-dow-de-tc-mod-v1.0.7.zip`

**Quality check:**
```bash
make lint  # Runs Ruff linting on all Python scripts
```

See the [BUILD_GUIDE.md](docs/BUILD_GUIDE.md) for complete details.
