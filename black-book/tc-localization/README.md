# Black Book — Traditional Chinese Localization Mod

**繁體中文本地化模組**

> **English** · [中文](#繁體中文安裝說明)

Unofficial Traditional Chinese (繁體中文 / 正體中文) localization mod for **Black Book** (Steam App ID 1138660).

Converts game UI text from English to Taiwan Traditional Chinese (zh-TW) by directly replacing localization asset files, with professional terminology and Noto Sans TC font support.

## Features

- ✓ Full UI text translation via Unity asset replacement (no plugins needed)
- ✓ Taiwan terminology (Taiwan-specific word choices and phrases)
- ✓ Noto Sans TC font — excellent CJK character coverage
- ✓ Multiple installation methods (Vortex, manual, script-based)
- ✓ Works on Windows, WSL2, and Linux/Proton
- ✓ Automatic backup & restoration

## How It Works

This mod replaces the game's localization asset files in `Black Book_Data/resources/` with TC versions. No third-party plugins or translators are required—just direct asset replacement.

## Installation

### Option A — Vortex Mod Manager (Recommended)

1. **Install the Vortex extension**:
   - Download `vortex-ext-game-black-book-v*.zip` from [Nexus Mods](#nexus-link)
   - Drag it onto Vortex's **Extensions** tab and click *Enable*
   - (Only needed once)

2. **Install the TC mod**:
   - Download `tc-localization-v*.zip` from [Releases](#releases)
   - Drag it onto Vortex's **Mods** tab

3. **Deploy**:
   - Click *Deploy Mods* in Vortex
   - Launch Black Book

4. **Uninstall** (optional):
   - Click *Purge Mods* in Vortex

### Option B — Manual Install (Windows)

1. Download `tc-localization-v*.zip` from [Releases](#releases)
2. Locate your Black Book game folder:
   - In Steam, right-click **Black Book** → **Manage** → **Browse local files**
   - Common paths: `C:\Program Files (x86)\Steam\steamapps\common\Black Book\`
3. Extract the zip to the game folder
4. Launch the game — text should appear in Traditional Chinese

**To uninstall**:
- Delete the TC asset files from `Black Book_Data/resources/`
- Delete `Fonts/NotoSansTC.asset` (if present)

### Option C — Script Install (Linux / WSL2 / Windows PowerShell)

**Linux / WSL2**:
```bash
cd /path/to/tc-localization
bash deploy.sh
```

**Windows (PowerShell, Run as Administrator)**:
```powershell
cd C:\path\to\tc-localization
.\deploy.ps1
```

Both scripts:
- Auto-detect your Steam installation
- Create a timestamped backup
- Deploy localization asset files
- Print status and next steps

**To uninstall**:
```bash
bash uninstall.sh                  # Linux/WSL2
.\uninstall.ps1                    # Windows (PowerShell)
```

## System Requirements

- **Black Book** (Steam App 1138660)
- Windows 7+ or Linux (via Proton)
- ~5 MB free space
- Vortex 1.2+ (if using Vortex installation)

## Compatibility

- ✓ Windows 11 / Windows 10
- ✓ WSL2 + Steam
- ✓ Linux + Proton
- ✓ Save game compatible (no save data modifications)

## Troubleshooting

### Text appears as blank boxes (tofu)

This usually means the TC font asset didn't load:
1. Verify `Fonts/NotoSansTC.asset` is deployed to the game folder
2. Try reinstalling with Vortex: *Purge Mods* → *Deploy Mods*
3. Check game logs for font loading errors

### Text doesn't appear in TC

1. Verify asset files are in `Black Book_Data/resources/`
2. Try restarting the game
3. Check file integrity: `ls -la Black Book_Data/resources/`

### Deploy script can't find the game

1. Install Black Book to Steam (not Epic/GOG)
2. Run the script from the mod directory
3. Manually specify the game path (Linux):
   ```bash
   GAME_PATH=/mnt/c/Program\ Files\ \(x86\)/Steam/steamapps/common/Black\ Book bash deploy.sh
   ```

## Credits

- **Translation**: Community
- **Font**: [Noto Sans TC](https://fonts.google.com/noto/specimen/Noto+Sans+TC) by Google / Adobe
- **Conversion tool**: [OpenCC](https://github.com/BYVoid/OpenCC)

## License

This mod is provided as-is for personal use. Black Book is © HypeTrain Digital / Morteshka.

---

## 繁體中文安裝說明

**Black Book — Traditional Chinese Localization Mod**（繁體中文本地化模組）

> **中文** · [English](#features) 上方

非官方 Black Book（Steam App ID 1138660）繁體中文本地化模組。

透過直接取代遊戲本地化資源檔案，將遊戲 UI 文字從英文轉換成台灣繁體中文（zh-TW），配備專業術語及 Noto Sans TC 字型。

### 運作方式

本模組取代 `Black Book_Data/resources/` 資料夾中的遊戲本地化資源檔案為繁體中文版本。不需要任何第三方外掛或翻譯工具—— 只是單純的資源檔案取代。

### 安裝方式

#### 方式 A — Vortex Mod Manager（推薦）

1. **安裝 Vortex 擴充套件**：
   - 從 [Nexus Mods](#nexus-link) 下載 `vortex-ext-game-black-book-v*.zip`
   - 將檔案拖放到 Vortex 的 **Extensions** 標籤並點擊 *Enable*
   - （只需要做一次）

2. **安裝 TC 模組**：
   - 從 [Releases](#releases) 下載 `tc-localization-v*.zip`
   - 將檔案拖放到 Vortex 的 **Mods** 標籤

3. **部署**：
   - 在 Vortex 中點擊 *Deploy Mods*
   - 啟動 Black Book

4. **移除**（可選）：
   - 在 Vortex 中點擊 *Purge Mods*

#### 方式 B — 手動安裝（Windows）

1. 從 [Releases](#releases) 下載 `tc-localization-v*.zip`
2. 找到 Black Book 遊戲資料夾：
   - 在 Steam 庫中對 **Black Book** 點右鍵 → **管理** → **瀏覽本機檔案**
   - 常見路徑：`C:\Program Files (x86)\Steam\steamapps\common\Black Book\`
3. 將 zip 檔案解壓到遊戲資料夾
4. 啟動遊戲 — 文字應該會以繁體中文顯示

**移除方式**：
- 刪除 `Black Book_Data/resources/` 資料夾中的繁體中文資源檔案
- 刪除 `Fonts/NotoSansTC.asset`（如果存在）

#### 方式 C — 指令碼安裝（Linux / WSL2 / Windows PowerShell）

**Linux / WSL2**：
```bash
cd /path/to/tc-localization
bash deploy.sh
```

**Windows（PowerShell，以系統管理員身分執行）**：
```powershell
cd C:\path\to\tc-localization
.\deploy.ps1
```

指令碼會自動：
- 偵測 Steam 安裝位置
- 建立備份
- 部署本地化資源檔案
- 顯示狀態和後續步驟

**移除方式**：
```bash
bash uninstall.sh                  # Linux/WSL2
.\uninstall.ps1                    # Windows (PowerShell)
```

### 常見問題

#### 文字顯示為方塊（豆腐字）

通常表示字型資源載入失敗：
1. 確認 `Fonts/NotoSansTC.asset` 已部署到遊戲資料夾
2. 試著用 Vortex 重新安裝：*Purge Mods* → *Deploy Mods*
3. 檢查遊戲日誌確認字型是否正常載入

#### 文字沒有顯示為繁體中文

1. 確認資源檔案在 `Black Book_Data/resources/` 資料夾中
2. 試著重啟遊戲
3. 檢查檔案：`ls -la Black Book_Data/resources/`

#### 安裝指令碼找不到遊戲

1. 在 Steam 上安裝 Black Book（不是 Epic/GOG）
2. 從模組資料夾執行指令碼
3. 手動指定遊戲路徑（Linux）：
   ```bash
   GAME_PATH=/mnt/c/Program\ Files\ \(x86\)/Steam/steamapps/common/Black\ Book bash deploy.sh
   ```

### 下載連結

- **Mod 發佈**: [GitHub Releases](#releases) / [Nexus Mods](#nexus-link)
- **Vortex 擴充套件**: [Nexus Mods](#nexus-link)
- **原始碼**: [GitHub](#github)

### 系統需求

- **Black Book**（Steam App 1138660）
- Windows 7+ 或 Linux（透過 Proton）
- 約 5 MB 可用空間
- Vortex 1.2+（如使用 Vortex 安裝方式）

### 致謝

- **翻譯**: 社群
- **字型**: [Noto Sans TC](https://fonts.google.com/noto/specimen/Noto+Sans+TC)（Google / Adobe）
- **轉換工具**: [OpenCC](https://github.com/BYVoid/OpenCC)

---

## Download Links

- **Mod**: [GitHub Releases](https://github.com/shc261392/crystal-mods/releases) · [Nexus Mods](#nexus)
- **Vortex Extension**: [Nexus Mods](#nexus)
- **Source**: [GitHub](https://github.com/shc261392/crystal-mods/tree/main/black-book/tc-localization)

---

*Last updated: 2026-06-10*

## Features

- ✓ Full UI text translation (menus, dialogs, item descriptions)
- ✓ Taiwan terminology (Taiwan-specific word choices and phrases)
- ✓ Noto Sans TC font — excellent CJK character coverage
- ✓ Multiple installation methods (Vortex, manual, script-based)
- ✓ Works on Windows, WSL2, and Linux/Proton
- ✓ Automatic backup & restoration

## Installation

### Option A — Vortex Mod Manager (Recommended)

1. **Install the Vortex extension**:
   - Download `vortex-ext-game-black-book-v*.zip` from [Nexus Mods](#nexus-link)
   - Drag it onto Vortex's **Extensions** tab and click *Enable*
   - (Only needed once)

2. **Install the TC mod**:
   - Download `tc-localization-v*.zip` from [Releases](#releases)
   - Drag it onto Vortex's **Mods** tab

3. **Deploy**:
   - Click *Deploy Mods* in Vortex
   - Launch Black Book

4. **Uninstall** (optional):
   - Click *Purge Mods* in Vortex

### Option B — Manual Install (Windows)

1. Download `tc-localization-v*.zip` from [Releases](#releases)
2. Locate your Black Book game folder:
   - In Steam, right-click **Black Book** → **Manage** → **Browse local files**
   - Common paths: `C:\Program Files (x86)\Steam\steamapps\common\Black Book\`
3. Extract the zip to the game folder
4. Launch the game — text should appear in Traditional Chinese

**To uninstall**:
- Delete the `AutoTranslator/Translation/zh-TW` folder and `Fonts/NotoSansTC.asset`

### Option C — Script Install (Linux / WSL2 / Windows PowerShell)

**Linux / WSL2**:
```bash
cd /path/to/tc-localization
bash deploy.sh
```

**Windows (PowerShell, Run as Administrator)**:
```powershell
cd C:\path\to\tc-localization
.\deploy.ps1
```

Both scripts:
- Auto-detect your Steam installation
- Create a timestamped backup
- Deploy localization files
- Print status and next steps

**To uninstall**:
```bash
bash uninstall.sh                  # Linux/WSL2
.\uninstall.ps1                    # Windows (PowerShell)
```

## System Requirements

- **Black Book** (Steam App 1138660)
- Windows 7+ or Linux (via Proton)
- ~5 MB free space
- Vortex 1.2+ (if using Vortex installation)

## Compatibility

- ✓ Windows 11 / Windows 10
- ✓ WSL2 + Steam
- ✓ Linux + Proton
- ✓ Save game compatible (no save data modifications)

## Troubleshooting

### Text appears as blank boxes (tofu)

This usually means font rendering failed:
1. Verify `Fonts/NotoSansTC.asset` is deployed to the game folder
2. Try reinstalling with Vortex: *Purge Mods* → *Deploy Mods*
3. Check TextMeshPro is loading correctly in game logs

### Text doesn't appear in TC

1. Verify `AutoTranslator/Translation/zh-TW/` contains `Text/_Translations.txt`
2. Try restarting the game
3. Check file is not empty: `wc -l AutoTranslator/Translation/zh-TW/Text/_Translations.txt`

### Deploy script can't find the game

1. Install Black Book to Steam (not Epic/GOG)
2. Run the script from the mod directory
3. Manually specify the game path:
   ```bash
   GAME_PATH=/mnt/c/Program\ Files\ \(x86\)/Steam/steamapps/common/Black\ Book bash deploy.sh
   ```

## Credits

- **Translation**: Community
- **Font**: [Noto Sans TC](https://fonts.google.com/noto/specimen/Noto+Sans+TC) by Google / Adobe
- **Conversion tool**: [OpenCC](https://github.com/BYVoid/OpenCC)

## License

This mod is provided as-is for personal use. Black Book is © HypeTrain Digital / Morteshka.

---

## 繁體中文安裝說明

**Black Book — Traditional Chinese Localization Mod**（繁體中文本地化模組）

> **中文** · [English](#features) 上方

非官方 Black Book（Steam App ID 1138660）繁體中文本地化模組。

將遊戲 UI 文字從英文轉換成台灣繁體中文（zh-TW），配備專業術語及 Noto Sans TC 字型。

### 安裝方式

#### 方式 A — Vortex Mod Manager（推薦）

1. **安裝 Vortex 擴充套件**：
   - 從 [Nexus Mods](#nexus-link) 下載 `vortex-ext-game-black-book-v*.zip`
   - 將檔案拖放到 Vortex 的 **Extensions** 標籤並點擊 *Enable*
   - （只需要做一次）

2. **安裝 TC 模組**：
   - 從 [Releases](#releases) 下載 `tc-localization-v*.zip`
   - 將檔案拖放到 Vortex 的 **Mods** 標籤

3. **部署**：
   - 在 Vortex 中點擊 *Deploy Mods*
   - 啟動 Black Book

4. **移除**（可選）：
   - 在 Vortex 中點擊 *Purge Mods*

#### 方式 B — 手動安裝（Windows）

1. 從 [Releases](#releases) 下載 `tc-localization-v*.zip`
2. 找到 Black Book 遊戲資料夾：
   - 在 Steam 庫中對 **Black Book** 點右鍵 → **管理** → **瀏覽本機檔案**
   - 常見路徑：`C:\Program Files (x86)\Steam\steamapps\common\Black Book\`
3. 將 zip 檔案解壓到遊戲資料夾
4. 啟動遊戲 — 文字應該會以繁體中文顯示

**移除方式**：
- 刪除 `AutoTranslator/Translation/zh-TW` 資料夾和 `Fonts/NotoSansTC.asset`

#### 方式 C — 指令碼安裝（Linux / WSL2 / Windows PowerShell）

**Linux / WSL2**：
```bash
cd /path/to/tc-localization
bash deploy.sh
```

**Windows（PowerShell，以系統管理員身分執行）**：
```powershell
cd C:\path\to\tc-localization
.\deploy.ps1
```

指令碼會自動：
- 偵測 Steam 安裝位置
- 建立備份
- 部署本地化檔案
- 顯示狀態和後續步驟

**移除方式**：
```bash
bash uninstall.sh                  # Linux/WSL2
.\uninstall.ps1                    # Windows (PowerShell)
```

### 常見問題

#### 文字顯示為方塊（豆腐字）

通常表示字型載入失敗：
1. 確認 `Fonts/NotoSansTC.asset` 已部署到遊戲資料夾
2. 試著用 Vortex 重新安裝：*Purge Mods* → *Deploy Mods*
3. 檢查遊戲日誌確認 TextMeshPro 是否正常載入

#### 文字沒有顯示為繁體中文

1. 確認 `AutoTranslator/Translation/zh-TW/` 包含 `Text/_Translations.txt`
2. 試著重啟遊戲
3. 檢查檔案不是空的：`wc -l AutoTranslator/Translation/zh-TW/Text/_Translations.txt`

#### 安裝指令碼找不到遊戲

1. 在 Steam 上安裝 Black Book（不是 Epic/GOG）
2. 從模組資料夾執行指令碼
3. 手動指定遊戲路徑（Windows）：
   ```powershell
   $env:GAME_PATH = "D:\SteamLibrary\steamapps\common\Black Book"
   .\deploy.ps1
   ```

### 下載連結

- **Mod 發佈**: [GitHub Releases](#releases) / [Nexus Mods](#nexus-link)
- **Vortex 擴充套件**: [Nexus Mods](#nexus-link)
- **原始碼**: [GitHub](#github)

### 系統需求

- **Black Book**（Steam App 1138660）
- Windows 7+ 或 Linux（透過 Proton）
- 約 5 MB 可用空間
- Vortex 1.2+（如使用 Vortex 安裝方式）

### 致謝

- **翻譯**: 社群
- **字型**: [Noto Sans TC](https://fonts.google.com/noto/specimen/Noto+Sans+TC)（Google / Adobe）
- **轉換工具**: [OpenCC](https://github.com/BYVoid/OpenCC)

---

## Download Links

- **Mod**: [GitHub Releases](https://github.com/shc261392/crystal-mods/releases) · [Nexus Mods](#nexus)
- **Vortex Extension**: [Nexus Mods](#nexus)
- **Source**: [GitHub](https://github.com/shc261392/crystal-mods/tree/main/black-book/tc-localization)

---

*Last updated: 2026-06-10*
