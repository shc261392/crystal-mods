#!/usr/bin/env python3
"""Build the Traditional Chinese payload from the checked-in Simplified
Chinese source tree.

Pipeline:  source/sc/**/config_zh.yaml  --OpenCC s2twp-->  payload/**/config_zh.yaml

Design notes
------------
*   The source tree under ``source/sc`` is the game's own Simplified Chinese
    localisation, copied verbatim.  The build never reads the installed game,
    so ``make build`` is reproducible on any machine (AGENTS.md rule 15).
*   Every string scalar is converted, at any nesting depth, including inside
    lists.  The previous implementation built dotted key paths but then looked
    them up against bare keys, which silently dropped every nested file
    (``Service/Credits``, ``Demons``, ``Izba``).
*   Output preserves the game's native file format byte-for-byte: UTF-8 BOM,
    CRLF line endings, key order, quoting style, comments and the exact
    trailing newline run.  Files whose text needs no change are copied
    verbatim instead of being re-serialised.
"""

from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

try:
    from opencc import OpenCC
except ImportError:  # pragma: no cover
    sys.exit("ERROR: opencc-python-reimplemented is required. See pyproject.toml")

try:
    from ruamel.yaml import YAML
except ImportError:  # pragma: no cover
    sys.exit("ERROR: ruamel.yaml is required. See pyproject.toml")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import apply_terms, load_terms  # noqa: E402

TERMS = load_terms()

SCRIPT_DIR = Path(__file__).resolve().parent.parent
SOURCE_DIR = SCRIPT_DIR / "source" / "sc" / "StreamingAssets" / "Config"
PAYLOAD_DIR = SCRIPT_DIR / "payload" / "Black Book_Data" / "StreamingAssets" / "Config"
OVERRIDES_FILE = SCRIPT_DIR / "reference" / "overrides.tsv"

# OpenCC profile: Simplified -> Traditional (Taiwan), with phrase substitution.
CONVERTER = OpenCC("s2twp")

BOM = b"\xef\xbb\xbf"


# --------------------------------------------------------------------------- #
# YAML round-trip helpers
# --------------------------------------------------------------------------- #


def _reader() -> YAML:
    y = YAML(typ="rt")
    y.preserve_quotes = True
    y.width = 1 << 30  # never wrap long lines
    y.allow_unicode = True
    return y


def _writer() -> YAML:
    y = YAML(typ="rt")
    y.preserve_quotes = True
    y.width = 1 << 30
    y.allow_unicode = True
    return y


def split_format(raw: bytes) -> tuple[str, bool, bytes]:
    """Return (text, has_bom, trailing_newline_run)."""
    has_bom = raw.startswith(BOM)
    body = raw[len(BOM):] if has_bom else raw
    tail_match = re.search(rb"(\r?\n)+$", body)
    tail = tail_match.group() if tail_match else b""
    return body.decode("utf-8"), has_bom, tail


def serialise(data: object, has_bom: bool, crlf: bool, tail: bytes) -> bytes:
    """Dump ``data`` back to bytes matching the original file's conventions."""
    buf = io.StringIO()
    _writer().dump(data, buf)
    out = buf.getvalue()
    if crlf:
        out = out.replace("\r\n", "\n").replace("\n", "\r\n")
    out = re.sub(r"(\r?\n)+$", "", out)
    return (BOM if has_bom else b"") + out.encode("utf-8") + tail


# --------------------------------------------------------------------------- #
# Conversion
# --------------------------------------------------------------------------- #


def convert_node(node: object, stats: dict[str, int]) -> int:
    """Convert every string scalar in ``node`` in place. Returns changes made.

    Recurses through both mappings and sequences, so nested structures and
    list items are handled.
    """
    changed = 0
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(value, str):
                tc = apply_terms(CONVERTER.convert(value), TERMS)
                if tc != value:
                    node[key] = tc
                    changed += 1
                    stats["strings"] += 1
            else:
                changed += convert_node(value, stats)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            if isinstance(value, str):
                tc = apply_terms(CONVERTER.convert(value), TERMS)
                if tc != value:
                    node[index] = tc
                    changed += 1
                    stats["strings"] += 1
            else:
                changed += convert_node(value, stats)
    return changed


# --------------------------------------------------------------------------- #
# Manual overrides
# --------------------------------------------------------------------------- #


def load_overrides(path: Path) -> dict[str, dict[str, str]]:
    """Parse reference/overrides.tsv into ``{relative_file: {key: replacement}}``."""
    overrides: dict[str, dict[str, str]] = {}
    if not path.exists():
        return overrides
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            raise SystemExit(
                f"ERROR: {path.name}:{lineno}: expected 3 TAB-separated fields, "
                f"got {len(parts)}"
            )
        rel, key, replacement = parts
        overrides.setdefault(rel.strip(), {})[key.strip()] = replacement
    return overrides


def apply_overrides(node: object, key_map: dict[str, str]) -> list[str]:
    """Set the named string leaves to their override value.

    Returns the list of override keys that actually matched, so the caller can
    report (and gate_overrides.py can flag) entries that matched nothing.
    """
    matched: list[str] = []

    def recurse(obj, path: str) -> None:
        if isinstance(obj, dict):
            for key, value in list(obj.items()):
                child = f"{path}.{key}" if path else str(key)
                if isinstance(value, str):
                    if child in key_map:
                        obj[key] = key_map[child]
                        matched.append(child)
                else:
                    recurse(value, child)
        elif isinstance(obj, list):
            for index, value in enumerate(list(obj)):
                child = f"{path}[{index}]"
                if isinstance(value, str):
                    if child in key_map:
                        obj[index] = key_map[child]
                        matched.append(child)
                else:
                    recurse(value, child)

    recurse(node, "")
    return matched


