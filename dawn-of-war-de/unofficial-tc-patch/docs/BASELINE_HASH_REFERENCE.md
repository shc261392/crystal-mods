# Baseline Hash Reference — DoW DE Vanilla Locale Files

> **Critical for backup validation and troubleshooting. DO NOT DELETE.**

## Purpose

This document establishes the **canonical hashes of unmodified original files** shipped by Steam with Warhammer 40K: Dawn of War – Definitive Edition. Use these to verify whether a backup or deployment state contains TC-modified files.

## Vanilla Baseline (Original/Clean)

| File | Size | SHA256 Hash | Notes |
|------|------|-------------|-------|
| `Engine/Locale/Chinese/EnginLoc.sga` | 190M | `9174735668f20090bc5f1cbe443050b68a6e559aff288786f3b830e9e077cb4a` | Original packed locale archive (vanilla Chinese) |
| `Engine/Locale/Chinese/Engine.ucs` | 1.6M | `215baacd2846db80229b5763723b4b998642f197507dec752d65ce473f22ff02` | Original game strings table (vanilla Chinese) |

## Verification Instructions

### Compute Hashes

**Linux / WSL2:**
```bash
sha256sum "$GAME_DIR/Engine/Locale/Chinese/EnginLoc.sga" \
          "$GAME_DIR/Engine/Locale/Chinese/Engine.ucs"
```

**Windows (PowerShell):**
```powershell
Get-FileHash -Algorithm SHA256 `
  -Path "$env:GAME_DIR\Engine\Locale\Chinese\EnginLoc.sga", `
        "$env:GAME_DIR\Engine\Locale\Chinese\Engine.ucs"
```

### Interpret Results

- **Both hashes match baseline** → Files are VANILLA (unmodified original)
- **Either hash differs** → Files are TC-MODIFIED or corrupted

## Backup Audit

When validating a backup in `backup/<YYYYMMDD-HHmmss>/`:

```bash
# Check a specific backup
cd backup/20260604-115747/
sha256sum EnginLoc.sga Engine.ucs

# Should output:
# 9174735668f20090bc5f1cbe443050b68a6e559aff288786f3b830e9e077cb4a  EnginLoc.sga
# 215baacd2846db80229b5763723b4b998642f197507dec752d65ce473f22ff02  Engine.ucs
```

**If hashes match** → Safe to restore; this backup contains vanilla original files.  
**If hashes differ** → Unsafe to restore; this backup contains TC-modified files. Use only if absolutely necessary (e.g., to revert an in-progress TC deployment).

## Known Audit Results

| Backup ID | Status | SGA Hash Match | UCS Hash Match |
|-----------|--------|---|---|
| `20260604-115747` | ✓ SAFE | Yes | Yes |
| `20260605-211309` | ⚠️ PARTIAL | Yes | No (TC-modified) |

> **⚠️ WARNING:** Backup `20260605-211309` has TC-modified `Engine.ucs`. Do not use for full vanilla restoration—only for reverting an incomplete TC deployment.

## When to Use This Reference

1. **Before running `uninstall.sh`** — Verify it will restore from a vanilla backup
2. **Troubleshooting failed deploys** — Identify if backups have been "touched"
3. **Manual restoration** — Ensure you're restoring from the correct backup
4. **Auditing the mod state** — Compare current game files against baseline to detect corruption

## If Files Don't Match Baseline

If your current game files do not match the baseline hashes:

1. **Option 1: Verify game files via Steam** (recommended)
   - Right-click **Dawn of War Definitive Edition** in Steam
   - Click **Manage** → **Verify integrity of game files**
   - Steam will download any missing or corrupted files

2. **Option 2: Restore from a vanilla backup** (if Step 1 fails)
   ```bash
   # Copy the vanilla backup over the current files
   rsync -a backup/20260604-115747/ \
     "$GAME_DIR/Engine/Locale/Chinese/"
   ```

3. **Option 3: Full game reinstall** (if all else fails)
   - Uninstall the game from Steam
   - Delete the game directory manually
   - Reinstall from Steam

## Change History

| Date | Event |
|------|-------|
| 2026-06-05 | Baseline hashes computed and verified from clean Steam installation |

---

**Maintained by:** Crystal Mods TC Patch Team  
**Last Updated:** 2026-06-05
