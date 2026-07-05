# Nexus Mods Publishing Guide — Battlesector TC Localization

This document contains everything needed to publish this mod on Nexus Mods.  
Copy each section into the corresponding Nexus Mods field.

---

## 1 — Upload the Vortex Extension

### What to upload

| File | Where to get it |
|------|----------------|
| `game-warhammer40kbattlesector-0.1.0.zip` | `warhammer-40k-battlesector/dist/` |

### Steps

1. Go to <https://www.nexusmods.com/site/mods>
2. Log in → click **Upload a mod** → select **Vortex Extension**
3. Fill in fields using the content from **Section 4** below
4. Upload `game-warhammer40kbattlesector-0.1.0.zip`
   - File name: `Warhammer 40K Battlesector Support`
   - Version: `0.1.0`
   - Description: `Vortex game extension for automatic mod management`
5. Publish the extension
6. Note the extension URL (e.g. `.../site/mods/XXXX`)
7. Update the mod page to link to this extension

---

## 2 — Upload the TC Mod

### What to upload

| File | Where to get it |
|------|----------------|
| `wh40k-battlesector-tc-localization-v0.1.0.zip` | `warhammer-40k-battlesector/dist/` |

### Steps

1. Go to <https://www.nexusmods.com/warhammer40kbattlesector>
2. Log in → click **Upload a mod**
3. Fill in the fields using the content below (**Section 3**)
4. Under **Files**, click **Add file** → upload `wh40k-battlesector-tc-localization-v0.1.0.zip`
   - File name: `Traditional Chinese Localization`
   - Version: `0.1.0`
   - Description: `Main mod archive — Traditional Chinese localization with full font support`
5. Upload screenshots (see **Section 5**)
6. Publish the mod
7. Note the mod ID from the URL (e.g. `.../mods/42` → ID is `42`)
8. Update `modinfo.json` with the real mod ID

---

## 3 — TC Mod Nexus Page Content

### Title

```
Traditional Chinese Localization
```

### Summary (one-liner shown on mod card)

```
Community Traditional Chinese (繁體中文) localization with full font support — 4,524+ strings converted SC→TC with pre-baked glyphs. | 社群繁體中文本地化，完整字型支援。
```

### Category

`Localization / Translations`

### Tags

`Traditional Chinese`, `繁體中文`, `Localization`, `Translation`, `Font`, `UI`, `Chinese`

### Description (BBCode — paste into the Nexus description editor)

