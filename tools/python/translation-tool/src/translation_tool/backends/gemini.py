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

_GLOSSARY_PROMPT = (
    "You are building a bilingual glossary for a narrative video game.{context}"
    " For each English term below, provide the best {tgt} rendering. Rules:\n"
    "- Personal names and place names: transliterate consistently (phonetic).\n"
    "- Factions, titles, institutions, and game concepts: translate by meaning.\n"
    "- Keep each translation concise (the term only, no explanation).\n"
    "- Stay consistent with the ESTABLISHED translations below: reuse their"
    " character roots for related/derived forms (e.g. nationalities,"
    " possessives, adjectives).\n{known}"
    "- Return a result for EVERY input id, with the SAME id.\n\n"
    "Terms (JSON):\n{items}"
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

    def translate_glossary(
        self, terms: list[str], src: str, tgt: str, context: str = "",
        known: dict[str, str] | None = None,
    ) -> list[str]:
        """Translate a list of glossary terms (proper nouns / concepts).

        `known` is an optional map of already-established term→translation pairs
        used to keep derived forms consistent. Returns a list aligned to
        `terms`; failed items stay empty.
        """
        items = [{"id": i, "text": t} for i, t in enumerate(terms)]
        ctx = f" The game is: {context}." if context else ""
        if known:
            pairs = "\n".join(f"  {s} = {t}" for s, t in known.items())
            known_block = f"Established translations:\n{pairs}\n"
        else:
            known_block = ""
        prompt = _GLOSSARY_PROMPT.format(
            tgt=tgt, context=ctx, known=known_block,
            items=json.dumps(items, ensure_ascii=False),
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
                "temperature": 0.1,
                "responseMimeType": "application/json",
                "responseSchema": schema,
            },
        )
        result = [""] * len(terms)
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
            if isinstance(idx, int) and 0 <= idx < len(terms) and isinstance(txt, str):
                result[idx] = txt.strip()
        return result

