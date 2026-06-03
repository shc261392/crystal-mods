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

The Vortex game extension is hosted on Nexus Mods, not the main mod page, and is currently under Vortex review. For now, users install it by dragging the zip onto Vortex's Extensions tab and clicking *Enable*.

### Steps

1. Go to <https://www.nexusmods.com/site/mods/1934>
2. Confirm that `vortex-ext-game-warhammer40kdawnofwar-v1.0.2.zip` is attached
3. Tell users to install the extension from Nexus Mods, then enable it in Vortex before installing the mod archive.

4. Link to it from the Nexus mod description (link is already in the BBCode below)

To rebuild the extension zip: `make package-ext`

---

## 3 — Nexus Page Content

### Title

```
Unofficial Traditional Chinese Patch
```

### Summary (one-liner shown on mod card)

```
Unofficial Traditional Chinese patch for DoW DE — fonts, subtitle artifact, and text corrections. | 非官方繁體中文補丁：字型、字幕殘字與文字校正。
```

### Description (Markdown — paste into the Nexus description editor)

---

# 非官方繁體中文補丁

《戰鎚40,000：破曉之戰 決定版》非官方繁體中文補丁，修正字型、字幕殘字與文字校正。

---

## 修正內容

- **字型大小** — 修正高解析度下字體過小的問題，繁中不再截斷或溢出。
- **字重** — 主選單改用較細字重。
- **字幕殘字** — 修正《冬襲》字幕尾端多出的「緝」。
- **文字校正** — 修正標點、錯字與句末標記。
- **高哥德語重譯** — 99 則帝國金句重譯為更莊嚴的高哥德語風格，並修正幾處嚴重誤譯。
  - 死亡為汝之羅盤 → 死亡乃汝之羅盤
  - 令帝皇的旨意成為你的火炬，破除眼前的陰影 → 以帝皇之旨為炬，焚盡眼前陰影
  - 祈禱淨化靈魂，而痛苦則淨化身體 → 祈禱淨化靈魂，痛苦淬鍊肉身
- **名詞表統一** — 採用中文圈常用譯名：
  - 猿人 → 歐格林（Ogryn）
  - 政戰官 / 政戰軍官 → 政委；政戰處 / 政戰部 → 政委部（Commissar / Commissariat）
  - 神靈族 → 艾達靈族（Eldar）；暗黑神靈族 → 暗黑靈族（Dark Eldar）
- **WAAAGH!** — 歐克戰吼改以原文 WAAAGH 呈現。
- **中文引號** — ASCII 半形 "..." 轉為 「...」，嵌套用 『...』。

---

## 相容性

本模組只修改 `Engine\Locale\Chinese\` 資料夾內的檔案；不碰同路徑的模組理論上都可相容。

若發現衝突，歡迎在下方**留言區**告知。

---

## 如何找到遊戲資料夾

在 Steam 的遊戲庫中，對《破曉之戰 決定版》**點右鍵 → 管理 → 瀏覽本機檔案**。

常見安裝路徑：
- `C:\Program Files (x86)\Steam\steamapps\common\Dawn of War Definitive Edition\`
- `D:\SteamLibrary\steamapps\common\Dawn of War Definitive Edition\`

---

## 安裝方式

### 手動安裝（Windows）

1. 從本頁面下載模組壓縮檔。
2. 解壓到 `Engine\Locale\Chinese\`。
3. 將 `EnginLoc.sga` 重新命名為 `EnginLoc.sga.disabled`。
4. 啟動遊戲即可。

**解除安裝：**
1. 回到遊戲的 `Engine\Locale\Chinese\` 資料夾。
2. 刪除 `data\` 資料夾以及 `Engine.ucs`。
3. 將 `EnginLoc.sga.disabled` 改回 `EnginLoc.sga`。

### Vortex Mod Manager

Vortex 支援目前仍在 Vortex 審核中；先從 Nexus Mods 下載擴充套件 zip，拖到 Vortex 的 **Extensions** 分頁並啟用，再安裝主模組。

---

## 已知問題

**首次啟動出現教學提示**
安裝後首次點選「戰役」，遊戲可能詢問「是否要進行教學？」，忽略即可，只會出現一次。

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

- **Font size** — Fixes overly small text at high resolutions. Traditional Chinese characters no longer clip or overflow the UI.
- **Font weight** — Main menu uses lighter fonts. No more bold-on-bold text.
- **Subtitle artifact** — A stray character (緝) at the end of every voiced subtitle in Winter Assault is removed.
- **Text corrections** — Punctuation, typos, and missing sentence endings fixed.
- **High-Gothic litanies** — All 99 Imperial creed lines rewritten in a solemn, semi-classical High-Gothic register, fixing several outright mistranslations.
  - Purity proves nothing. → Purity cannot prove all things.
  - My armour is contempt. → My carapace is disdain itself.
  - For the Emperor we fight. → For the Emperor, until the end of all ends.
- **Glossary consistency** — Adopts the Chinese 40K community's standard renderings:
  - Ogryn: 猿人 → 歐格林
  - Commissar / Commissariat: 政戰官 / 政戰軍官 → 政委；政戰處 / 政戰部 → 政委部
  - Eldar / Dark Eldar: 神靈族 → 艾達靈族；暗黑神靈族 → 暗黑靈族
- **WAAAGH!** — The ork warcry now renders as WAAAGH with A-count matching the original tildes for emphasis. Unrelated 吼 compounds (戰場怒吼, 戰吼, 吼聲, etc.) are preserved.
- **Chinese quotation marks** — ASCII "..." is converted to Chinese corner brackets 「...」 (with 『...』 for nested cases).

---

## Compatibility

This mod only changes files inside `Engine\Locale\Chinese\`. It should be compatible with any mod that doesn't touch those files.

If you find a conflict with another mod, leave a note in the **comments** below.

---

## How to Find Your Game Folder

In Steam, right-click **Dawn of War Definitive Edition** → **Manage** → **Browse local files**.

Common paths:
- `C:\Program Files (x86)\Steam\steamapps\common\Dawn of War Definitive Edition\`
- `D:\SteamLibrary\steamapps\common\Dawn of War Definitive Edition\`

---

## How to Install

### Manual (Windows)

1. Download the mod zip from this page.
2. Open `Engine\Locale\Chinese\` in your game folder and extract the zip there.
3. Rename `EnginLoc.sga` to `EnginLoc.sga.disabled`.
4. Start the game. Done!

**To uninstall:**
1. Go to your game's `Engine\Locale\Chinese\` folder.
2. Delete the `data\` folder and `Engine.ucs` (the files from this mod).
3. Rename `EnginLoc.sga.disabled` back to `EnginLoc.sga`.

### Vortex Mod Manager

Vortex support currently requires the DoW DE game extension to be installed manually first. Download `vortex-ext-game-warhammer40kdawnofwar-v1.0.2.zip` from Nexus Mods, drag it onto Vortex's **Extensions** tab, and click *Enable*. Then enable **Warhammer 40,000: Dawn of War - Definitive Edition** and install the mod archive.

---

## Known Issues

**Tutorial prompt on first launch**
After installing, the game may ask "Do you want to play the tutorial?" when you click Campaign. Just dismiss it — this only happens once.

---

## Changelog

### v1.0.2 — 2026-05-28

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