```bbcode
[center][size=6][b]Warhammer 40,000: Battlesector[/b][/size]
[size=5]Traditional Chinese Localization / 繁體中文本地化[/size]
[img]https://i.imgur.com/PLACEHOLDER.jpg[/img][/center]

[line]

[size=4][b]繁體中文本地化模組[/b][/size]

《戰鎚40,000：戰區》社群繁體中文本地化，修正字型、完整支援繁體中文字符。

[size=3][b]特色功能[/b][/size]
[list]
[*][b]4,524+ 條 UI 文字[/b] — 簡體轉繁體（OpenCC s2twp 轉換）
[*][b]完整字型支援[/b] — 2,555+ 繁體字符預先烘焙至遊戲字型
[*][b]選單、任務、單位、對話[/b] — 全面本地化
[*][b]無需外部載入器[/b] — 直接修補遊戲資源檔案
[*][b]Vortex 相容[/b] — 一鍵安裝，自動備份原始檔案
[/list]

[size=3][b]已知限制[/b][/size]
[list]
[*]戰役 / 遠征描述文字可能出現缺字（□ 方塊），約影響 ~100 個字符
[*]這是 TextMesh Pro 字型回退鏈的技術限制，選單、任務、單位名稱均正常顯示
[/list]

[line]

[size=4][b]Traditional Chinese Localization Mod[/b][/size]

Community Traditional Chinese (繁體中文) localization for [b]Warhammer 40,000: Battlesector[/b] (Black Lab Games / Slitherine).

[size=3][b]Features[/b][/size]
[list]
[*][b]4,524+ UI strings[/b] converted Simplified → Traditional Chinese (OpenCC)
[*][b]Full font support[/b] with 2,555+ TC glyphs baked into game fonts
[*][b]Menu, missions, units, barks[/b] — fully localized
[*][b]No external mod loader[/b] — patches game assets directly
[*][b]Vortex-compatible[/b] — one-click install with automatic backup
[/list]

[size=3][b]Known Limitations[/b][/size]
[list]
[*]Campaign/crusade description text may show tofu boxes (□) for ~100 characters
[*]This is a technical limitation in TextMesh Pro's fallback chain; all menu, mission, and unit text renders correctly
[/list]

[line]

[size=4][b]Installation / 安裝方式[/b][/size]

[size=3][b]Option A: Vortex Mod Manager (Recommended / 推薦)[/b][/size]

[b]1. Install the Vortex extension[/b] [i](first time only / 首次安裝)[/i]
[list]
[*]Download from [url=https://www.nexusmods.com/site/mods/XXXX]Nexus Mods[/url]
[*]Drag onto [b]Vortex Extensions[/b] tab → [b]Enable[/b] → [b]Restart Vortex[/b]
[/list]

[b]2. Install this mod[/b]
[list]
[*]Download this mod zip
[*]Drag onto [b]Vortex Mods[/b] tab
[*]Click [b]Install[/b] → [b]Enable[/b]
[/list]

[b]3. Deploy[/b]
[list]
[*]Click [b]Deploy Mods[/b]
[*]Vortex automatically backs up original files to [font=Courier New].zh-tw-mod-backup/[/font]
[/list]

[b]4. Launch the game[/b]
[list]
[*]In-game: [b]Settings[/b] → [b]Language[/b] → [b]Chinese (Simplified)[/b]
[*]Traditional Chinese text will display
[/list]

[b]To uninstall:[/b] Click [b]Purge Mods[/b] in Vortex. Original files are restored from backup.

[line]

[size=3][b]Option B: Manual Install / 手動安裝[/b][/size]

[color=#ff0000][b]⚠️ Manual installation requires careful file placement. Vortex is strongly recommended.[/b][/color]

[b]1. Locate game folder / 找到遊戲資料夾[/b]
[list]
[*]Steam: Right-click game → [b]Manage[/b] → [b]Browse local files[/b]
[*]Example: [font=Courier New]C:\Program Files (x86)\Steam\steamapps\common\Warhammer 40K Battlesector\[/font]
[/list]

[b]2. Backup original files / 備份原始檔案[/b]
[code]
Warhammer 40K Battlesector_Data/sharedassets1.assets
Warhammer 40K Battlesector_Data/StreamingAssets/aa/unknownassets_assets_all_*.bundle
Warhammer 40K Battlesector_Data/StreamingAssets/aa/catalog.bin
Warhammer 40K Battlesector_Data/StreamingAssets/aa/catalog.hash
[/code]

[b]3. Extract and copy files from this zip:[/b]
[list]
[*][font=Courier New]sharedassets1.assets[/font] → [font=Courier New]Warhammer 40K Battlesector_Data/[/font]
[*][font=Courier New]unknownassets_assets_all_*.bundle[/font] → [font=Courier New]Warhammer 40K Battlesector_Data/StreamingAssets/aa/StandaloneWindows64/[/font]
[*][font=Courier New]catalog.bin[/font] → [font=Courier New]Warhammer 40K Battlesector_Data/StreamingAssets/aa/[/font]
[*][font=Courier New]catalog.hash[/font] → [font=Courier New]Warhammer 40K Battlesector_Data/StreamingAssets/aa/[/font]
[/list]

[b]4. Launch game[/b] → Select [b]Chinese (Simplified)[/b] in language settings

[b]To uninstall:[/b] Restore backed-up files or [b]Verify Integrity of Game Files[/b] in Steam.

[line]

[size=4][b]How It Works / 原理說明[/b][/size]

This mod directly patches the game's Unity asset files:
[list]
[*][b]sharedassets1.assets[/b] — Replaces Simplified Chinese strings with Traditional Chinese
[*][b]Font bundle[/b] — Pre-baked TC glyphs into TextMesh Pro font atlases
[*][b]Catalog files[/b] — Updated asset hashes and CRC32 checksums
[/list]

Traditional Chinese text replaces the Simplified Chinese slot. In-game, selecting [b]Chinese (Simplified)[/b] displays Traditional Chinese.

[line]

[size=4][b]Technical Details / 技術細節[/b][/size]

[list]
[*][b]Conversion:[/b] OpenCC [font=Courier New]s2twp[/font] (Simplified → Traditional with Taiwan variants)
[*][b]Strings processed:[/b] 4,524 entries (barks, missions, UI, units)
[*][b]Font patching:[/b]
  [list]
  [*]Futura font: 2,555 TC glyphs baked into 2048×8704 atlas
  [*]NotoSansCJKjp fallback: 3,798 TC glyphs pre-baked
  [/list]
[*][b]Asset integrity:[/b] CRC32/MD5 checksums updated for game validation
[/list]

[line]

[size=4][b]Requirements / 系統需求[/b][/size]

[list]
[*][b]Warhammer 40,000: Battlesector[/b] (Steam / GOG) — Version 1.3.0+
[*][b]For Vortex install:[/b] [url=https://www.nexusmods.com/about/vortex/]Vortex Mod Manager[/url] with Battlesector extension
[*][b]For manual install:[/b] Basic file management skills, admin/write access to game folder
[/list]

[line]

[size=4][b]Support & Issues / 支援與問題[/b][/size]

[list]
[*][b]GitHub Issues:[/b] [url=https://github.com/shc261392/crystal-mods/issues]crystal-mods/issues[/url]
[*][b]Nexus Comments:[/b] Post below
[/list]

When reporting issues, include:
[list]
[*]Game version
[*]Installation method (Vortex / manual)
[*]Screenshots of the issue
[*][font=Courier New]Player.log[/font] from [font=Courier New]%APPDATA%\..\LocalLow\Black Lab Games\Warhammer 40K Battlesector\[/font]
[/list]

[line]

[size=4][b]Credits / 致謝[/b][/size]

[list]
[*][b]Localization:[/b] Community effort
[*][b]OpenCC:[/b] BYVoid ([url=https://github.com/BYVoid/OpenCC]GitHub[/url])
[*][b]UnityPy:[/b] K0lb3 ([url=https://github.com/K0lb3/UnityPy]GitHub[/url])
[*][b]Noto Sans CJK:[/b] Google Fonts ([url=https://github.com/googlefonts/noto-cjk]GitHub[/url])
[/list]

[line]

[center][size=2][b]Warhammer 40,000[/b] and all associated trademarks are property of Games Workshop Limited.
This is an unofficial community mod. Not affiliated with Games Workshop, Black Lab Games, or Slitherine.[/size][/center]
```

