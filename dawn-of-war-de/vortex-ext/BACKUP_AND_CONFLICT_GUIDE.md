# Vortex Extension Architecture Guide

**For:** DoW DE Game Extension Developers  
**Purpose:** Best practices for file backup, conflict resolution, and multi-mod SGA handling

---

## 1. File Backup Strategy

### Vortex's Recommended Approach

Vortex extensions do **NOT** perform traditional `.bak` backups. Instead:

**Official Pattern:**
- Extensions preserve game files by **not modifying them directly**
- Files are deployed through Vortex's "staging" system
- User can uninstall any mod → game returns to previous state automatically
- Vortex stores deployment history (who deployed what, when)

**Why .bak is problematic:**
- Creates clutter and confusion for users
- Doesn't integrate with Vortex's uninstall mechanism
- Users may accidentally delete backups
- No version tracking (which backup is current?)

### Our Recommended Backup Strategy for DoW DE

Given DoW DE's SGA architecture, here's the best approach:

**Deployment Pattern:**
```
Game state before mod:
└── Engine/Locale/Chinese/
    ├── EnginLoc.sga (207MB vanilla, read-only)
    └── Engine.ucs (vanilla, read-only)

After Vortex deploys TC mod v1.0.3:
└── Engine/Locale/Chinese/
    ├── EnginLoc.sga (207MB vanilla, unchanged)
    ├── Engine.ucs (TC version, from mod)
    ├── EnginLocMod.sga (207MB TC, deployed by extension)
    └── [deployment metadata]

User uninstalls TC mod:
└── Engine/Locale/Chinese/
    ├── EnginLoc.sga (restored to vanilla)
    └── Engine.ucs (restored to vanilla)
```

**Key Principle:** Extensions should NOT create `.bak` files. Vortex's uninstall mechanism restores state.

