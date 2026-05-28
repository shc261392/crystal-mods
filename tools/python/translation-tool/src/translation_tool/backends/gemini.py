"""Gemini REST backend.

Reads `GEMINI_API_KEY` from the environment. Model name is configurable
via project config or the CLI flag.
"""

from __future__ import annotations

import os

import httpx

_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

_PROMPT = (
    "You are a professional game-localisation translator. Translate the text"
    " from {src} to {tgt}. Preserve placeholders that look like ⟦G\\d+⟧, line"
    " breaks, leading/trailing whitespace, and inline tags exactly. Reply with"
    " ONLY the translated text, no preamble.\n\nText:\n{text}"
)


class GeminiBackend:
    name = "gemini"

    def __init__(self, model: str, timeout: float = 60.0) -> None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable is not set")
        self._key = api_key
        self._model = model
        self._client = httpx.Client(timeout=timeout)

    def translate(self, text: str, src: str, tgt: str) -> str:
        url = f"{_BASE}/{self._model}:generateContent"
        body = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": _PROMPT.format(src=src, tgt=tgt, text=text)}],
                }
            ],
            "generationConfig": {"temperature": 0.2},
        }
        r = self._client.post(url, params={"key": self._key}, json=body)
        r.raise_for_status()
        data = r.json()
        candidates = data.get("candidates") or []
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts") or []
        return "".join(p.get("text", "") for p in parts).strip()