---

## 4 — Vortex Extension Nexus Page Content

### Title

```
Warhammer 40,000: Battlesector Support
```

### Summary

```
Vortex game extension for Warhammer 40,000: Battlesector — adds automatic mod detection, deployment, and backup management to Vortex.
```

### Category

`Vortex Extension`

### Description (BBCode)

```bbcode
[size=5][b]Warhammer 40,000: Battlesector — Vortex Support Extension[/b][/size]

Adds full mod management support for [b]Warhammer 40,000: Battlesector[/b] (Steam App ID 1295500) to Vortex Mod Manager.

[line]

[size=4][b]Features[/b][/size]

[size=3][b]Game Detection[/b][/size]
Automatically discovers the game installation via Steam (App ID [font=Courier New]1295500[/font]) and GOG, registering the game for mod management.

[size=3][b]Asset Replacement Mod Installer[/b][/size]
Handles Unity asset replacement mods: localization packs, asset bundles, catalog files, and loose-file mods.

[b]Deployment[/b] — files are deployed to their full paths relative to the game root:
[list]
[*][font=Courier New]sharedassets1.assets[/font] → [font=Courier New]Warhammer 40K Battlesector_Data/sharedassets1.assets[/font]
[*][font=Courier New]unknownassets_*.bundle[/font] → [font=Courier New]Warhammer 40K Battlesector_Data/StreamingAssets/aa/StandaloneWindows64/[/font]
[*][font=Courier New]catalog.bin[/font] → [font=Courier New]Warhammer 40K Battlesector_Data/StreamingAssets/aa/[/font]
[/list]

[b]Archive layouts supported:[/b]
[list]
[*][b]Full path present:[/b] [font=Courier New]sharedassets1.assets[/font] → deployed to game root as-is
[*][b]Single wrapper folder:[/b] [font=Courier New]wh40k-battlesector-tc-v0.1.0/sharedassets1.assets[/font] → wrapper stripped automatically
[/list]

[size=3][b]File Management[/b][/size]
The extension lets Vortex's staging system handle file deployment and restoration natively. When a user uninstalls a mod, Vortex automatically restores the previous game state without manual backup management.

[line]

[size=4][b]Installation[/b][/size]

[b]1.[/b] Download [font=Courier New]game-warhammer40kbattlesector-{version}.zip[/font] from this page
[b]2.[/b] Open Vortex → [b]Extensions[/b] tab
[b]3.[/b] Drag the zip onto the Extensions window
[b]4.[/b] Click [b]Enable[/b]
[b]5.[/b] Restart Vortex
[b]6.[/b] Vortex will now detect Battlesector and allow mod installation

[line]

[size=4][b]Compatible Mods[/b][/size]

[list]
[*][url=https://www.nexusmods.com/warhammer40kbattlesector/mods/XXX]Traditional Chinese Localization[/url]
[*]Any asset replacement mod for Battlesector
[/list]

[line]

[size=4][b]Source Code[/b][/size]

[url=https://github.com/shc261392/crystal-mods/tree/main/warhammer-40k-battlesector/vortex-ext/game-warhammer40kbattlesector]GitHub Repository[/url]

[line]

[size=4][b]Support[/b][/size]

[list]
[*][b]Issues:[/b] [url=https://github.com/shc261392/crystal-mods/issues]GitHub Issues[/url]
[*][b]Vortex Documentation:[/b] [url=https://wiki.nexusmods.com/index.php/Vortex]Vortex Wiki[/url]
[/list]

[line]

[center][size=2]Developed by shadowevor | MIT License
[b]Warhammer 40,000[/b] is a trademark of Games Workshop Limited.[/size][/center]
```

