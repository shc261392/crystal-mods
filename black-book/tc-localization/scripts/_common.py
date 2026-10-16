"""Shared helpers for the build gates and the payload builder."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterator

try:
    from ruamel.yaml import YAML
except ImportError:  # pragma: no cover
    sys.exit("ERROR: ruamel.yaml is required. See pyproject.toml")

SCRIPT_DIR = Path(__file__).resolve().parent.parent
SOURCE_DIR = SCRIPT_DIR / "source" / "sc" / "StreamingAssets" / "Config"
PAYLOAD_DIR = SCRIPT_DIR / "payload" / "Black Book_Data" / "StreamingAssets" / "Config"

BOM = b"\xef\xbb\xbf"


def source_root() -> Path:
    return SOURCE_DIR


def payload_root() -> Path:
    return PAYLOAD_DIR


def _yaml() -> YAML:
    y = YAML(typ="safe")
    y.allow_unicode = True
    return y


def load(path: Path):
    """Parse a game YAML file, tolerating the UTF-8 BOM the game ships."""
    raw = path.read_bytes()
    if raw.startswith(BOM):
        raw = raw[len(BOM):]
    return _yaml().load(raw.decode("utf-8"))


def iter_strings(node, path: str = "") -> Iterator[tuple[str, str]]:
    """Yield ``(dotted_path, value)`` for every non-empty string scalar."""
    if isinstance(node, dict):
        for key, value in node.items():
            child = f"{path}.{key}" if path else str(key)
            yield from iter_strings(value, child)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from iter_strings(value, f"{path}[{index}]")
    elif isinstance(node, str) and node.strip():
        yield path, node


def iter_scalars(node, path: str = "") -> Iterator[tuple[str, object]]:
    """Yield ``(dotted_path, value)`` for every non-string, non-container scalar.

    Used to prove the converter never touched numbers, booleans or nulls.
    """
    if isinstance(node, dict):
        for key, value in node.items():
            child = f"{path}.{key}" if path else str(key)
            yield from iter_scalars(value, child)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from iter_scalars(value, f"{path}[{index}]")
    elif not isinstance(node, (dict, list, str)):
        yield path, node


def format_flags(path: Path) -> tuple[bool, bool]:
    """Return ``(has_bom, uses_crlf)`` for a file."""
    raw = path.read_bytes()
    return raw.startswith(BOM), b"\r\n" in raw

# --------------------------------------------------------------------------- #
# Taiwan terminology
# --------------------------------------------------------------------------- #

TERMS_FILE = SCRIPT_DIR / "reference" / "terms.tsv"


def load_terms() -> dict[str, str]:
    """Taiwan term fixes applied to EVERY converted string.

    OpenCC's s2twp dictionary does not cover every Mainland/Taiwan difference, and
    some of the strings that need them (dialogue, UI labels) live in
    data.unity3d and are only converted at runtime, so they cannot be expressed
    as config overrides.
    """
    terms: dict[str, str] = {}
    if not TERMS_FILE.exists():
        return terms
    for line in TERMS_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0].strip():
            terms[parts[0].strip()] = parts[1]
    return terms


def apply_terms(text: str, terms: dict[str, str]) -> str:
    """Longest-match replacement, so a longer term wins over a shorter one."""
    if not text or not terms:
        return text
    longest = max(len(k) for k in terms)
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        hit = None
        for length in range(min(longest, n - i), 0, -1):
            chunk = text[i:i + length]
            if chunk in terms:
                hit = terms[chunk]
                i += length
                break
        if hit is None:
            out.append(text[i])
            i += 1
        else:
            out.append(hit)
    return "".join(out)
