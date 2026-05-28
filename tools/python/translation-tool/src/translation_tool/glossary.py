"""Glossary with longest-match placeholder protection."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GlossaryRule:
    src: str
    tgt: str


def load_glossary(path: Path) -> list[GlossaryRule]:
    rules: list[GlossaryRule] = []
    if not path.exists():
        return rules
    for line in path.read_text("utf-8").splitlines():
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0]:
            rules.append(GlossaryRule(src=parts[0], tgt=parts[1]))
    rules.sort(key=lambda r: len(r.src), reverse=True)
    return rules


def protect(text: str, rules: list[GlossaryRule]) -> tuple[str, dict[str, str]]:
    """Replace glossary src terms with stable placeholders.

    Returns the protected text and a placeholder→target map so we can
    restore after the backend translates the surrounding text.
    """
    mapping: dict[str, str] = {}
    out = text
    for i, rule in enumerate(rules):
        token = f"⟦G{i}⟧"
        pattern = re.compile(re.escape(rule.src))
        if pattern.search(out):
            out = pattern.sub(token, out)
            mapping[token] = rule.tgt
    return out, mapping


def restore(text: str, mapping: dict[str, str]) -> str:
    out = text
    for token, tgt in mapping.items():
        out = out.replace(token, tgt)
    return out
