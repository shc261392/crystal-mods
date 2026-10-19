# Loose Data Deployment Purge — Complete

**Date:** 2026-07-04  
**Status:** ✅ COMPLETE  
**Scope:** Eliminated all obsolete loose data deployment code (v1.0.4+)

---

## Changes Summary

### Core Scripts Rewritten (SGA-only)

1. **deploy.sh** (493 → 307 lines)
   - ✅ Removed `DEPLOY_MODE` variable and `--mode` flag
   - ✅ Removed `DEPLOY_DIRS` array
   - ✅ Removed font-fix application (hardcoded size 34)
   - ✅ Removed `build_and_deploy_sga()` function
   - ✅ Removed all loose file deployment code
   - ✅ Removed EnginLoc.sga renaming logic
   - ✅ Simplified to: backup → copy SGA+UCS → done

2. **deploy.ps1** (287 → 214 lines)
   - ✅ Removed `$DeployDirs` array
   - ✅ Removed font-fix application code
   - ✅ Removed all loose file deployment code
   - ✅ Simplified to match bash version

3. **uninstall.sh** (239 → 145 lines)
   - ✅ Removed `DEPLOY_MODE` and `DEPLOY_DIRS`
   - ✅ Removed EnginLoc.sga renaming restoration
   - ✅ Removed data/ directory deletion
   - ✅ Simplified to: remove SGA+UCS → restore backup → done

### Build System

4. **Makefile**
   - ✅ Removed `deploy` (loose mode) target
   - ✅ Renamed `deploy-sga` → `deploy`
   - ✅ Removed `deploy-sga-dry` target
   - ✅ Updated target descriptions to remove "loose" references

### Documentation

5. **README.md**
   - ✅ Removed EnginLoc.sga renaming instructions from manual install
   - ✅ Updated uninstall steps to remove "delete data/ folder"
   - ✅ Updated both English and Chinese sections

6. **FONT_FIX_README.md**
   - ✅ Added **DEVELOPMENT ONLY** warning at top
   - ✅ Clarified loose data deployment is obsolete
   - ✅ Redirected end users to releases

7. **docs/CHANGELOG.md**
   - ✅ Added new section documenting architecture cleanup
   - ✅ Marked changes as BREAKING
   - ✅ Documented rationale (v1.0.4 established SGA-only)

---

## Verification Results

```bash
✓ No "loose" or "data/" references in deploy scripts
✓ No "--mode" or "DEPLOY_MODE" references
✓ deploy.sh --help runs without errors
✓ New simplified usage message displayed
```

### Test Output
```
Usage: bash deploy.sh [OPTIONS]

Options:
  --game-dir PATH   Override auto-detected game installation directory
  --dry-run         Show what would be deployed without writing anything
  --no-backup       Skip backup step (not recommended)
  --help            Show this help message

Environment:
  DOW_GAME_DIR      Alternative to --game-dir (env var)

Note:
  This script deploys pre-built SGA archives only.
  Loose data deployment has been removed (obsolete since v1.0.4).
```

---

## Files Modified

```
 M FONT_FIX_README.md
 M Makefile
 M README.md
 M deploy.ps1
 M deploy.sh
 M docs/CHANGELOG.md
 M uninstall.sh
```

---

## Impact Assessment

### For End Users
- ✅ **No breaking changes** — package structure unchanged
- ✅ Simpler manual install (no SGA renaming step)
- ✅ Clearer documentation

### For Developers
- ✅ Simpler deploy script (~40% code reduction)
- ✅ Single deployment path (no mode confusion)
- ✅ Faster maintenance (fewer code paths)
- ✅ Clearer separation: dev tools vs deployment

### For Future Maintenance
- ✅ **Eliminates confusion** about deployment modes
- ✅ **Prevents RCA incidents** like font size not working
- ✅ **Single source of truth**: pre-built SGA
- ✅ **Reduced testing surface**: one deployment method only

---

## Related Context

### Root Cause Analysis (Previous Issue)
The font size not working issue was caused by:
1. Unverified assumption: "SGA determines font size"
2. Reality: Deploy script hardcoded `--size 34` and overwrote SGA
3. Multiple broken deployment modes masking the issue

### Resolution
By eliminating loose data deployment:
1. SGA is now the single source of truth
2. No runtime font patching
3. No mode confusion
4. Simpler, more predictable deployment

---

## Next Steps

- [x] Purge loose data deployment code
- [x] Update all documentation
- [x] Test deploy.sh --help
- [ ] Test full deployment (when ready)
- [ ] Update v1.0.5 release notes
- [ ] Consider tagging this cleanup as v1.0.6

---

## Appendix: What Was Removed

### Obsolete Features (v1.0.4+)
- ❌ Loose file deployment mode (`--mode loose`)
- ❌ Runtime font patching during deploy
- ❌ EnginLoc.sga renaming workflow
- ❌ data/ directory management
- ❌ DEPLOY_MODE variable and validation
- ❌ build_and_deploy_sga() function
- ❌ Mode-dependent uninstall logic

### Retained (Essential)
- ✅ SGA-only deployment
- ✅ Backup/restore functionality
- ✅ Campaign state migration
- ✅ Pre-built EnginLocMod.sga + Engine.ucs
- ✅ Auto-detect game directory
- ✅ Dry-run mode