def count_strings(node: object) -> int:
    if isinstance(node, dict):
        return sum(count_strings(v) for v in node.values())
    if isinstance(node, list):
        return sum(count_strings(v) for v in node)
    return 1 if isinstance(node, str) and node.strip() else 0


def iter_strings(node, path: str = ""):
    """Yield ``(dotted_path, value)`` for every non-empty string scalar."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield from iter_strings(value, f"{path}.{key}" if path else str(key))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from iter_strings(value, f"{path}[{index}]")
    elif isinstance(node, str) and node.strip():
        yield path, node


def build_file(src: Path, rel: Path, dst: Path, stats: dict,
               overrides: dict[str, str],
               examples: list[tuple[str, str, str]]) -> list[str]:
    """Convert one file. Returns the override keys that actually matched."""
    raw = src.read_bytes()
    text, has_bom, tail = split_format(raw)
    crlf = "\r\n" in text

    data = _reader().load(text)
    if data is None:
        data = {}

    before = {path: value for path, value in iter_strings(data)}
    changed = convert_node(data, stats)
    stats["files"] += 1
    stats["strings_total"] += count_strings(data)

    matched = apply_overrides(data, overrides) if overrides else []
    stats["overrides"] += len(matched)

    dst.parent.mkdir(parents=True, exist_ok=True)
    if changed == 0 and not overrides:
        # Nothing to convert - emit the original bytes untouched so the file
        # stays byte-identical to what the game shipped.
        dst.write_bytes(raw)
        stats["verbatim"] += 1
    else:
        dst.write_bytes(serialise(data, has_bom, crlf, tail))
        stats["rewritten"] += 1

    # Collect a few before/after pairs for the build report.
    after = dict(iter_strings(data))
    for path, value in before.items():
        new = after.get(path)
        if new is not None and new != value and len(examples) < 8:
            examples.append((f"{rel} [{path}]", value, new))

    return matched


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #


def write_report(payload_root: Path, stats: dict, examples: list[tuple[str, str, str]]) -> None:
    """Write a build report next to the payload."""
    # Deliberately OUTSIDE Black Book_Data: package_zip.py stages that tree
    # wholesale, so a report written inside it would be deployed into the
    # game folder.
    report = payload_root.parent.parent.parent / "EXTRACTION_REPORT.txt"
    lines = [
        "Black Book TC Localization - build report",
        "=" * 60,
        "",
        f"Config files      : {stats['files']}",
        f"Strings total     : {stats['strings_total']}",
        f"Strings converted : {stats['strings']}",
        f"Files copied as-is: {stats['verbatim']}  (no Simplified text to convert)",
        f"Files re-serialised: {stats['rewritten']}",
        f"Manual overrides  : {stats['overrides']}",
        "",
        "Sample conversions (SC -> TC):",
        "-" * 60,
    ]
    for path, sc, tc in examples:
        lines.append(f"  {path}")
        lines.append(f"    SC: {sc}")
        lines.append(f"    TC: {tc}")
    lines.append("")
    report.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"  report           : {report.relative_to(SCRIPT_DIR)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE_DIR)
    parser.add_argument("--payload", type=Path, default=PAYLOAD_DIR)
    parser.add_argument("--overrides", type=Path, default=OVERRIDES_FILE)
    args = parser.parse_args()

    if not args.source.is_dir():
        sys.exit(f"ERROR: SC source tree not found: {args.source}")

    sources = sorted(args.source.rglob("config_zh.yaml"))
    if not sources:
        sys.exit(f"ERROR: no config_zh.yaml found under {args.source}")

    # Always regenerate from scratch so stale files can never survive a build.
    if args.payload.exists():
        shutil.rmtree(args.payload)
    args.payload.mkdir(parents=True, exist_ok=True)

    stats = {"files": 0, "strings": 0, "strings_total": 0, "verbatim": 0,
             "rewritten": 0, "overrides": 0}
    overrides = load_overrides(args.overrides)
    remaining = dict(overrides)
    examples: list[tuple[str, str, str]] = []

    for src in sources:
        rel = src.relative_to(args.source)
        rel_str = str(rel)
        file_overrides = remaining.pop(rel_str, {})
        matched = build_file(src, rel, args.payload / rel, stats, file_overrides,
                             examples)
        for key in file_overrides:
            if key not in matched:
                print(f"ERROR: override matched nothing: {rel_str} [{key}]",
                      file=sys.stderr)

    # Overrides pointing at files that do not exist at all.
    for rel_str, key_map in remaining.items():
        for key in key_map:
            print(f"ERROR: override targets a missing file: {rel_str} [{key}]",
                  file=sys.stderr)

    print(f"  source files      : {len(sources)}")
    print(f"  payload files     : {stats['files']}")
    print(f"  copied verbatim   : {stats['verbatim']}  (no Simplified text)")
    print(f"  re-serialised     : {stats['rewritten']}")
    print(f"  strings converted : {stats['strings']}")
    print(f"  strings total     : {stats['strings_total']}")
    print(f"  overrides applied : {stats['overrides']}")
    write_report(args.payload, stats, examples)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())