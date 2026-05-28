#!/usr/bin/env python3
"""
Apply a Dawn of War DE font-size fix to unpacked .fnt files.

Default behavior (safer anti-clipping profile):
- Searches ./data/font recursively for *.fnt (or ./font)
- Rewrites only `sizeDefault` to the requested size
- Leaves `size640/800/1024/1280/1600` untouched unless `--mode all` is used
- Creates a .bak file next to each changed file (once)

Why: in DE, very large values across *all* size keys can cause top/bottom clipping in many UI elements.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


SIZE_KEYS = r"(?:font_?size|fontsize|size(?:default|\d+)?|lineheight)"
ASSIGNMENT = re.compile(
    rf"(?i)(?P<prefix>\b)(?P<key>{SIZE_KEYS})(?P<sep>\s*[:=]\s*)(?P<q>['\"]?)(?P<num>-?\d+)(?P=q)"
)
FILE_ASSIGNMENT = re.compile(
    r'(?i)(?P<prefix>\bfile\b\s*[:=]\s*)(?P<q>["\'])(?P<name>[^"\']+)(?P=q)'
)


def _should_patch_key(key: str, mode: str) -> bool:
    k = key.lower()
    if mode == "fallback-only":
        return k == "sizedefault"
    return k in {
        "font_size",
        "fontsize",
        "size",
        "sizedefault",
        "lineheight",
    } or (k.startswith("size") and k[4:].isdigit())


def patch_line(line: str, size: int, mode: str) -> tuple[str, int]:
    replacements = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal replacements
        key = m.group("key")
        if not _should_patch_key(key, mode):
            return m.group(0)
        replacements += 1
        return f"{m.group('prefix')}{key}{m.group('sep')}{m.group('q')}{size}{m.group('q')}"

    out = ASSIGNMENT.sub(repl, line)
    return out, replacements


def patch_file(
    path: Path,
    size: int,
    mode: str,
    dry_run: bool = False,
    replace_font_file: str | None = None,
    replace_font_match: str | None = None,
) -> tuple[bool, int]:
    original = path.read_text(encoding="utf-8", errors="ignore")
    lines = original.splitlines(keepends=True)

    total = 0
    new_lines: list[str] = []
    font_match_re = re.compile(replace_font_match, re.IGNORECASE) if replace_font_match else None

    for line in lines:
        new_line, changed = patch_line(line, size, mode)
        if replace_font_file:
            m = FILE_ASSIGNMENT.search(new_line)
            if m:
                old_name = m.group("name")
                if font_match_re is None or font_match_re.search(old_name):
                    new_line = FILE_ASSIGNMENT.sub(
                        lambda mm: f"{mm.group('prefix')}{mm.group('q')}{replace_font_file}{mm.group('q')}",
                        new_line,
                        count=1,
                    )
                    changed += 1
        total += changed
        new_lines.append(new_line)

    if total == 0:
        return False, 0

    if not dry_run:
        backup = path.with_suffix(path.suffix + ".bak")
        if not backup.exists():
            backup.write_text(original, encoding="utf-8")
        path.write_text("".join(new_lines), encoding="utf-8")

    return True, total


def restore_from_backup(path: Path, dry_run: bool = False) -> bool:
    backup = path.with_suffix(path.suffix + ".bak")
    if not backup.exists():
        return False
    if not dry_run:
        path.write_text(backup.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Patch Dawn of War font files to a larger size.")
    parser.add_argument("--root", default=".", help="Locale root directory (default: current directory)")
    parser.add_argument("--size", type=int, default=34, help="Target font size (default: 34)")
    parser.add_argument(
        "--mode",
        choices=("fallback-only", "all"),
        default="fallback-only",
        help="Patch strategy: fallback-only (sizeDefault only) or all (all size keys).",
    )
    parser.add_argument(
        "--restore-from-bak",
        action="store_true",
        help="Restore each .fnt from its .fnt.bak before applying patch.",
    )
    parser.add_argument(
        "--replace-font-file",
        default=None,
        help="Optional font filename to set in `file = \"...\"` entries (e.g. msyh.ttc).",
    )
    parser.add_argument(
        "--replace-font-match",
        default=r"NotoSansTC|Gulim",
        help="Regex filter for existing `file` names to replace (default: NotoSansTC|Gulim).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing files")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    candidates = [root / "data" / "font", root / "font"]
    font_dir = next((p for p in candidates if p.exists()), None)

    if font_dir is None:
        print("ERROR: Expected font folder not found. Tried:")
        for p in candidates:
            print(f"  - {p}")
        print("Hint: run unpack_chinese_locale.ps1 first.")
        return 1

    files = sorted(font_dir.rglob("*.fnt"))
    if not files:
        print(f"ERROR: No .fnt files found under: {font_dir}")
        return 1

    changed_files = 0
    replacements = 0
    restored = 0

    if args.restore_from_bak:
        for fp in files:
            if restore_from_backup(fp, dry_run=args.dry_run):
                restored += 1
        print(f"restored from .bak: {restored}/{len(files)}")

    for fp in files:
        changed, count = patch_file(
            fp,
            args.size,
            args.mode,
            dry_run=args.dry_run,
            replace_font_file=args.replace_font_file,
            replace_font_match=args.replace_font_match,
        )
        if changed:
            changed_files += 1
            replacements += count
            print(f"patched: {fp} ({count} replacements)")
        else:
            print(f"skipped: {fp} (no known size keys found)")

    mode = "DRY-RUN" if args.dry_run else "WRITE"
    print(f"[{mode}] files changed: {changed_files}/{len(files)}, replacements: {replacements}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
