# Nexus Mods description — TC Localization (mod page)

> Paste into the Nexus mod page description. 繁體中文在前（主要受眾），English below.
> 本頁「檔案（FILES）」下載區共有兩個檔案：
>   • 主檔案：繁體中文化本體
>   • 「Core (BepInEx6)」：必要的執行環境框架（只需安裝一次）

---

## 戰鎚 40,000：戰鬥區 — 繁體中文化

適用於 **Warhammer 40,000: Battlesector（戰鎚 40,000：戰鬥區）** 版本 **1.7.7**
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

### 已知限制（持續改善中）

- 部分字（例如 眾）目前使用日文／簡體字形，而非繁體字形 —— 計畫改用繁體中文
  Noto 字型重新烘焙字圖。
- 部分標點目前為半形；計畫改為全形中文標點。
- 部分強調字（粗體）目前偏粗。

### 製作資訊

- 文字轉換使用 OpenCC（s2tw）。字型基於 Noto Sans CJK。
- BepInEx 由 BepInEx 團隊開發（LGPL-2.1）。`TCFix`／`TCDiag` 外掛原始碼隨附，可供審閱。

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

### Known limitations (being refined)

- Some characters (e.g. 眾) currently use JP/Simplified glyph shapes; a re-bake from a
  Traditional-Chinese Noto is planned.
- Some punctuation is half-width; full-width CJK punctuation planned.
- Bold weight on some emphasized words is a little heavy.

### Credits

- Text via OpenCC (s2tw). Fonts based on Noto Sans CJK. BepInEx by the BepInEx team
  (LGPL-2.1). Plugin source included for auditing.
