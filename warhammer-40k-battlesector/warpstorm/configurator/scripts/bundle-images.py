#!/usr/bin/env python3
"""Warpstorm — bundle unit/weapon images for the configurator.

Downloads the icons referenced by BattleSector Tools data (from the same R2
bucket the site uses), downscales them, and writes them into
`configurator/assets/` where the csproj embeds them (AvaloniaResource), so the
shipped EXE shows images offline.

Run:
    uv run --no-project --with pillow python scripts/bundle-images.py

Env:
    WARPSTORM_IMG_SIZE   max width/height (default 96)
    WARPSTORM_ASSETS     output dir (default ../assets)
"""
from __future__ import annotations

import io
import json
import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
CONFIGURATOR = HERE.parent
REPO = CONFIGURATOR.parents[1]
DATA = REPO / "battlesector-tools" / "src" / "data"
OUT = Path(os.environ.get("WARPSTORM_ASSETS", CONFIGURATOR / "assets"))
SIZE = int(os.environ.get("WARPSTORM_IMG_SIZE", "96"))

# Mirrors battlesector-tools/src/scripts/images.ts (FACTION_EMBLEMS / STAT_ICONS).
FACTION_EMBLEMS = {
    0: "3CCUI_side_column_factionSelect-BloodAngels",
    1: "3CCUI_side_column_factionSelect-Tyranids",
    2: "3CCUI_side_column_factionSelect-BattleSisters",
    3: "3CCUI_side_column_factionSelect-Necrons",
    4: "3CCUI_side_column_factionSelect-Necrons",
    5: "3CCUI_side_column_factionSelect-KhorneDaemons",
    7: "3CCUI_side_column_factionSelect-AstraMilitarum",
    8: "3CCUI_side_column_factionSelect-Orks",
    9: "3CCUI_side_column_factionSelect-Tau",
    10: "3CCUI_side_column_factionSelect-BlackLegion",
    11: "3CCUI_side_column_factionSelect-Ultramarines",
}
UI_ICONS = {
    "stat-health": "hudUI_panelIcon-HEALTH",
    "stat-armor": "hudUI_panelIcon-SHIELD",
    "stat-evasion": "hudUI_panelIcon-EVADE",
    "stat-movement": "hudUI_panelIcon-MOVE",
    "stat-ap": "hudUI_panelIcon-ACTION",
    "type-melee": "MeleeDamageIcon",
    "type-ranged": "BalisticDamageIcon",
}


def collect() -> list[tuple[str, str]]:
    units = json.loads((DATA / "units.json").read_text())
    weapons = json.loads((DATA / "weapons.json").read_text())
    images = json.loads((DATA / "image-urls.json").read_text())
    iu, iw = images.get("units", {}), images.get("weapons", {})

    tasks: dict[str, str] = {}
    for u in units:
        name = u.get("portrait")
        if name and name in iu:
            tasks[f"units/{name}.png"] = iu[name]["url"]
    for w in weapons:
        name = w.get("icon")
        if name and name in iw:
            tasks[f"weapons/{name}.png"] = iw[name]["url"]
    # In-game UI art: faction crests (by faction id) and HUD stat icons.
    ifac = images.get("factions", {})
    for fid, key in FACTION_EMBLEMS.items():
        if key in ifac:
            tasks[f"ui/faction-{fid}.png"] = ifac[key]["url"]
    for name, key in UI_ICONS.items():
        if key in iu:
            tasks[f"ui/{name}.png"] = iu[key]["url"]
    return sorted(tasks.items())


def is_placeholder(image: Image.Image) -> bool:
    """The game ships some icons as black text on white ("ASSAULT INTERCESSORS").
    Those are skipped so the UI falls back to the faction crest / weapon type icon."""
    rgba = image.convert("RGBA")
    px = rgba.get_flattened_data() if hasattr(rgba, "get_flattened_data") else rgba.getdata()
    px = list(px)
    white = sum(1 for r, g, b, a in px if a > 200 and r > 235 and g > 235 and b > 235)
    return white / max(1, len(px)) > 0.45


def fetch(rel: str, url: str) -> str:
    dest = OUT / rel
    if dest.exists():
        if not rel.startswith("ui/") and is_placeholder(Image.open(dest)):
            dest.unlink()
            return "placeholder"
        return "skip"
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Warpstorm bundler)"})
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read()
        image = Image.open(io.BytesIO(raw)).convert("RGBA")
        image.thumbnail((SIZE, SIZE), Image.LANCZOS)
        if not rel.startswith("ui/") and is_placeholder(image):
            return "placeholder"
        dest.parent.mkdir(parents=True, exist_ok=True)
        image.save(dest, "PNG", optimize=True)
        return "ok"
    except Exception as exc:  # noqa: BLE001
        return f"FAIL {rel}: {exc}"


def main() -> int:
    tasks = collect()
    print(f"bundling {len(tasks)} images -> {OUT} (max {SIZE}px)")
    ok = skip = fail = placeholder = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(fetch, rel, url) for rel, url in tasks]
        for i, fut in enumerate(as_completed(futures), 1):
            result = fut.result()
            if result == "ok":
                ok += 1
            elif result == "skip":
                skip += 1
            elif result == "placeholder":
                placeholder += 1
            else:
                fail += 1
                print("  " + result)
            if i % 50 == 0:
                print(f"  {i}/{len(tasks)} …")
    total = sum(f.stat().st_size for f in OUT.rglob("*.png"))
    print(f"done: {ok} new, {skip} existing, {placeholder} placeholder art skipped, {fail} failed; {total / 1048576:.1f} MB on disk")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
