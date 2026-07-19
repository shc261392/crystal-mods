# Engine.ucs File Structure - CRITICAL

## ⚠️ WARNING: Mixed Content File

`Engine.ucs` contains **BOTH**:
1. **Chinese localization strings** (safe to translate)
2. **English game mode keys** (MUST NOT CHANGE - hardcoded game references)

**Changing English keys will BREAK THE GAME.**

## Examples of MUST-NOT-CHANGE English Keys

```
11271878	Dark Crusade
11271879	Soulstorm
```

These are **internal game mode identifiers**. The game code expects these **exact English strings**.

- ✅ Used by game code to identify campaign modes
- ❌ Translating them causes game mode selection to fail
- ❌ Changing them breaks campaign loading

## Engine.ucs Edit Rules

### ✅ SAFE to Edit
- Actual UI text that players see (descriptions, tooltips, button labels)
- Dialogue subtitles
- Campaign story text

### ❌ FORBIDDEN to Edit
- Game mode keys (Dark Crusade, Soulstorm)
- Internal identifiers referenced by game code
- Any string that appears to be a "key" rather than "display text"

## Agent Operating Rules

**AGENTS MUST:**
1. **NEVER** edit `Engine.ucs` without explicit user approval
2. **NEVER** assume English text should be translated
3. **ALWAYS** ask user before making changes to `Engine.ucs`
4. **NEVER** create automated scripts that modify `Engine.ucs` without review

**When in doubt:** ASK THE USER.

## Recovery

If `Engine.ucs` is corrupted:
1. Restore from `dist/.archived/wh40k-dow-de-tc-mod-v1.0.6.zip`
2. Check git history for last known good version
3. User has manually preserved correct data as safeguard

## Why This Matters

The game expects specific English strings for internal logic. Translating these breaks core functionality even though the translation is technically correct Chinese.

**User knowledge and manual review saved this project from agent-caused corruption.**
