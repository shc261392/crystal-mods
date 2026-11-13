# Nexus Mods Description — Battlesector Traditional Chinese Localization

## Short Description (max 250 chars)
Traditional Chinese (繁體中文) localization for Warhammer 40,000: Battlesector. Replaces Simplified Chinese slot. Select "Chinese (Simplified)" in-game to display Traditional Chinese.

---

## Full Description

**繁體中文 Traditional Chinese Localization**

Community Traditional Chinese (繁體中文) localization mod for Warhammer 40,000: Battlesector.

本模組為《戰鎚40,000：Battlesector》的社群繁體中文化補丁。

---

**How It Works 運作方式**

This mod replaces the Simplified Chinese (SC) locale text in the game's asset files with Traditional Chinese, and ships TextMesh Pro fonts re-baked with full Traditional glyph coverage.

本模組將遊戲資源檔案中的簡體中文文字替換為繁體中文，並附上以繁體字形完整重製的 TextMesh Pro 字型。

- `resources.assets` — the seven Chinese text repositories (units, campaign, barks, UI) converted with OpenCC + a lore glossary.
- `sharedassets2.assets` + the startup and map-builder bundles — the game fonts extended with every Traditional glyph the text needs (Noto Sans CJK TC), so nothing renders as a box.
- `TCFix` — a small BepInEx 6 (IL2CPP) plugin that switches any CJK text still drawn with a partial font to the full Traditional font at runtime.

Text is converted from the official Simplified Chinese; the terminology glossary is editable and community corrections are welcome.

文字由官方簡體中文轉換而來；術語表可編輯，歡迎提供修正。

**Requires / 需求**

- Warhammer 40,000: Battlesector **1.8.0** (Steam / GOG).
- **BepInEx Framework** mod (BepInEx 6 IL2CPP runtime) — install it first and launch the game once.
- Windows 10/11 (Linux/Proton works but is less tested).

---

**Known Limitations 已知限制**

- The conversion is character-level Traditional Chinese with a curated glossary; some names keep the official wording.
- Text added by future game patches will appear in Simplified Chinese until the mod is rebuilt.
- If a character renders as a box or in Simplified form, report the screen and the exact text.

- 轉換採用逐字繁體化加上自訂術語表，部分名稱保留官方用語。
- 未來遊戲更新新增的文字會先以簡體顯示，直到模組重新建置。
- 若出現方框或簡體字，請回報畫面和文字內容。

---

**Installation 安裝方式**

Option A - Vortex (Recommended 建議)
1. Install the Battlesector Vortex extension (required, see Files tab)
   安裝 Battlesector Vortex 擴充套件（必要，請見檔案分頁）
2. Install **BepInEx Framework**, then Deploy, and launch the game once
   安裝 **BepInEx Framework**、部署，並啟動遊戲一次
3. Drag this mod zip onto Vortex and Deploy
   將此模組壓縮檔拖入 Vortex 並部署
4. Launch the game and select Chinese (Simplified) in the language settings
   啟動遊戲並在語言設定中選擇 Chinese (Simplified)

Option B - Manual Installation 手動安裝
1. Install the BepInEx Framework zip into the game folder first
   先將 BepInEx Framework 壓縮檔解壓到遊戲資料夾
2. Backup these files:
   `Warhammer 40K Battlesector_Data/resources.assets`,
   `Warhammer 40K Battlesector_Data/sharedassets2.assets`,
   `Warhammer 40K Battlesector_Data/StreamingAssets/startup_assets_all.bundle`,
   `Warhammer 40K Battlesector_Data/StreamingAssets/mapbuilder-tools_assets_all.bundle`,
   `Launcher/Localization/stringsChinese.resx`
   備份上述檔案
3. Extract this mod's zip to the game installation directory
   解壓縮本模組至遊戲安裝目錄
4. Launch the game and select Chinese (Simplified)
   啟動遊戲並選擇 Chinese (Simplified)

To Uninstall 解除安裝:
- Vortex: Purge/remove both mods (originals restore automatically)
  Vortex：清除/移除兩個模組（自動還原原始檔案）
- Manual: Restore the backed-up files above and delete `BepInEx/plugins/TCFix.dll`
  手動：還原上述備份檔案，並刪除 `BepInEx/plugins/TCFix.dll`

---

**Translation Status 翻譯狀態**

All text repositories shipped with the game are converted: unit and weapon names, abilities, campaign and mission text, barks, and the launcher. The glossary (`translation/zh-TW/glossary.tsv`) carries the reviewed term corrections.

遊戲內所有文字庫皆已轉換：單位與武器名稱、技能、戰役與任務文字、語音文字，以及啟動器。術語修正集中於 `translation/zh-TW/glossary.tsv`。

Feedback and corrections welcome. 歡迎回饋與修正建議。
