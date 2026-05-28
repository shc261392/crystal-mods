from __future__ import annotations

from typing import Protocol


class Backend(Protocol):
    name: str

    def translate(self, text: str, src: str, tgt: str) -> str: ...
