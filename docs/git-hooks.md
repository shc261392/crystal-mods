# Git Hooks Documentation

This repository uses git hooks to enforce quality and safety standards.

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