**Exception:** User configuration files that mods modify should be preserved:
- `.fnt` font configs → Store originals separately, not as `.bak`
- User preferences → Handled by mod itself (not extension's job)

---

## 2. SGA Conflict Resolution Strategy

### Problem Statement

**Scenario:** Two mods both want to edit `Engine/Locale/Chinese/EnginLocMod.sga`

```
User installs:
1. DoW DE TC Mod v1.0.3 (EnginLocMod.sga with TC fonts)
2. Custom Sound Mod (also wants to patch EnginLocMod.sga with new audio)

Result: Conflict! Which SGA wins?
```

### Current Vortex Behavior (File-Based)

**Default:** Last deployed mod's files overwrite previous ones
- Priority determined by mod **load order** (top = highest priority)
- No merging of SGA archives

**Problem:** This breaks both mods if they both edit same SGA!

### Recommended Solution: Staged SGA Merge

For locale-specific SGAs (single-file conflicts), implement this pattern:

#### Step 1: Detect SGA Conflicts

```javascript
// In extension's installLocaleContent()
async function detectSGAConflicts(modId, files) {
  const sgas = files.filter(f => f.endsWith('.sga'));
  const conflictingSGAs = sgas.filter(sga => 
    // Check if this SGA would conflict with already-deployed SGAs
    isAlreadyDeployed(sga)
  );
  
  if (conflictingSGAs.length > 0) {
    return { hasConflict: true, sgaFiles: conflictingSGAs };
  }
  return { hasConflict: false };
}
```

#### Step 2: User Notification (Guardrail)

**DON'T silently merge.** Alert user:

```javascript
if (conflictDetected) {
  context.api.sendNotification({
    type: 'warning',
    title: 'SGA File Conflict',
    message: `Mod "${modId}" wants to modify ${conflictingSGA}.
      
      Currently deployed: "${currentlyDeployedMod}"
      
      Options:
      1. Stack (keep both) - requires Archive.exe merge
      2. Replace - overwrite with new SGA
      3. Cancel - don't deploy this mod
      
      Higher priority mods override lower priority.`,
    actions: [
      { title: 'Stack' },
      { title: 'Replace' },
      { title: 'Cancel' }
    ]
  });
}
```

#### Step 3: Determine Priority

```javascript
// Load order determines SGA priority
const modLoadOrder = context.api.getState().loadOrder[gameId];
const currentModPriority = modLoadOrder.indexOf(modId);
const deployedModPriority = modLoadOrder.indexOf(currentlyDeployedModId);

if (currentModPriority > deployedModPriority) {
  // Current mod has higher priority → use its SGA
  action = 'replace';
} else if (currentModPriority < deployedModPriority) {
  // Deployed mod has higher priority → keep it, warn user
  action = 'skip';
}
```

#### Step 4: Safe Conflict Resolution (if merging possible)

**Only if user explicitly chooses "Stack":**

```javascript
// Archive.exe merge logic (optional, requires user to have Archive.exe)
async function mergeSGAs(baseSGA, newSGA, outputSGA, modPriority) {
  /*
  1. Extract both SGAs
  2. Merge file lists (mod load order determines priority)
  3. Re-pack to outputSGA
  4. Verify integrity
  5. Deploy merged SGA
  */
}
```

---

## 3. Recommended Implementation

### What We Should DO

✅ **Implement:**
```javascript
// installLocaleContent() enhancements
1. Detect SGA filename conflicts
2. Check if conflicting SGA already deployed
3. If conflict exists:
   a) Get user's preference via notification
   b) Respect load order priority
   c) Either skip, replace, or merge (with user consent)
4. Log conflict in deployment manifest
5. Warn user: "Higher priority mod overrides lower priority"
```

### What We Should NOT DO

❌ **Avoid:**
- Silent SGA overwrites (breaks user trust)
- Automatic merging (too risky without user consent)
- Creating `.bak` files (conflicts with Vortex's uninstall)
- Modifying SGAs in-place (use staging first)

---

## 4. Implementation Checklist

- [ ] **SGA Conflict Detection**
  - Check if SGA file already exists in deployment
  - Identify which mod currently owns it
  
- [ ] **User Notification**
  - Display conflict warning with clear options
  - Show load order priority explanation
  - Provide "Stack", "Replace", or "Cancel" actions

- [ ] **Priority Resolution**
  - Query mod load order from Vortex API
  - Determine winner based on priority
  - Log decision to deployment manifest

- [ ] **Guardrails**
  - Never silently overwrite existing SGA
  - Require explicit user action for conflicts
  - Preserve deployment history
  - Allow reverting to previous state via uninstall

- [ ] **Testing**
  - Test with 2+ mods editing same SGA
  - Verify uninstall restores previous state
  - Confirm load order priority is respected

---

## 5. Future Work: SGA Merge Tool

If conflicts become common, build a companion tool:

```bash
# Python utility (optional, advanced users only)
python sga-merge.py --base vanilla.sga \
                    --patch mod1.sga \
                    --patch mod2.sga \
                    --priority "mod2 > mod1" \
                    --output merged.sga
```

**Note:** Only for advanced users who understand SGA format.

---

## 6. Reference: Vortex API for Conflicts

**Key API Endpoints:**

```javascript
// Get current deployment state
context.api.getState().deployments[gameId][modId]

// Get mod load order
context.api.getState().loadOrder[gameId]

// Send user notification
context.api.sendNotification(notification)

// Access file system (staging folder)
context.api.getStagingPath(gameId)

// Register uninstall handler
context.registerAction('mod-settings', ..., () => { /* cleanup */ })
```

---

## Summary

| Aspect | Approach | Rationale |
|--------|----------|-----------|
| **Backups** | Let Vortex handle (uninstall) | Integrates with Vortex's lifecycle |
| **Conflicts** | Detect + alert user | Prevents silent data loss |
| **Priority** | Respect load order | Consistent with Vortex design |
| **SGA Merge** | Optional, with user consent | Complex, risky if automated |
| **.bak files** | Don't create | Clutter, not Vortex-native |

**Core Principle:** The extension's job is to **detect problems and alert users**, not to silently fix them.

---

**Status:** Recommended pattern ✅  
**Implementation:** Phase 2 (when SGA conflicts occur)  
**Risk Level:** Low (guardrails prevent silent failures)
