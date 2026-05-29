"""Gemini REST backend.

Reads `GEMINI_API_KEY` from the environment. Model name is configurable
via project config or the CLI flag.
"""

from __future__ import annotations

import json
import os

import httpx

_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

_PROMPT = (
    "You are a professional game-localisation translator. Translate the text"
    " from {src} to {tgt}. Preserve placeholders that look like ⟦G\\d+⟧, line"
    " breaks, leading/trailing whitespace, and inline tags exactly. Reply with"
    " ONLY the translated text, no preamble.\n\nText:\n{text}"
)

_BATCH_PROMPT = (
    "You are a professional game-localisation translator for the political"
    " strategy game Suzerain. Translate each item's text from {src} to {tgt}."
    " Rules:\n"
    "- Preserve placeholders matching ⟦G\\d+⟧ EXACTLY (do not translate them).\n"
    "- Preserve line breaks, leading/trailing whitespace, and inline tags.\n"
    "- Keep proper nouns consistent.\n"
    "- Return a translation for EVERY input id, with the SAME id.\n\n"
    "Input items (JSON):\n{items}"
)


class GeminiBackend:
    name = "gemini"

    def __init__(self, model: str, timeout: float = 120.0) -> None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable is not set")
        self._key = api_key
        self._model = model
        self._client = httpx.Client(timeout=timeout)

    def _generate(self, prompt: str, generation_config: dict) -> str:
        url = f"{_BASE}/{self._model}:generateContent"
        body = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": generation_config,
        }
        r = self._client.post(url, params={"key": self._key}, json=body)
        r.raise_for_status()
        data = r.json()
        candidates = data.get("candidates") or []
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts") or []
        return "".join(p.get("text", "") for p in parts).strip()

    def translate(self, text: str, src: str, tgt: str) -> str:
        return self._generate(
            _PROMPT.format(src=src, tgt=tgt, text=text),
            {"temperature": 0.2},
        )

    def translate_batch(self, texts: list[str], src: str, tgt: str) -> list[str]:
        """Translate many strings in a single request.

        Returns a list aligned to `texts`. Any item the model fails to
        return is left as an empty string so the caller can retry it.
        """
        items = [{"id": i, "text": t} for i, t in enumerate(texts)]
        prompt = _BATCH_PROMPT.format(
            src=src, tgt=tgt, items=json.dumps(items, ensure_ascii=False)
        )
        schema = {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "INTEGER"},
                    "text": {"type": "STRING"},
                },
                "required": ["id", "text"],
            },
        }
        out_text = self._generate(
            prompt,
            {
                "temperature": 0.2,
                "responseMimeType": "application/json",
                "responseSchema": schema,
            },
        )
        result = [""] * len(texts)
        try:
            parsed = json.loads(out_text)
        except json.JSONDecodeError:
            return result
        if not isinstance(parsed, list):
            return result
        for rec in parsed:
            if not isinstance(rec, dict):
                continue
            idx = rec.get("id")
            txt = rec.get("text")
            if isinstance(idx, int) and 0 <= idx < len(texts) and isinstance(txt, str):
                result[idx] = txt
        return result

