# Nexus Mods Publishing Guide

This document contains everything needed to publish this mod on Nexus Mods.  
Copy each section into the corresponding Nexus Mods field.

---

## 1 — Upload the Mod File

### What to upload

| File | Where to get it |
|------|----------------|
| `wh40k-dow-de-tc-mod-v1.0.2.zip` | Run `make package` → `.copilot_workspace/dist/` |

**Do NOT upload the Vortex extension zip to Nexus** — that goes separately (see Section 2).

### Steps

1. Go to <https://www.nexusmods.com/warhammerdawnofwardefinitiveedition>
2. Log in → click **Upload a mod**
3. Fill in the fields using the content below
4. Under **Files**, click **Add file** → upload `wh40k-dow-de-tc-mod-v1.0.2.zip`
   - File name: `wh40k-dow-de-tc-mod-v1.0.2`
   - Version: `1.0.2`
   - Description: `Main mod archive — unofficial TC patch (fonts, art, sound, Engine.ucs)`
5. Publish the mod
6. Note the mod ID from the URL (e.g. `.../mods/42` → ID is `42`)
7. Update `mod/info.json` with the real mod ID

---

## 2 — Upload the Vortex Extension

The Vortex game extension is hosted on GitHub Releases, not Nexus Mods.  
Users install it by dragging the zip onto Vortex's Extensions tab.

### Steps

1. Go to <https://github.com/shc261392/wh40k-dow-de-tc-mod/releases/latest>
2. Confirm that `vortex-ext-game-warhammer40kdawnofwar-v1.0.2.zip` is attached
3. Link to it from the Nexus mod description (link is already in the BBCode below)

To rebuild the extension zip: `make package-ext`

---

## 3 — Nexus Page Content

### Title

```
Unofficial Traditional Chinese Patch
```

### Summary (one-liner shown on mod card)

```
Unofficial Traditional Chinese patch for DoW DE — fixes fonts, subtitle artifact, and text corrections. | 非官方繁體中文補丁，修正字型、字幕殘字及文字校正。
```

### Description (Markdown — paste into the Nexus description editor)

---

# 非官方繁體中文補丁

《戰鎚40,000：破曉之戰 決定版》非官方繁體中文補丁，修正字型、字幕殘字問題並校正文字內容。

---

## 修正內容

- **字型大小** — 修正全部 13 個字型設定檔，繁體中文字形不再被截斷或溢出介面。
- **字重** — 主選單改用較細字重，消除雙重加粗現象。
- **字幕殘字** — 修正《冬襲》劇情語音字幕末尾出現多餘「緝」字的問題。
- **文字校正** — 修正標點符號、錯字及缺少句末標記等問題。
- **高哥德語重譯（v1.0.2 新增）** — 99 則帝國金句重譯為文白交雜的高哥德語風格，並修正幾處嚴重誤譯（如 31016 Innocence、「殺戮變種人」、「我的盔甲已蒙羞」、「他的目標已達成」等）。
- **名詞表統一（v1.0.2 新增）** — 採用中文圈 40K 慣用譯名：
  - `猿人` → `歐格林`（Ogryn）
  - `政戰官` / `政戰軍官` → `政委`；`政戰處` / `政戰部` → `政委部`（Commissar / Commissariat）
  - `神靈族` → `艾達靈族`（Eldar）；`暗黑神靈族` → `暗黑靈族`（Dark Eldar）
- **WAAAGH!（v1.0.2 新增）** — 歐克戰吼改以原文 `WAAAGH` 呈現，A 的數量依原來「吼～」長度對應；保留 `戰場怒吼`、`戰吼`、`吼聲` 等一般詞未變。
- **中文引號（v1.0.2 新增）** — ASCII 半形 `"..."` 轉換為中文角括號 `「...」`（嵌套時用 `『...』`）。

---

## 相容性

