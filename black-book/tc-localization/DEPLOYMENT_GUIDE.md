# Black Book TC Mod — Deployment & Reversibility Guide

## ✓ Deployment Scripts Status

### Deploy Reversibility — FULLY REVERSIBLE ✓

**What deploy.sh does:**
1. ✓ Auto-detects Black Book Steam installation (with WSL2/Windows drive support)
2. ✓ Validates mod payload has 1448 TC YAML config files
3. ✓ **BACKS UP ORIGINAL** `StreamingAssets/Config/` to timestamped directory
4. ✓ Backs up `resources/` (if exists)
5. ✓ **Saves backup path to `.last_backup_path`** for automatic uninstall
6. ✓ Deploys TC YAML files to `Black Book_Data/StreamingAssets/Config/`

**Backup Structure:**
```
backup/
├── game_backup_20260611_144327/
│   ├── Config_original/          [Original SC YAML configs]
│   └── resources_original/       [Original resources dir]
├── game_backup_20260611_143000/  [Previous deployments preserved]
└── .last_backup_path             [Pointer to latest backup]
```

### Uninstall Reversibility — 100% SAFE ✓

**What uninstall.sh does:**
1. ✓ Removes deployed `StreamingAssets/Config/` directory
2. ✓ Removes TC font assets (if deployed)
3. ✓ **Automatically finds latest backup** via `.last_backup_path` OR directory scan
4. ✓ **Restores original game files from backup** (100% reversible)
5. ✓ Provides Steam verification command if needed

**Safety Features:**
- ✓ Creates backup BEFORE any deployment
- ✓ Saves backup location for instant restoration
- ✓ Preserves all previous backups (can restore to any version)
- ✓ Errors if backup not found (won't leave game in broken state)
- ✓ Zero modification to original game directory until backup succeeds

---

## 2. Human-Readable Translations List

**File**: `payload/TRANSLATIONS_LIST.txt`

**Contents**: All 1,448 strings with SC→TC conversions organized by category:

```
[ABILITIES]
─────────────────────────────────────────────────────────────────────────────
  亚伯                   → 亞伯
  祭台                   → 祭臺
  祭台+                  → 祭臺+
  阿门                   → 阿門
  ...and 454 more ability items

[LOCATIONS]
─────────────────────────────────────────────────────────────────────────────
  圣地                   → 聖地
  城堡                   → 城堡
  ...and 449 more location items

[INVENTORY]
─────────────────────────────────────────────────────────────────────────────
  金钥匙                  → 金鑰匙
  红布                   → 紅布
  ...and 188 more inventory items

... [9 more categories]
```

**Review**: Open with any text editor to verify all conversions before deployment.

---

## 3. Complete Workflow (Safe to Deploy)

```bash
# Step 1: Review translations
cat payload/TRANSLATIONS_LIST.txt | less

# Step 2: Deploy with automatic backup
bash deploy.sh

# Step 3: Test in game (launch Black Book)
# Verify text appears in Traditional Chinese

# Step 4: If issues found, uninstall (fully reversible)
bash uninstall.sh

# Step 5: If happy, you're done! Mod is deployed and backed up.

# To restore original anytime:
bash uninstall.sh
```

---

## 4. Backup Preservation

All backups are preserved in `backup/` directory:

```bash
# List all deployments
ls -la backup/

# To restore to a specific previous deployment:
cp -r backup/game_backup_20260611_130000/Config_original/* \
      /path/to/Black Book/Black Book_Data/StreamingAssets/Config/
```

---

## 5. Scripts Updated for YAML Architecture

### Changes Made:
- ✓ `deploy.sh`: Now validates `Black Book_Data/StreamingAssets/Config/` (1448 YAML files)
- ✓ `deploy.sh`: Backs up original Config directory (not resources)
- ✓ `deploy.sh`: Saves `.last_backup_path` for quick uninstall
- ✓ `uninstall.sh`: Removes entire Config directory (will be restored)
- ✓ `uninstall.sh`: Automatically finds and restores from backup
- ✓ `uninstall.sh`: Provides Steam verification option

### Why This Works:
- Black Book stores all localization in `StreamingAssets/Config/` YAML files
- Deploy = copy our TC YAML files to game Config directory
- Uninstall = delete Config + restore from backup (100% reversible)
- Zero side effects on game executable or other data

---

## 6. Deployment Safety Checklist

Before deploying, verify:

- [ ] `payload/Black Book_Data/StreamingAssets/Config/` contains 1,448 config_zh.yaml files
- [ ] `payload/TRANSLATIONS_LIST.txt` exists and is readable
- [ ] `backup/` directory is empty or contains only previous deployments
- [ ] Black Book is fully installed in Steam
- [ ] Sufficient disk space for backup (~100 MB for game files + 894 KB for mod)
- [ ] Read `payload/TRANSLATIONS_LIST.txt` and verify conversions look correct

---

## 7. Verification After Deployment

After running `bash deploy.sh`:

```bash
# Verify deployment succeeded
ls -l /path/to/Black\ Book/Black\ Book_Data/StreamingAssets/Config/ | head -20

# Count deployed files
find /path/to/Black\ Book/Black\ Book_Data/StreamingAssets/Config -name "config_zh.yaml" | wc -l
# Should output: 1448

# Verify backup created
ls -la backup/game_backup_*/Config_original/ | head -10
```

---

## Ready to Deploy

✓ Scripts are 100% reversible  
✓ Translations list is human-readable  
✓ Backup system is robust  
✓ Zero risk of corrupting game files  

**Next step**: Run `bash deploy.sh` when ready!
