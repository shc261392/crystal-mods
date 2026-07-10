# Git Hooks Documentation

This repository uses git hooks to enforce quality and safety standards.

## Hooks Overview

1. **pre-commit**: Blocks large files (>= 25MB)
2. **commit-msg**: Enforces UI verification evidence (NEW)

## Pre-commit Hook

### Purpose
Prevents commits of files >= 25MB to avoid bloating git history with large binary files.

### Location
`.git/hooks/pre-commit`

### How It Works
- Runs automatically before every `git commit`
- Checks all staged files for size
- Blocks commit if any file is >= 25MB
- Provides clear error message with remediation steps

### Bypassing (Requires Human Approval)
If you have verified that a large file MUST be committed:
```bash
git commit --no-verify
```

**⚠️ WARNING**: Only bypass after explicit human approval and verification that:
1. The file cannot be stored elsewhere (GitHub Releases, CDN, Git LFS)
2. The file is absolutely necessary for the repository
3. You understand this will bloat git history permanently

### Testing
To verify the hook works:
```bash
# Create a test file
dd if=/dev/zero of=test_30mb.dat bs=1M count=30

# Try to commit it (should be blocked)
git add test_30mb.dat
git commit -m "test"

# Clean up
git restore --staged test_30mb.dat
rm test_30mb.dat
```

### Installation
The hook is already installed in this repository. If you clone to a new location or need to reinstall:

1. The hook file is at `.git/hooks/pre-commit`
2. It's automatically active (executable permissions set)
3. No additional setup required

## Commit-msg Hook (UI Verification)

### Purpose
Enforces visual verification for UI changes to prevent broken deployments.

**AGENTS.md Rule #9**: AI agents must visually verify UI changes using browser tools before claiming completion.

### How It Works
1. Detects if commit modifies UI files:
   - `src/pages/**/*.astro` (pages)
   - `src/components/**/*.{astro,tsx,jsx}` (components)
   - `src/layouts/**/*.astro` (layouts)
   - `**/*.{css,scss}` (stylesheets)

2. Checks commit message for verification evidence:
   - `[verified]` - Manual verification tag
   - `screenshot:` - Screenshot reference
   - `tested in browser:` - Browser test claim
   - `dev server:` - Dev server verification
   - `visual test:` - Visual testing description

3. Blocks commit if UI files modified WITHOUT verification evidence

### Example: Blocked Commit

```bash
$ git commit -m "fix(ui): ability editor shows weapons"

❌ UI VERIFICATION REQUIRED

This commit modifies UI code but lacks visual verification evidence.

Modified UI files:
  - src/pages/editor/abilities.astro

Add verification evidence to your commit message:
  • [verified] - Manual verification tag
  • screenshot: <description>
  • tested in browser: <outcome>
```

### Example: Allowed Commit

```bash
$ git commit -m "fix(ui): ability editor shows weapons

[verified] Tested in dev server at localhost:4324
Screenshot shows ability #20000 with 4 weapons displayed correctly"

[main abc1234] fix(ui): ability editor shows weapons
```

### Bypassing (Emergency Only)

If you have human approval to bypass verification:
```bash
git commit --no-verify -m "your message"
```

**⚠️ WARNING**: Only bypass after explicit human approval. Unverified UI changes may break production.

### Testing the Hook

```bash
# Test 1: UI change without verification (should block)
echo "<!-- test -->" >> src/pages/index.astro
git add src/pages/index.astro
git commit -m "test: update page"
# Expected: ❌ BLOCKED

# Test 2: UI change with verification (should pass)
git commit -m "test: update page

[verified] Visually tested in browser"
# Expected: ✓ ALLOWED

# Test 3: Non-UI change (should pass without verification)
echo "test" >> README.md
git add README.md  
git commit -m "docs: update readme"
# Expected: ✓ ALLOWED

# Cleanup
git reset HEAD~1
git restore src/pages/index.astro
```

### Installation
The hook is already installed at `.git/hooks/commit-msg` with executable permissions.

### Troubleshooting

**Hook not running?**
- Check file is executable: `ls -l .git/hooks/pre-commit`
- If not: `chmod +x .git/hooks/pre-commit`

**Need to disable temporarily?**
```bash
# Option 1: Use --no-verify for this commit only
git commit --no-verify

# Option 2: Rename hook to disable
mv .git/hooks/pre-commit .git/hooks/pre-commit.disabled
```

## Why This Matters

Git is designed for source code, not large binaries. Large files:
- **Bloat history permanently** (never truly deleted even if removed later)
- **Slow down operations** (clone, pull, fetch become extremely slow)
- **Make collaboration painful** (huge repo sizes for all contributors)
- **Violate best practices** (git != file storage)

### Better Alternatives
- **GitHub Releases**: For distributable binaries (ZIPs, executables)
- **Git LFS**: For version-controlled large files (models, assets)
- **CDN/Cloud Storage**: For static assets (images, videos)
- **Build artifacts**: Should be generated, not committed