本模組只修改 `Engine\Locale\Chinese\` 資料夾內的檔案。凡是不修改相同路徑的模組，理論上皆可與本模組相容。目前尚未進行正式的相容性測試。

若您發現與其他模組的衝突，歡迎在下方**留言區**告知。

---

## 如何找到遊戲資料夾

在 Steam 的遊戲庫中，對《破曉之戰 決定版》**點右鍵 → 管理 → 瀏覽本機檔案**，即可開啟遊戲根目錄。

常見安裝路徑：
- `C:\Program Files (x86)\Steam\steamapps\common\Dawn of War Definitive Edition\`
- `D:\SteamLibrary\steamapps\common\Dawn of War Definitive Edition\`

---

## 安裝方式

### 手動安裝（Windows）

1. 從本頁面下載模組壓縮檔。
2. 使用上方說明找到遊戲根目錄，進入 `Engine\Locale\Chinese\` 子資料夾，將壓縮檔解壓縮至此處。
3. 在同一個資料夾內，找到 `EnginLoc.sga`，將它**重新命名**為 `EnginLoc.sga.disabled`。
4. 啟動遊戲，完成！

**解除安裝：**
1. 回到遊戲的 `Engine\Locale\Chinese\` 資料夾。
2. 刪除 `data\` 資料夾以及 `Engine.ucs`（本模組的檔案）。
3. 將 `EnginLoc.sga.disabled` 重新命名回 `EnginLoc.sga`。

### Vortex Mod Manager

Vortex 支援需要手動安裝遊戲擴充套件，待擴充套件正式列入 Vortex 名單後，步驟將更簡單，屆時說明會一併更新。

目前請使用上方的手動安裝方式。

---

## 已知問題

**首次啟動出現教學提示**
安裝後首次點選「戰役」，遊戲可能詢問「是否要進行教學？」，忽略即可，只會出現一次。

**戰役進度**
本模組**不會**修改任何存檔或戰役進度，可安心安裝與解除安裝。

---

## 問題與回饋

有任何問題或發現錯誤？請在本頁面的**留言區**留言。

*（原始碼：[github.com/shc261392/wh40k-dow-de-tc-mod](https://github.com/shc261392/wh40k-dow-de-tc-mod)）*

---
---

# Unofficial Traditional Chinese Patch

Unofficial Traditional Chinese patch for Warhammer 40,000: Dawn of War – Definitive Edition.

---

## What This Mod Fixes

- **Font size** — All 13 font files corrected. Traditional Chinese characters no longer clip or overflow the UI.
- **Font weight** — Main menu uses lighter fonts. No more bold-on-bold text.
- **Subtitle artifact** — A stray character (緝) at the end of every voiced subtitle in Winter Assault is removed.
- **Text corrections** — Punctuation, typos, and missing sentence endings fixed.
- **High-Gothic litanies (new in v1.0.2)** — All 99 Imperial creed lines rewritten in a solemn, semi-classical High-Gothic register, fixing several outright mistranslations (Innocence proves nothing; Know/kill the mutant; My armour is contempt; His will be done; etc.).
- **Glossary consistency (new in v1.0.2)** — Adopts the Chinese 40K community's standard renderings:
  - Ogryn: `猿人` → `歐格林`
  - Commissar / Commissariat: `政戰官` / `政戰軍官` → `政委`; `政戰處` / `政戰部` → `政委部`
  - Eldar / Dark Eldar: `神靈族` → `艾達靈族`; `暗黑神靈族` → `暗黑靈族`
- **WAAAGH! (new in v1.0.2)** — The ork warcry now renders as `WAAAGH` with A-count matching the original tildes for emphasis. Unrelated `吼` compounds (`戰場怒吼`, `戰吼`, `吼聲`, etc.) are preserved.
- **Chinese quotation marks (new in v1.0.2)** — ASCII `"..."` is converted to Chinese corner brackets `「...」` (with `『...』` for nested cases).

---

## Compatibility

This mod only changes files inside `Engine\Locale\Chinese\`. It should be compatible with any other mod that doesn't touch those same files. No formal compatibility testing has been done.

If you find a conflict with another mod, let me know in the **comments** below.

---

## How to Find Your Game Folder

In Steam, right-click **Dawn of War Definitive Edition** → **Manage** → **Browse local files** to open the game folder.

Common paths:
- `C:\Program Files (x86)\Steam\steamapps\common\Dawn of War Definitive Edition\`
- `D:\SteamLibrary\steamapps\common\Dawn of War Definitive Edition\`

---

## How to Install

### Manual (Windows)

1. Download the mod zip from this page.
2. Find your game folder using the steps above, then open the `Engine\Locale\Chinese\` subfolder. Extract the mod zip there.
3. In that same folder, **rename** `EnginLoc.sga` to `EnginLoc.sga.disabled`.
4. Start the game. Done!

**To uninstall:**
1. Go to your game's `Engine\Locale\Chinese\` folder.
2. Delete the `data\` folder and `Engine.ucs` (the files from this mod).
3. Rename `EnginLoc.sga.disabled` back to `EnginLoc.sga`.

### Vortex Mod Manager

Vortex support requires a game extension that currently needs to be set up manually.
Once the extension is officially listed in Vortex, setup will be much simpler — instructions will be updated then.

For now, use the manual install above.

---

## Known Issues

**Tutorial prompt on first launch**
After installing, the game may ask "Do you want to play the tutorial?" when you click Campaign. Just dismiss it — this only happens once.

**Campaign progress**
This mod does **not** touch any save files or campaign progress. You can install and uninstall safely.

---

## Changelog

### v1.0.2 — 2026-05-28

**Translation overhaul (zh-TW):**
- Rewrote 99 Imperial litanies (IDs 31000–31100 and scattered duplicates) in a High-Gothic / semi-classical register; fixed several severe mistranslations.
- Glossary unification: `猿人` → `歐格林` (Ogryn); `政戰官` / `政戰軍官` / `政戰處` / `政戰部` → `政委` / `政委部` (Commissar / Commissariat); `神靈族` → `艾達靈族` (Eldar); `暗黑神靈族` → `暗黑靈族` (Dark Eldar).
- WAAAGH! variants (`吼` / `吼吼！` / `吼～` / `吼~~~~！`, etc.) standardised to `WAAAGH` with A-count proportional to original tilde length. Non-warcry `吼` compounds left untouched.
- ASCII straight quotes `"..."` converted to Chinese corner brackets `「...」` (nested → `『...』`); 5 odd-quote edge cases repaired.

See `docs/glossary-zh.md` in the repo for the full glossary and conversion rules.

### v1.0.1

- Initial font, subtitle artifact, and round-1 punctuation/typo corrections.

---

## Questions & Support

Have a question or found an issue? Post in the **comments** on this page.

*(Source: [github.com/shc261392/wh40k-dow-de-tc-mod](https://github.com/shc261392/wh40k-dow-de-tc-mod))*

---

## 4 — After Publishing

Once the mod is live, update `mod/info.json` with the real mod ID:

1. Find the mod ID in the Nexus URL, e.g.:  
   `https://www.nexusmods.com/warhammerdawnofwardefinitiveedition/mods/42` → ID is `42`

2. Edit `mod/info.json`:
   ```json
   "nexusMods": {
     "modId": 42,
     ...
   },
   "source": {
     ...
     "nexusMods": "https://www.nexusmods.com/warhammerdawnofwardefinitiveedition/mods/42"
   }
   ```

3. Commit and push:
   ```bash
   git add mod/info.json
   git commit -m "chore(mod): set Nexus Mods ID to 42"
   git push
   ```
