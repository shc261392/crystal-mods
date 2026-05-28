from __future__ import annotations


class ManualBackend:
    name = "manual"

    def translate(self, text: str, src: str, tgt: str) -> str:  # noqa: ARG002
        return text
