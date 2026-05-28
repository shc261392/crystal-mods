"""Unofficial Google Translate web endpoint.

Uses the `client=gtx` single-translation endpoint. No API key. May be
rate-limited or blocked at any time \u2014 use sparingly and prefer a paid
backend for bulk runs.
"""

from __future__ import annotations

import httpx

_URL = "https://translate.googleapis.com/translate_a/single"


class GoogleBackend:
    name = "google"

    def __init__(self, timeout: float = 15.0) -> None:
        self._client = httpx.Client(timeout=timeout)

    def translate(self, text: str, src: str, tgt: str) -> str:
        params = {
            "client": "gtx",
            "sl": _normalize(src),
            "tl": _normalize(tgt),
            "dt": "t",
            "q": text,
        }
        r = self._client.get(_URL, params=params)
        r.raise_for_status()
        data = r.json()
        # data[0] is a list of [translated_segment, source_segment, ...]
        if not data or not data[0]:
            return ""
        return "".join(seg[0] for seg in data[0] if seg and seg[0])


def _normalize(lang: str) -> str:
    # Google uses "zh-TW", "zh-CN", "en" etc. Pass through but lowercase region prefix.
    return lang
