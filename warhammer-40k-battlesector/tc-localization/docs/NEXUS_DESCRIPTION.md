# Nexus Mods description — TC Localization (mod page)

> Paste into the Nexus mod page description. 繁體中文在前（主要受眾），English below.
> 本頁「檔案（FILES）」下載區共有兩個檔案：
>   • 主檔案：繁體中文化本體
>   • 「Core (BepInEx6)」：必要的執行環境框架（只需安裝一次）

---

## 戰鎚 40,000：戰區 — 繁體中文化

適用於 **Warhammer 40,000: Battlesector（戰鎚 40,000：戰區）** 版本 **1.7.7**
的完整**繁體中文**化。將遊戲內建的簡體中文轉換為繁體中文 —— 涵蓋選單、陣營、單位、
戰役、任務文字、單位描述與啟動器介面。

遊戲原生僅提供簡體中文，本模組提供正體（繁體）中文的完整體驗。

### ⚠️ 安裝需求（請先閱讀）

本模組分為**兩個檔案**（皆位於本頁面的「檔案（FILES）」下載區），各安裝一次即可，
日後更新時通常只需更新本地化主檔案：

1. **Core (BepInEx6)** —— 一次性的執行環境相依套件（**必要**，請先安裝）。
   幾乎不需要更新。
2. **繁體中文化（主檔案）** —— 字型、文字與執行期修正外掛。日後的更新以此檔為主。

> 為什麼需要框架？遊戲的單位／戰役**描述文字**是由一個「沒有中文字符」的字型在
> 執行期算繪，會把繁體特有字（如 將／領／隊／遠／眾）算繪成亂碼。單純修改遊戲檔案
> 無法解決，因此以一個小型 BepInEx 外掛（`TCFix`）在執行期修正字型。此外掛為開源，
> 已隨本模組附上。

### 安裝方式（Vortex，推薦）

1. 安裝 **Warhammer 40,000: Battlesector 的 Vortex 擴充功能**（Games → 搜尋），
   讓 Vortex 能管理本遊戲。
2. 安裝 **Core (BepInEx6)** 檔案，然後按 **Deploy（部署）**。
3. 安裝**繁體中文化（主檔案）**，然後按 **Deploy**。
4. 啟動遊戲**一次**並進入主選單（首次啟動較慢 —— BepInEx 正在初始化），接著在
   「選項」中將語言設為 **中文（簡體）**，畫面即會顯示為**繁體中文**。

### 安裝方式（手動）

先將 **Core (BepInEx6)** 解壓到遊戲根目錄，再將**本模組**解壓到同一個遊戲根目錄
（允許覆蓋）。啟動遊戲一次。

### 移除方式

Vortex：清除（purge）／移除兩個模組，原始遊戲檔案會自動還原。
手動：刪除遊戲根目錄的 `winhttp.dll` 以停用 BepInEx；還原備份的 `*.assets` 與 bundle。

### 相容性與注意事項

- 遊戲版本 **1.7.7**（Unity 6, IL2CPP），其他版本未測試。
- 主要支援 Windows；Linux/Proton 理論上可用，但測試較少。
- BepInEx 6 為預先發行（Bleeding Edge）版本，廣泛用於 IL2CPP 遊戲。
- 可隨時安全移除。

### 版本更新（0.2.2）

- **繁體字形**：字圖改由 **Noto Sans CJK TC** 重新烘焙，眾／骨／說 等字改用繁體字形。
- **全形標點**：句中標點改為全形（，。！？：；（）……），數字與版本號不受影響。
- **粗體**：降低 `<b>` 粗體權重，強調文字不再過粗。
- **更廣的執行期修正（TCFix 1.2.0）**：修正**退出遊戲**、**十字軍區域加成／獎勵**、
  存檔命名等先前仍亂碼的視窗，並將修正延遲由 1 秒縮短至約 0.2 秒（幾乎無閃爍）。
- 補齊先前缺字：`！ ？ ）`、項目符號 `•`、`∞`。

### 已知限制

- 少數不常用符號或極少數畫面若使用未涵蓋字型仍可能顯示異常，歡迎回報。

### 製作資訊與原始碼

- 文字轉換使用 OpenCC（s2tw，字元級，避免 s2twp 的詞語誤轉）。字型基於 Noto Sans CJK TC。
  校正詞彙表：`translation/zh-TW/glossary.tsv`（可編輯，`make build` 重建）。
