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