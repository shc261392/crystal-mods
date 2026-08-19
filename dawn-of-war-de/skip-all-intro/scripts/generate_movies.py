#!/usr/bin/env python3
"""Generate 0-byte replacement movies for the skip-all-intro mod.

The Definitive Edition engine plays intro movies via the `.lua` files that sit
next to each movie in `Engine/Movies/`, `DXP2/Movies/` and `DXP3/Movies/`.
Those `.lua` files declare the movie filename and an external audio stream, but
they carry no "enabled" flag — the engine triggers playback itself.

We cannot cleanly switch a movie off through the `.lua`, so instead we replace
each movie *binary* with an empty (0-byte) file. The engine errors out starting
the movie (verified strings in W40k.exe: "MOV -- Movie does not exist",
"MOV -- Error starting movie") and skips playback. Because the movie fails to
start, the `audio = "..."` declared in the `.lua` is never played either, so the
whole intro — picture and audio — is skipped.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Game-root-relative destinations (match the Vortex deployment paths).
MOVIES: list[str] = [
    # ── Engine/Movies ─────────────────────────────────────────────────────────
    "Engine/Movies/blur_intro.webm",
    "Engine/Movies/credits.avi",
    "Engine/Movies/dow_intro.avi",
    "Engine/Movies/relic_intro.webm",
    "Engine/Movies/rivalry.webm",
    "Engine/Movies/warhammer_intro.webm",
    "Engine/Movies/wxp_credits.avi",
    # ── DXP2 (Dark Crusade) ───────────────────────────────────────────────────
    "DXP2/Movies/dark_crusade_intro.webm",
    # ── DXP3 (Soulstorm) ──────────────────────────────────────────────────────
    "DXP3/Movies/soulstorm_intro.webm",
]


def main() -> int:
    mod_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("mod")
    for rel in MOVIES:
        out = mod_dir / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.touch(exist_ok=True)
        assert out.stat().st_size == 0, f"{out} is not empty"
        print(f"  {rel}  (0 bytes)")
    print(f"✓ generated {len(MOVIES)} empty replacement movies under {mod_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
