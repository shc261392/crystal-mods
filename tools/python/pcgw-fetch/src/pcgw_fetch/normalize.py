"""Normalize PCGW Cargo rows into a metadata.jsonc shape."""

from __future__ import annotations

import datetime as dt
import re
from typing import Any

from . import __version__

_LIST_SPLIT = re.compile(r"\s*,\s*")
# PCGW Cargo values often carry a wiki-namespace prefix (e.g. "Company:Relic
# Entertainment", "Engine:Essence Engine"). Strip these for display.
_PREFIX_STRIP = re.compile(r"^(?:Company|Engine|Developer|Publisher|Series):")


def _split(value: str | None) -> list[str]:
    if not value:
        return []
    # PCGW often joins values with "," or " · ".
    return [_PREFIX_STRIP.sub("", v).strip() for v in _LIST_SPLIT.split(value) if v.strip()]


def _store_id(value: str | None) -> str | None:
    if not value:
        return None
    v = value.strip()
    return v or None


def _support(value: str | None) -> str:
    """Map PCGW OS column to our enum."""
    if not value:
        return "unsupported"
    v = value.strip().lower()
    if not v or v in {"unknown", "?"}:
        return "untested"
    if v in {"true", "yes", "native", "1"}:
        return "primary"
    if "proton" in v or "wine" in v or "compatibility" in v:
        return "supported"
    return "primary"


def _graphics_apis(api_row: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for label, key in [
        ("Direct3D", "Direct3D versions"),
        ("OpenGL", "OpenGL versions"),
        ("Vulkan", "Vulkan versions"),
        ("Metal", "Metal"),
        ("Mantle", "Mantle"),
        ("Glide", "Glide"),
    ]:
        val = api_row.get(key)
        if not val:
            continue
        sval = str(val).strip()
        if not sval or sval.lower() in {"false", "no", "0"}:
            continue
        if label in {"Metal", "Mantle", "Glide"}:
            out.append(label)
        else:
            for v in _split(sval):
                out.append(f"{label} {v}")
    if api_row.get("Software renderer"):
        out.append("Software")
    return out


def build_metadata(
    *,
    page: str,
    infobox: dict[str, Any],
    api_row: dict[str, Any],
    os_row: dict[str, Any],
    pcgw_url: str,
) -> dict[str, Any]:
    now = dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    return {
        "$schema": "../docs/schemas/game-metadata.schema.json",
        "pcgwPage": page,
        "displayName": infobox.get("Page") or page,
        "released": infobox.get("Released") or None,
        "developers": _split(infobox.get("Developers")),
        "publishers": _split(infobox.get("Publishers")),
        "engine": _split(infobox.get("Engines")),
        "graphicsApi": _graphics_apis(api_row),
        "stores": {
            "steam": (
                {"appId": _store_id(infobox.get("Steam AppID"))}
                if infobox.get("Steam AppID")
                else None
            ),
            "gog": (
                {"id": _store_id(infobox.get("GOGcom ID"))}
                if infobox.get("GOGcom ID")
                else None
            ),
            "epic": (
                {"id": _store_id(infobox.get("Epic Games Store ID"))}
                if infobox.get("Epic Games Store ID")
                else None
            ),
            "ubisoft": (
                {"id": _store_id(infobox.get("Ubisoft Connect ID"))}
                if infobox.get("Ubisoft Connect ID")
                else None
            ),
            "microsoft": (
                {"id": _store_id(infobox.get("Microsoft Store ID"))}
                if infobox.get("Microsoft Store ID")
                else None
            ),
        },
        "os": {
            "windows": _support(os_row.get("Windows")),
            "macos": _support(os_row.get("OS X")),
            "linuxProton": _support(os_row.get("Linux")),
        },
        "modding": {
            "framework": None,
            "vortexExtension": False,
        },
        "links": {
            "pcgw": pcgw_url,
            "nexus": None,
        },
        "_source": f"pcgw-fetch v{__version__}",
        "_fetchedAt": now,
    }