- **`TCFix` 外掛為開源軟體，原始碼公開於 GitHub 供審閱與自行編譯**：
  <https://github.com/shc261392/crystal-mods/tree/main/warhammer-40k-battlesector/tc-localization/bepinex/TCFix>
- **Core (BepInEx6)** 為 **BepInEx 6（IL2CPP, Bleeding Edge）** 官方建置，未經修改重打包。
  官方來源（可自行下載驗證）：
  - BepInEx（LGPL-2.1）：<https://github.com/BepInEx/BepInEx>
  - Bleeding Edge builds：<https://builds.bepinex.dev/projects/bepinex_be>
  - 使用版本：**#785**，commit `6abdba4`
  重打包 ZIP 的 SHA-256 與原始建置雜湊值皆記載於模組內的 `docs/BEPINEX_SETUP.md`。

---

## Warhammer 40,000: Battlesector — Traditional Chinese Localization (English)

Full **Traditional Chinese** localization for **Warhammer 40,000: Battlesector**
(patch **1.7.7**). Converts the in-game Simplified Chinese to Traditional Chinese —
menus, factions, units, campaign, mission text, unit descriptions, and the launcher.

### ⚠️ Requirements

This mod ships as **two files on this page** (Files tab); install each once, then only
update the localization:

1. **Core (BepInEx6)** — a one-time runtime dependency (**required**, install first).
2. **Traditional Chinese Localization (main file)** — fonts, text, and the runtime fix
   plugin. This is the part updated over time.

> Why a framework? The game renders unit/campaign **descriptions** through a font with
> no Chinese glyphs and garbles Traditional-specific characters at runtime. File edits
> can't fix it — a tiny open-source BepInEx plugin (`TCFix`, included) corrects the font
> at runtime.

### Installation (Vortex — recommended)

1. Install the **Warhammer 40,000: Battlesector Vortex extension** (Games → search).
2. Install the **Core (BepInEx6)** file, then **Deploy**.
3. Install the **Localization (main file)**, then **Deploy**.
4. Launch once to the main menu (first launch is slower — BepInEx is initializing),
   then set language to **Chinese (Simplified)** in Options. It displays as Traditional.

### Uninstall

Vortex: purge/remove both mods — originals restore automatically. Manual: delete
`winhttp.dll` from the game root and restore the backed-up `*.assets` / bundle files.

### Compatibility & notes

- Game **1.7.7** (Unity 6, IL2CPP). Windows primary; Linux/Proton less tested.
- BepInEx 6 is a Bleeding-Edge pre-release, widely used for IL2CPP games.
- Safe to remove at any time.

### What's new in 0.2.2

- **Traditional letterforms** — CJK glyphs re-baked from **Noto Sans CJK TC**
  (眾/骨/說 etc. now use TC shapes).
- **Full-width punctuation** — `，。！？：；（）……` where adjacent to CJK; numbers and
  version strings untouched.
- **Lighter bold** — reduced `<b>` weight so emphasis isn't too heavy.
- **Broader runtime fix (TCFix 1.2.0)** — now also corrects the **exit-game modal**,
  **Crusade zone modifiers/rewards**, and save/name dialogs; correction latency cut
  from ~1s to ~0.2s (no visible flash).
- Baked previously-missing glyphs: `！ ？ ）`, bullet `•`, `∞`.

### Known limitations

- A few uncommon symbols or rare screens using an uncovered font may still misrender
  — please report them.

### Credits & source

- Text via OpenCC **`s2tw`** (character-level; avoids `s2twp` phrase errors such as
  `重装 → 重灌`). Fonts based on Noto Sans CJK TC. Editable term glossary at
  `translation/zh-TW/glossary.tsv` (`make build` rebuilds).
- **`TCFix` plugin is open source** — audit or build it yourself from the repository:
  <https://github.com/shc261392/crystal-mods/tree/main/warhammer-40k-battlesector/tc-localization/bepinex/TCFix>
- **Core (BepInEx6)** is an unmodified repackage of the official **BepInEx 6
  (IL2CPP, Bleeding Edge)** build. Verify/download from source:
  - BepInEx (LGPL-2.1): <https://github.com/BepInEx/BepInEx>
  - Bleeding Edge builds: <https://builds.bepinex.dev/projects/bepinex_be>
  - Build used: **#785**, commit `6abdba4`
  The repackaged ZIP's SHA-256 and the original build hash are recorded in the mod's
  `docs/BEPINEX_SETUP.md`.