---

## 5 — Required Assets

### Images to prepare:

1. **Banner / Hero Image** (1920×1080 recommended)
   - Game logo with "Traditional Chinese Localization" subtitle
   - Use official Battlesector key art as background

2. **Screenshots** (at least 3-5):
   - Main menu with TC text
   - Mission briefing screen with TC text
   - Unit roster with TC names
   - In-game UI showing TC tooltips
   - Before/After comparison (if possible)

3. **Thumbnail** (256×256)
   - Small icon version of the banner

### Where to get game assets:

- **Steam header:** `https://cdn.akamai.steamstatic.com/steam/apps/1295500/header.jpg`
- **Capsule:** `https://cdn.akamai.steamstatic.com/steam/apps/1295500/capsule_616x353.jpg`
- **Library hero:** `https://cdn.akamai.steamstatic.com/steam/apps/1295500/library_hero.jpg`
- **Screenshots:** Available from Steam store page

For Vortex extension:
- Use the `gameart.png` (Blood Angels chapter icon or game logo)

---

## 6 — Checklist Before Publishing

- [ ] Mod zip tested with Vortex
- [ ] Mod zip tested with manual install
- [ ] README.md included in zip
- [ ] modinfo.json included in zip
- [ ] Screenshots captured (at least 3)
- [ ] Banner image prepared
- [ ] Vortex extension tested and works
- [ ] All links updated with real URLs
- [ ] Version numbers match across all files
- [ ] Changelog prepared for future updates

---

## 7 — Post-Publishing Tasks

1. Update `modinfo.json` with real Nexus mod ID
2. Update GitHub README with Nexus links
3. Create GitHub release with same version
4. Link Vortex extension page from mod page
5. Link mod page from Vortex extension page
6. Monitor comments section for bug reports
7. Prepare v0.1.1 with tofu box improvements (if possible)
