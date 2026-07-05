# Battlesector TC Mod — Nexus Assets Checklist

## Steam Assets URLs

Use these to download official game artwork for Nexus pages:

### Battlesector (App ID: 1295500)

**Headers & Banners:**
```
https://cdn.akamai.steamstatic.com/steam/apps/1295500/header.jpg
https://cdn.akamai.steamstatic.com/steam/apps/1295500/capsule_616x353.jpg
https://cdn.akamai.steamstatic.com/steam/apps/1295500/library_hero.jpg
https://cdn.akamai.steamstatic.com/steam/apps/1295500/library_600x900.jpg
```

**Logo:**
```
https://cdn.akamai.steamstatic.com/steam/apps/1295500/logo.png
```

**Screenshots (examples):**
```
https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/1295500/ss_c221d5d1759ba0778bf334145e3d9cf805057657.1920x1080.jpg
https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/1295500/ss_fd387cf6a17010d7c24a189a2187e41e5723986a.1920x1080.jpg
https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/1295500/ss_fbd361c8f27929d2e1d6fcb3a8846e62b35f2fb8.1920x1080.jpg
```

---

## Required Images for Nexus Mod Page

### 1. **Main Banner** (1920×1080 or 1920×480)
   - [ ] Download library_hero.jpg from Steam
   - [ ] Add text overlay: "繁體中文本地化 | Traditional Chinese Localization"
   - [ ] Use Warhammer 40K font style or gothic font
   - [ ] Save as: `nexus_banner.jpg`

### 2. **Screenshots** (minimum 3, ideally 5-7)
   - [ ] Main menu showing TC text
   - [ ] Unit roster with TC unit names
   - [ ] Mission briefing with TC description
   - [ ] In-game UI with TC tooltips
   - [ ] Campaign/crusade selection screen
   - [ ] Settings/language menu showing selection
   - [ ] (Optional) Before/After SC vs TC comparison

### 3. **Thumbnail** (256×256)
   - [ ] Crop Blood Angels icon or game logo
   - [ ] Add "TC" badge overlay
   - [ ] Save as: `nexus_thumbnail.png`

### 4. **Vortex Extension Icon** (already exists)
   - [x] `gameart.png` (640×360) — already included in extension

---

## Screenshot Capture Guide

### In-Game Screenshot Locations

1. **Launch Battlesector with the TC mod installed**
2. **Navigate to Settings → Language** and select **Chinese (Simplified)**
3. **Capture screenshots with F12 (Steam) or Windows+PrintScreen**
4. **Find screenshots:**
   - Steam: `C:\Program Files (x86)\Steam\userdata\<USER_ID>\760\remote\1295500\screenshots\`
   - Windows: `%USERPROFILE%\Videos\Captures\` or `%USERPROFILE%\Pictures\Screenshots\`

### Recommended Screenshot Locations

| # | Location | What to Show |
|---|----------|--------------|
| 1 | Main Menu | "開始戰役" "多人遊戲" buttons in TC |
| 2 | Campaign Select | Mission titles and descriptions in TC |
| 3 | Unit Roster | Unit names like "星際戰士" "終結者" in TC |
| 4 | Mission Briefing | Full TC paragraph text |
| 5 | In-Game UI | Action tooltips and status text in TC |
| 6 | Settings Menu | Language selection showing "Chinese (Simplified)" |

---

## Image Editing Tools (Optional)

- **GIMP** (free) — `sudo apt install gimp` or download from gimp.org
- **Krita** (free) — `sudo apt install krita` or krita.org
- **ImageMagick** — `sudo apt install imagemagick` (CLI tool for batch processing)
- **Online tools:**
  - Photopea (photopea.com) — web-based Photoshop alternative
  - Canva (canva.com) — easy banner creation

---

## Quick Banner Creation with ImageMagick

```bash
# Download Steam hero image
wget -O steam_hero.jpg "https://cdn.akamai.steamstatic.com/steam/apps/1295500/library_hero.jpg"

# Add text overlay
convert steam_hero.jpg \
  -gravity center \
  -pointsize 72 \
  -fill white \
  -stroke black \
  -strokewidth 2 \
  -annotate +0+50 "繁體中文本地化" \
  -pointsize 48 \
  -annotate +0+120 "Traditional Chinese Localization" \
  nexus_banner.jpg
```

---

## Assets Checklist

### TC Mod Page
- [ ] Banner image (1920×1080)
- [ ] Thumbnail (256×256)
- [ ] Screenshot 1: Main menu
- [ ] Screenshot 2: Campaign select
- [ ] Screenshot 3: Unit roster
- [ ] Screenshot 4: Mission briefing
- [ ] Screenshot 5: In-game UI
- [ ] Screenshot 6 (optional): Settings
- [ ] Screenshot 7 (optional): SC vs TC comparison

### Vortex Extension Page
- [x] gameart.png (640×360) — already included
- [ ] Optional: Screenshot of Vortex with extension enabled
- [ ] Optional: Screenshot of mod deployed in Vortex

---

## Notes

- All screenshots should be **1920×1080** or higher resolution
- Compress images before upload (use tinypng.com or similar)
- Keep file sizes under 2MB per image
- Use descriptive filenames (e.g., `battlesector_tc_main_menu.jpg`)
- Nexus accepts JPG, PNG, GIF, and WebP formats
