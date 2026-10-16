# Nexus Mods Description — Black Book Traditional Chinese Localization

## Short Description (max 250 chars)

Traditional Chinese (繁體中文) localisation for Black Book. Converts the game's built-in Simplified Chinese config files and dialogue/UI text to Traditional, with a Traditional typeface. Requires the BepInEx Framework mod.

---

## Full Description

**繁體中文 Traditional Chinese Localization**

Unofficial community Traditional Chinese (繁體中文 / 正體中文) localisation for
**Black Book** (Steam App ID 1138660).

本模組為《Black Book》的社群繁體中文化補丁。

---

**How It Works 運作方式**

Black Book already ships a complete Simplified Chinese localisation. This mod
converts it to Traditional Chinese using [OpenCC](https://github.com/BYVoid/OpenCC)
`s2twp` plus a set of reviewed terminology corrections, and installs a BepInEx
plugin that:

- converts the game's **dialogue database** and **UI localisation table** in
  memory at runtime (12,720 strings), and
- applies a Traditional-capable typeface (**Iansui**, 芫荽) so Traditional-only
  characters no longer render as empty boxes (`口口口`).

本模組使用 OpenCC `s2twp` 與人工校訂的術語修正，將遊戲內建的簡體中文轉為繁體，
並透過 BepInEx 外掛在執行時轉換對話資料庫與介面文字，同時套用繁體字型。

---

**Coverage 覆蓋範圍**

- **Converted in the config files** — item names and descriptions, ability
  names, quest and chapter text, the demon list and the credits screen:
  **3,479 strings in 1,448 files**.
- **Converted at runtime by the plugin** — the dialogue database and the UI
  localisation table.
- **May still appear Simplified** — some text baked into Unity assets (parts of
  the menus and settings). Closing that gap is ongoing work.

- **設定檔已轉換** — 物品名稱與說明、能力名稱、任務與章節文字、惡魔列表、製作
  人員名單：**1,448 個檔案、3,479 條字串**。
- **執行時由外掛轉換** — 對話資料庫與介面文字表。
- **仍可能顯示簡體** — 部分內嵌於 Unity 資源的選單與設定文字，仍在持續處理中。

The game ships its own CJK font, so no font needs to be installed manually; the
mod's plugin supplies a consistent Traditional typeface.

---

**Requirements 需求**

- **Black Book** (Steam App ID 1138660), Windows.
- **BepInEx Framework** (BepInEx 5.4.23.5 x64) — **required**. Install it once
  before this mod. Black Book is a Unity 2018.4 Mono game, so BepInEx 5 is used
  (not BepInEx 6 IL2CPP).
- For Vortex install: the **Black Book Vortex extension**.

---

**Installation 安裝方式**

Option A — Vortex (recommended 建議)

1. Install the Black Book Vortex extension.
   安裝 Black Book Vortex 擴充套件。
2. Install **BepInEx Framework** (required dependency).
   安裝 **BepInEx Framework**（必要）。
3. Drag this mod's zip onto Vortex and click **Deploy Mods**.
   將本模組壓縮檔拖入 Vortex，點選「Deploy Mods」。
4. Launch the game.
   啟動遊戲。

Option B — Manual 手動安裝

1. Install the BepInEx Framework first (extract it into the game root).
   先安裝 BepInEx Framework（解壓縮至遊戲根目錄）。
2. Extract this mod over the game folder, merging into
   `Black Book_Data/StreamingAssets/Config/` and `BepInEx/plugins/`.
   將本模組解壓縮覆蓋至遊戲目錄，合併到上述兩個資料夾。

To Uninstall 解除安裝:

- Vortex: click **Purge Mods** (Vortex restores the overwritten files).
  Vortex：點選「Purge Mods」（Vortex 會自動還原）。
- Manual: restore the game's own `config_zh.yaml` files (see the mod README), or
  verify the game files through Steam.
  手動：還原遊戲原始的 `config_zh.yaml`，或透過 Steam 驗證遊戲檔案。

---

**Uninstall / restore note 還原說明**

The mod README's uninstall scripts restore the game's original Simplified
Chinese files from a checked-in copy (`source/sc/`). No separate backup is
needed.

---

**Credits 製作群**

- **Game**: Black Book © Morteshka / HypeTrain Digital
- **Simplified Chinese localisation**: the original developers and community
- **Conversion**: [OpenCC](https://github.com/BYVoid/OpenCC) `s2twp`
- **Typeface**: Iansui (芫荽), SIL Open Font License
- **Mod**: Community

This is an unofficial fan project. Not affiliated with or endorsed by Morteshka
or HypeTrain Digital.
