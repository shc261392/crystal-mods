from __future__ import annotations

from .base import Backend
from .gemini import GeminiBackend
from .google import GoogleBackend
from .manual import ManualBackend


def get_backend(name: str, model: str) -> Backend:
    if name == "manual":
        return ManualBackend()
    if name == "google":
        return GoogleBackend()
    if name == "gemini":
        return GeminiBackend(model=model)
    raise ValueError(f"Unknown backend: {name}")


__all__ = ["Backend", "GeminiBackend", "GoogleBackend", "ManualBackend", "get_backend"]
