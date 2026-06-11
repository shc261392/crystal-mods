# Black Book TC Mod — Complete Build & Deployment Guide

**Complete workflow**: Extract → Convert → Validate → Package → Deploy → Publish

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Step 1: Extract Game Strings](#step-1-extract-game-strings)
3. [Step 2: Convert SC→TC (if needed)](#step-2-convert-sctc-if-needed)
4. [Step 3: Validate Quality](#step-3-validate-quality)
5. [Step 4: Package Mod](#step-4-package-mod)
6. [Step 5: Deploy & Test](#step-5-deploy--test)
7. [Step 6: Publish](#step-6-publish)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **Python 3.7+** (check with `python3 --version`)
- **Black Book** installed in Steam
- **pnpm** (if using workspace scripts)
- **Git** (for version control)

### Python Dependencies

Install required packages:

```bash
# From the mod directory
pip install UnityPy opencc

# Verify installation
python3 -c "import UnityPy; import opencc; print('✓ All dependencies installed')"
```

### Project Structure

Make sure you're in the mod directory:

```bash
cd /home/shado/crystal-mods/black-book/tc-localization
ls -la  # Should show: deploy.sh, Makefile, scripts/, payload/, etc.
```

---

## Step 1: Extract Game Strings

### What This Does

Scans Black Book's Unity assets and extracts all UI/dialogue strings into a plain text file.

**Smart auto-detection handles**:
- Windows (native & WSL2 mounts)
- Linux (native Steam)
- Multiple Steam library folders

### Run Extraction

```bash
cd /home/shado/crystal-mods/black-book/tc-localization

# Method 1: Auto-detect (recommended)
python3 scripts/extract_game_strings.py

# Method 2: Specify game path (if auto-detect fails)
python3 scripts/extract_game_strings.py --game-path /path/to/Black\ Book

# Method 3: Custom output file
python3 scripts/extract_game_strings.py --output /tmp/my_strings.txt
```

### What You'll See

```
[*] Searching for Black Book installation...
[✓] Found Black Book at: /mnt/d/SteamLibrary/steamapps/common/Black Book
[*] Scanning game assets in: /mnt/d/SteamLibrary/steamapps/common/Black Book/Black Book_Data
[*] Scanning .resource files...
    resources.resource...
    sharedassets0.resource...
    ...
[*] Scanning StreamingAssets...
[✓] Extraction complete!
    Total unique strings: 1247
    Files scanned: 12
    Output: /home/shado/crystal-mods/black-book/tc-localization/payload/Black Book_Data/resources/strings_extracted.txt
```

### Verify Output

```bash
# Check file size (should be >100 KB)
ls -lh payload/Black\ Book_Data/resources/strings_extracted.txt

# Preview first 20 strings
head -20 payload/Black\ Book_Data/resources/strings_extracted.txt

# Expected format:
# text_4829=Welcome, traveler
# ui_button_1043=Start Game
# npc_dialogue_2951=Goodbye friend
```

### Troubleshooting Extraction

| Issue | Solution |
|-------|----------|
| `No module named 'UnityPy'` | Run: `pip install UnityPy` |
| Can't find Black Book | Manually specify: `--game-path /mnt/d/...` |
| Empty output file | Check if Black Book is actually installed |
| Permission denied | Run: `chmod +x scripts/extract_game_strings.py` |

---

## Step 2: Convert SC→TC (if needed)

### Situation 1: You Have a Simplified Chinese (SC) Source

If you already have an SC translation:

```bash
# Place SC file at:
cp /path/to/SC_translation.txt reference/SC_SOURCE.txt

# Run conversion
python3 scripts/convert_sc_to_tc.py

# Output: payload/Black Book_Data/resources/_Translations.txt
```

### Situation 2: You're Starting from English (No SC)

If you only have English strings (extracted above):

```bash
# Edit the extracted file manually to add your own translations:
nano payload/Black\ Book_Data/resources/strings_extracted.txt

# Or use it as a template for a translation tool (Gemini, ChatGPT, etc.)
```

### Situation 3: Manual Terminology Editing

After conversion, review and edit for game-specific terminology:

```bash
# Open translation file
nano payload/Black\ Book_Data/resources/_Translations.txt

# Reference:
cat reference/TERMINOLOGY.md      # Game-specific terms
cat reference/TC_STANDARDS.md     # Chinese grammar/punctuation rules
```

---

## Step 3: Validate Quality

### Run Quality Gates

```bash
# All three gates
make validate

# Individual gates
python3 scripts/gate1_translation_validator.py  # File structure
python3 scripts/gate2_terminology_validator.py  # Chinese text quality
python3 scripts/gate3_font_validator.py         # Font assets
```

### Expected Output

```
Running quality gates...

[Gate 1] Validating translation file structure...
[*] Translation file size: 245000 bytes
[*] Total lines: 1247
[✓] Translation file structure valid
    Keys: 1247

[Gate 2] Checking for common translation errors...
[*] Validating terminology...
[✓] Terminology validation passed

[Gate 3] Font asset validation...
[!] No .asset font files found in: payload/Fonts/
[✓] Font validation passed (fonts optional for this release)

✓ All validation gates passed
```

### Fix Issues

If validation fails:

```bash
# See details
python3 scripts/gate1_translation_validator.py  # Shows line numbers & issues

# Edit problematic lines
nano payload/Black\ Book_Data/resources/_Translations.txt

# Re-validate
make validate
```

---

## Step 4: Package Mod

### Create Distributable ZIP

```bash
# Build mod package
make build

# Or manual packaging
mkdir -p dist
cd payload
zip -r ../dist/tc-localization-v1.0.0.zip .
cd ..

# Verify package contents
unzip -l dist/tc-localization-v1.0.0.zip | head -20
```

### Package Structure

```
tc-localization-v1.0.0.zip/
├── Black Book_Data/
│   └── resources/
│       └── _Translations.txt
├── Fonts/
│   └── NotoSansTC.asset (optional)
├── modinfo.json
└── (any other mod files)
```

### File Size

Typical sizes:
- Strings only: ~200-300 KB
- With Noto Sans TC font: ~5-8 MB

---

## Step 5: Deploy & Test

### Deploy to Your Game

```bash
# Option A: Vortex (if installed)
# 1. Download vortex-ext-game-black-book-v*.zip
# 2. Drag onto Vortex Extensions tab
# 3. Drag tc-localization-v*.zip onto Vortex Mods tab
# 4. Click "Deploy Mods"

# Option B: Script deployment
bash deploy.sh                              # Linux/WSL2
.\deploy.ps1                                # Windows (PowerShell Admin)

# Option C: Manual deployment
unzip dist/tc-localization-v1.0.0.zip -d /path/to/Black\ Book
```

### Test in Game

1. Launch Black Book from Steam
2. Check if text appears in Traditional Chinese
3. Look for any rendering issues (tofu boxes, corruption)
4. Test multiple game sections (menu, dialogue, items, etc.)

### Collect Feedback

- Screenshot any issues
- Note which strings look wrong
- Check for terminology inconsistencies
- Verify font rendering on different systems

---

## Step 6: Publish

### Step 6a: Create GitHub Release

```bash
# Tag the release
git tag -a v1.0.0 -m "Black Book TC Localization v1.0.0"
git push origin v1.0.0

# Create release on GitHub
# - Upload: dist/tc-localization-v1.0.0.zip
# - Title: "Black Book TC Localization v1.0.0"
# - Description: See README.md
```

### Step 6b: Prepare Nexus Submission

**File 1: TC Localization Mod**
- File: `dist/tc-localization-v1.0.0.zip`
- Name: "Traditional Chinese Localization v1.0.0"
- Category: Translation
- Description: See `README.md`
- Requires: Vortex Extension for Black Book

**File 2: Vortex Extension**
- File: `vortex-ext/dist/vortex-ext-game-black-book-v1.0.0.zip`
- Name: "Black Book (Vortex Extension) v1.0.0"
- Category: Vortex Mod Support
- Description: See `vortex-ext/README.md`
- Install note: "Drag & drop onto Vortex Extensions tab"

### Step 6c: Submit to Nexus

```bash
# Check file list
ls -lh dist/
ls -lh vortex-ext/dist/

# Upload via Nexus Mods website:
# 1. Create game page (if needed)
# 2. Upload files separately
# 3. Add documentation
# 4. Request Vortex review for extension
```

### Step 6d: Create Vortex Review Request

For the Vortex extension, file a review request at:
- [Vortex Nexus Hub](https://www.nexusmods.com/site/mods/)

Include:
- Link to extension file on Nexus
- Brief description of functionality
- Link to extension README

---

## Troubleshooting

### Extraction Issues

**Q: UnityPy fails to read assets**
- A: Some asset formats may not be supported. Try reducing max files scanned.

**Q: Memory error during extraction**
- A: Reduce StreamingAssets scan depth or process in chunks

**Q: No strings extracted**
- A: Check if strings are in compiled game code, not assets. May need alternative approach.

### Conversion Issues

**Q: OpenCC errors during conversion**
- A: Ensure file is valid UTF-8: `file -i strings_extracted.txt`

**Q: Wrong traditional characters**
- A: Use correct OpenCC config: `s2twp.json` (Taiwan with phrases)

### Validation Issues

**Q: Gate 2 fails with "mixed scripts"**
- A: Check for English text mixed with Chinese. Decide: translate or keep English.

**Q: Gate 3 fails for fonts**
- A: Fonts are optional for initial release. Can be added later.

### Deployment Issues

**Q: Text still in English after deployment**
- A: Verify `Black Book_Data/resources/` has asset files. Check file permissions.

**Q: Tofu boxes instead of text**
- A: Font didn't deploy correctly. Verify `Fonts/NotoSansTC.asset` exists and is readable.

**Q: Deploy script can't find game**
- A: Manually specify: `GAME_PATH=/path/to/game bash deploy.sh`

---

## Next: Make & Test Commands

Quick reference:

```bash
# Extract
python3 scripts/extract_game_strings.py

# Convert (if SC source)
python3 scripts/convert_sc_to_tc.py

# Validate
make validate

# Build package
make build

# Deploy
bash deploy.sh

# Uninstall
bash uninstall.sh

# Clean
make clean
```

---

## Resources

- **OpenCC**: https://github.com/BYVoid/OpenCC
- **UnityPy**: https://github.com/K0lb3/UnityPy
- **Noto Sans TC**: https://fonts.google.com/noto/specimen/Noto+Sans+TC
- **Nexus Mods**: https://www.nexusmods.com/
- **Vortex**: https://www.nexusmods.com/about/vortex/

---

**Last updated**: 2026-06-10  
**Status**: Ready for extraction & deployment
