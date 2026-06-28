#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

KEYS = ("size640", "size800", "size1024", "size1280", "size1600", "sizeDefault")
NUM_PATTERN = re.compile(r'(?i)(\b([A-Za-z0-9_]+)\b\s*[:=]\s*"?)(-?\d+)("?)')


def load_baseline(path: Path) -> dict[str, dict[str, int]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {name: {k: int(v) for k, v in values.items()} for name, values in data.items()}


def target_sizes(profile: str, baseline: dict[str, int], size_default: int | None) -> dict[str, int]:
    out = {k: baseline[k] for k in KEYS if k in baseline}
    if profile != "vanilla":
        if size_default is None:
            raise ValueError(f"profile {profile} requires --size-default")
        out["sizeDefault"] = size_default
    return out


def patch_file(path: Path, desired: dict[str, int]) -> int:
    replacements = 0
    changed = False
    out_lines: list[str] = []

    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True):
        def repl(match: re.Match[str]) -> str:
            nonlocal replacements, changed
            key = match.group(2)
            desired_value = desired.get(key)
            if desired_value is None:
                desired_value = desired.get(key.lower())
            if desired_value is None:
                return match.group(0)
            old_value = int(match.group(3))
            if old_value == desired_value:
                return match.group(0)
            replacements += 1
            changed = True
            return f"{match.group(1)}{desired_value}{match.group(4)}"

        out_lines.append(NUM_PATTERN.sub(repl, line))

    if changed:
        path.write_text("".join(out_lines), encoding="utf-8")
    return replacements


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply a named font-size profile to extracted DoW DE .fnt files.")
    parser.add_argument("--font-dir", required=True, help="Directory containing extracted .fnt files")
    parser.add_argument("--baseline", required=True, help="Path to baseline font size JSON")
    parser.add_argument("--profile", choices=("vanilla", "1080p", "4k"), required=True)
    parser.add_argument("--size-default", type=int, help="sizeDefault override for non-vanilla profiles")
    args = parser.parse_args()

    font_dir = Path(args.font_dir)
    baseline = load_baseline(Path(args.baseline))
    files = sorted(font_dir.glob("*.fnt"))
    if not files:
        raise SystemExit(f"No .fnt files found in {font_dir}")

    changed_files = 0
    total_replacements = 0
    for file_path in files:
        if file_path.name not in baseline:
            continue
        desired = target_sizes(args.profile, baseline[file_path.name], args.size_default)
        count = patch_file(file_path, desired)
        if count:
            changed_files += 1
            total_replacements += count
            print(f"patched: {file_path.name} ({count} replacements)")

    print(f"profile={args.profile} files_changed={changed_files} replacements={total_replacements}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
