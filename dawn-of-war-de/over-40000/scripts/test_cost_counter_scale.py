"""Unit tests for the over-40000 generator invariants.

These run against the scratch SGA extraction tree
(`<workspace-root>/.copilot_workspace/extract`). They are skipped if the tree
is missing (CI / fresh checkout), because the generator patches real game data.

The tree is located in this order:
    1. `$DOW_EXTRACT_ROOT`  (set by `make test` from the Makefile's EXTRACT_ROOT)
    2. the nearest `.copilot_workspace/extract` walking up from this file
       (the mod lives at `<workspace>/dawn-of-war-de/over-40000`, so the scratch
       space is 3 directories up from the mod dir, not 2)

Critical invariant tested here:
    EVERY squad that is model-count scaled (eff > 0) MUST have every EBP it
    spawns cost-counter-scaled by that same factor. Otherwise a scaled unit
    ships at 5x cost/time (the Chimera/Hellhound/Sentinel bug).
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from generate_mod import ALL_MODULES, collect_scale_maps, squad_loadout_ebp_refs  # noqa: E402


def _resolve_extract_root() -> Path:
    """Return the extraction tree root (may not exist -> tests skip)."""
    env = os.environ.get("DOW_EXTRACT_ROOT")
    if env:
        return Path(env)
    for parent in Path(__file__).resolve().parents:
        cand = parent / ".copilot_workspace" / "extract"
        if cand.is_dir():
            return cand
    return Path(__file__).resolve().parents[3] / ".copilot_workspace" / "extract"


EXTRACT = _resolve_extract_root()


@unittest.skipUnless(EXTRACT.is_dir(), "game-data extraction tree not present")
class TestCostCounterScaleInvariant(unittest.TestCase):
    def _scale_maps(self):
        return collect_scale_maps(EXTRACT, 5, "scale",
                                  exclude_single_model=True,
                                  exclude_sp=False,
                                  descale_campaign_single=True)

    def test_every_scaled_squad_has_cost_counter_scaled_ebps(self):
        squad_map, ebp_map = self._scale_maps()
        violations = []
        checked = 0
        for module in ALL_MODULES:
            data_root = EXTRACT / module / "data"
            if not data_root.is_dir():
                continue
            for rgd in sorted(data_root.rglob("*.rgd")):
                if "sbps" not in str(rgd).replace("\\", "/"):
                    continue
                try:
                    from rgd_decode import extract_aegd
                    aegd = extract_aegd(rgd)
                except Exception:
                    continue
                eff = squad_map.get((module, rgd.name), 0)
                if eff <= 0:
                    continue
                for ebp in squad_loadout_ebp_refs(aegd):
                    divisor = ebp_map.get((module, ebp), 0)
                    checked += 1
                    if divisor != eff:
                        violations.append(
                            f"{module}/{rgd.name} (eff {eff}) -> EBP {ebp} "
                            f"divisor {divisor}"
                        )
        self.assertEqual(
            violations,
            [],
            f"{len(violations)} scaled squad(s) without matching cost "
            f"counter-scale (checked {checked} EBP refs):\n"
            + "\n".join(violations[:20]),
        )


if __name__ == "__main__":
    unittest.main()
