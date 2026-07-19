#!/usr/bin/env python3
# ruff: noqa: RUF001, RUF002, RUF003
# ^ Intentional use of fullwidth punctuation for Traditional Chinese localization
"""
Apply Traditional Chinese localization corrections to Engine.ucs.

This is a one-shot burn-down script. After each round of corrections has been
applied and verified in Engine.ucs, the corresponding rules are removed so
the script stays a clean scaffold ready for the next round.

Add new rules to:
- TARGETED   — line-ID-specific fixes (exact_old → new)
- GLOSSARY   — blanket substring substitutions
- WAAAGH_RE  — the ork warcry regex (only edit if the pattern changes)

Then:
    python scripts/apply_tc_corrections.py --dry-run
    python scripts/apply_tc_corrections.py

Once verified in-game, clear the rules and commit the empty scaffold.

Burn-down history (kept here for traceability; see docs/glossary-zh.md for
the canonical glossary):
- Round 1: punctuation / typo / colon / mine-field / generator / Bopomofo
  fixes; subtitle stray-char fixes; embedded ASCII plurals.
- Round 2: High-Gothic rewrite of Imperial litanies (IDs 31000–31100, plus
  short-form duplicates 3009 / 3010 / 3024 / 3025 and other scattered
  duplicates throughout the file).
- Round 3: Glossary — 猿人→歐格林; 政戰官/政戰軍官/政戰處/政戰部→政委/政委部;
  神靈族→艾達靈族 (note: 暗黑神靈族→暗黑靈族, applied as a separate one-off).
- Round 4: WAAAGH! regex — 吼變體 → WAAAGH (A-count = 3 + tilde count).
- Round 5: ASCII "..." → 「...」 (nested → 『...』); 5 odd-quote repairs.
"""

import argparse
import re
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_DEFAULT_UCS = _SCRIPT_DIR.parent / "Engine.ucs"

# ---------------------------------------------------------------------------
# Targeted corrections: {id: (exact_old_text, new_text)}
# Applied first, before the global passes. Cleared after each verified round.
# ---------------------------------------------------------------------------
TARGETED: dict[int, tuple[str, str]] = {}

# ---------------------------------------------------------------------------
# Glossary: blanket string replacements.
# Order matters — longest / most-specific patterns first.
# ---------------------------------------------------------------------------
GLOSSARY: tuple[tuple[str, str], ...] = ()

# ---------------------------------------------------------------------------
# WAAAGH! regex (matches the ork warcry 吼 variants, excluding compound words
# like 戰吼/怒吼/低吼/惡魔之吼/吼聲/吼叫/吼哇/怒吼者).
# Disabled by default so a re-run is a true no-op.
# ---------------------------------------------------------------------------
WAAAGH_ENABLED = False
WAAAGH_RE = re.compile(r"(?<![戰怒低之])吼(吼)?([~～]*)([!！]*)(?![哇聲叫者])")


def _waaagh_sub(m: "re.Match[str]") -> str:
    tildes = m.group(2) or ""
    bangs = m.group(3) or ""
    return "W" + ("A" * (3 + len(tildes))) + "GH" + bangs


# ---------------------------------------------------------------------------
# ASCII "..." → 「...」 quote conversion.
# Disabled by default so a re-run is a true no-op.
# ---------------------------------------------------------------------------
QUOTES_ENABLED = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
CHINESE_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\uff00-\uffef]")


def has_chinese(s: str) -> bool:
    return bool(CHINESE_RE.search(s))


def apply_glossary(text: str) -> str:
    for old, new in GLOSSARY:
        if old in text:
            text = text.replace(old, new)
    if WAAAGH_ENABLED:
        text = WAAAGH_RE.sub(_waaagh_sub, text)
    return text


def apply_quote_conversion(text: str, lid: int) -> str:
    if not QUOTES_ENABLED:
        return text
    n = text.count('"')
    if n == 0:
        return text
    if n % 2:
        print(f"  SKIP ID {lid}: odd-count ASCII quotes (n={n}); left as-is")
        return text
    nested = ("「" in text) or ("」" in text)
    open_ch, close_ch = ("『", "』") if nested else ("「", "」")
    out, is_open = [], True
    for ch in text:
        if ch == '"':
            out.append(open_ch if is_open else close_ch)
            is_open = not is_open
        else:
            out.append(ch)
    return "".join(out)


def apply_corrections(content: str, dry_run: bool) -> tuple[str, int]:
    lines = content.split("\r\n")
    changed = 0

    for i, line in enumerate(lines):
        if "\t" not in line:
            continue
        parts = line.split("\t", 1)
        try:
            lid = int(parts[0])
        except ValueError:
            continue

        original = parts[1]
        text = original

        # 1. Targeted ID-level corrections
        if lid in TARGETED:
            old, new = TARGETED[lid]
            if text == old:
                text = new
            elif old in text:
                text = text.replace(old, new, 1)
            else:
                print(f"  MISMATCH ID {lid}: expected\n    {old!r}\n  got\n    {parts[1]!r}")

        # 2. Global: ! → ！  (Chinese-containing lines only)
        if has_chinese(text) and "!" in text:
            text = text.replace("!", "！")

        # 3. Global: ? → ？  (Chinese-containing lines only)
        if has_chinese(text) and "?" in text:
            text = text.replace("?", "？")

        # 4. Glossary + (optional) WAAAGH regex
        text = apply_glossary(text)

        # 5. ASCII "..." → 「...」 (optional)
        text = apply_quote_conversion(text, lid)

        if text != original:
            changed += 1
            print(f"  ID {lid}:\n    OLD: {original!r}\n    NEW: {text!r}")
            if not dry_run:
                lines[i] = f"{parts[0]}\t{text}"

    return "\r\n".join(lines), changed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply Traditional Chinese localization corrections to Engine.ucs.",
    )
    parser.add_argument(
        "--ucs",
        default=str(_DEFAULT_UCS),
        metavar="PATH",
        help=f"Path to Engine.ucs (default: {_DEFAULT_UCS})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing any files.",
    )
    args = parser.parse_args()

    ucs_path = Path(args.ucs)
    if not ucs_path.exists():
        print(f"ERROR: Engine.ucs not found: {ucs_path}", file=sys.stderr)
        return 1

    print(f"Reading {ucs_path} ...")
    content = ucs_path.read_bytes().decode("utf-16")

    print(f"Applying corrections{'  [DRY RUN — no file written]' if args.dry_run else ''} ...\n")
    new_content, changed = apply_corrections(content, args.dry_run)

    print(f"\nTotal lines changed: {changed}")

    if changed == 0:
        print("No-op. The script is currently a clean scaffold.")
        return 0

    if not args.dry_run:
        out_bytes = b"\xff\xfe" + new_content.encode("utf-16-le")
        ucs_path.write_bytes(out_bytes)
        print(f"Written {len(out_bytes):,} bytes to {ucs_path}")
    else:
        print("Dry-run complete. Re-run without --dry-run to apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
