"""Thin PCGamingWiki client (MediaWiki + Cargo API)."""

from __future__ import annotations

import time
from collections import deque
from typing import Any

import httpx

PCGW_API = "https://www.pcgamingwiki.com/w/api.php"
PCGW_APPID = "https://www.pcgamingwiki.com/api/appid.php"
USER_AGENT = (
    "crystal-mods/pcgw-fetch/0.1.0 "
    "(+https://github.com/shc261392/crystal-mods)"
)


class _RateLimiter:
    """Simple rolling-window limiter (default 20 req/min — under PCGW's 30)."""

    def __init__(self, max_per_min: int = 20) -> None:
        self._max = max_per_min
        self._calls: deque[float] = deque()

    def wait(self) -> None:
        now = time.monotonic()
        while self._calls and now - self._calls[0] > 60:
            self._calls.popleft()
        if len(self._calls) >= self._max:
            sleep_for = 60 - (now - self._calls[0]) + 0.05
            if sleep_for > 0:
                time.sleep(sleep_for)
        self._calls.append(time.monotonic())


class PCGWClient:
    def __init__(self, timeout: float = 20.0) -> None:
        self._http = httpx.Client(
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            timeout=timeout,
            follow_redirects=True,
        )
        self._limit = _RateLimiter()

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> PCGWClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    # ── low-level ────────────────────────────────────────────────────────────

    def _get(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        self._limit.wait()
        r = self._http.get(url, params=params)
        if r.status_code == 429:
            time.sleep(5)
            r = self._http.get(url, params=params)
        r.raise_for_status()
        return r.json()

    # ── high-level ───────────────────────────────────────────────────────────

    def resolve_by_steam_appid(self, appid: str | int) -> str | None:
        """Return the PCGW page name for a Steam App ID, or None."""
        data = self._cargo_query(
            tables="Infobox_game",
            fields="Infobox_game._pageName=Page",
            where=f'Infobox_game.Steam_AppID HOLDS "{appid}"',
            limit=1,
        )
        rows = data.get("cargoquery", [])
        if not rows:
            return None
        return rows[0]["title"]["Page"]

    def opensearch(self, query: str, limit: int = 5) -> list[str]:
        data = self._get(
            PCGW_API,
            {
                "action": "opensearch",
                "search": query,
                "limit": limit,
                "redirects": "resolve",
                "format": "json",
            },
        )
        # opensearch returns [query, [titles], [descs], [urls]]
        return list(data[1]) if isinstance(data, list) and len(data) > 1 else []

    def fetch_infobox(self, page: str) -> dict[str, Any]:
        """Fetch Infobox_game + selected joined tables for a page."""
        # Conservative field set — verified against PCGW Cargo schema. Extending
        # this list requires checking https://www.pcgamingwiki.com/wiki/Special:CargoTables
        # because unknown fields fail the whole query.
        fields = ",".join(
            [
                "Infobox_game._pageName=Page",
                "Infobox_game.Developers",
                "Infobox_game.Publishers",
                "Infobox_game.Released",
                "Infobox_game.Engines",
                "Infobox_game.Steam_AppID",
                "Infobox_game.GOGcom_ID",
                "Infobox_game.Cover_URL",
            ]
        )
        page_escaped = page.replace('"', '\\"')
        data = self._cargo_query(
            tables="Infobox_game",
            fields=fields,
            where=f'Infobox_game._pageName="{page_escaped}"',
            limit=1,
        )
        rows = data.get("cargoquery", [])
        if not rows:
            return {}
        return rows[0]["title"]

    def fetch_api_table(self, page: str) -> dict[str, Any]:
        """Fetch the API (graphics) table — Direct3D / Vulkan / etc."""
        fields = ",".join(
            [
                "API.Direct3D_versions",
                "API.OpenGL_versions",
                "API.Vulkan_versions",
                "API.Metal",
                "API.Mantle",
                "API.Glide",
                "API.Software_renderer",
            ]
        )
        page_escaped = page.replace('"', '\\"')
        data = self._cargo_query(
            tables="API",
            fields=fields,
            where=f'API._pageName="{page_escaped}"',
            limit=1,
        )
        rows = data.get("cargoquery", [])
        if not rows:
            return {}
        return rows[0]["title"]

    def fetch_os_support(self, page: str) -> dict[str, Any]:
        """Fetch OS support (Windows / Linux / macOS columns)."""
        fields = ",".join(
            [
                "Infobox_game.Windows",
                "Infobox_game.OS_X",
                "Infobox_game.Linux",
            ]
        )
        page_escaped = page.replace('"', '\\"')
        data = self._cargo_query(
            tables="Infobox_game",
            fields=fields,
            where=f'Infobox_game._pageName="{page_escaped}"',
            limit=1,
        )
        rows = data.get("cargoquery", [])
        if not rows:
            return {}
        return rows[0]["title"]

    # ── internals ────────────────────────────────────────────────────────────

    def _cargo_query(
        self,
        *,
        tables: str,
        fields: str,
        where: str,
        limit: int = 1,
    ) -> dict[str, Any]:
        return self._get(
            PCGW_API,
            {
                "action": "cargoquery",
                "tables": tables,
                "fields": fields,
                "where": where,
                "limit": limit,
                "format": "json",
            },
        )
