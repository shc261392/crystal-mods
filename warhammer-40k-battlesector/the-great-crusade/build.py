#!/usr/bin/env python3
"""the-great-crusade — builder (confirmed data levers only).

Single tuned config for the Crusade / Planetary Supremacy (Warzone) mode. All
parameters live in code (CONFIG below); the Makefile invokes one target per base.

Only edits that were CONFIRMED to take effect in-game are applied:
  * expNeededToLevelUp -> flat +STEP per level, LEVEL_CAP-1 thresholds
      => fast, steady leveling and a raised level cap (more upgrade picks).
  * CardDropProbabilities -> Rare & Legendary drop rates flattened high
      => top-tier ("gold") upgrade cards are available at every level, so the
         raised cap doesn't dilute card quality (rarity is keyed to level/maxLevel).
  * rewardModifiers[*].levelMul -> extended to the new cap (harmless safety).

Card effect values are read from the hand-editable ``cards.json`` (regenerate
defaults with ``make export-cards``): every build overrides each upgrade card's
stat modifiers from that file. See cards.py.

Deliberately NOT touched (proven hardcoded / economy-table-driven in 1.7.7, i.e.
editing them does nothing): xpMultiplier, UpgradeRerollCost, clusterRewardValue,
BaseSkipReward, and the WarzoneMapConfig starting requisition / HQ-token values.

Usage (invoked by the Makefile):
    python build.py <base_kind>     # 'standalone' or 'tccompat'
"""
from __future__ import annotations

import json
import os
import sys
import zipfile
from pathlib import Path

import UnityPy

import cards as cards_mod

VERSION = "0.1.0"

# ----------------------------------------------------------------------------
# Tuned config (build-variant-as-code).
# ----------------------------------------------------------------------------
LEVEL_CAP = 15          # max crusade level (vanilla 8)
STEP = 100              # flat XP per level: thresholds 100, 200, 300, ...
TOP_TIER_RARITIES = (2, 3)   # Rare, Legendary
# Card rarity is keyed to level/maxLevel (0..1). Force the top-tier drop rate to
# 1.0 once a unit is at/above this progression, i.e. the *upper* levels — vanilla
# rarity below it. 0.5 targets level ~8 of 15 (7/14 = 0.5). Levels 1-7 stay vanilla.
RARITY_FULL_FROM = 0.5

# ----------------------------------------------------------------------------
# Paths (I/O plumbing).
# ----------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
STAGE = HERE / ".copilot_workspace" / "stage"
DIST = HERE / "dist"
CARDS_JSON = HERE / "cards.json"
CARDS_NONPLAYER_JSON = HERE / "cards-nonplayer.json"
VANILLA_CARDS_JSON = HERE / "cards-vanilla.json"

_GAME_DIR = os.environ.get(
    "BS_GAME_DIR",
    "/mnt/d/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector",
)
VANILLA_BASE = Path(
    os.environ.get(
        "BS_VANILLA_BUNDLE",
        f"{_GAME_DIR}/Warhammer 40K Battlesector_Data/StreamingAssets/"
        "startup_assets_all.bundle.vortex_backup",
    )
)
# Independently-stored pristine 1.7.7 bundle; the authoritative source for the
# frozen cards-vanilla.json reference. Verified byte-for-byte identical to the
# Vortex .vortex_backup across all 55 cards. Falls back to VANILLA_BASE.
VANILLA_REF_BUNDLE = Path(
    os.environ.get(
        "BS_VANILLA_REF",
        str(
            REPO
            / ".copilot_workspace/battlesector-data/emperors-lasgun/vanilla/"
            "startup_assets_all.bundle"
        ),
    )
)
TC_BASE = REPO / (
    "warhammer-40k-battlesector/tc-localization/translation/zh-TW/dist/"
    "startup_assets_all.bundle"
)
BASES = {"standalone": VANILLA_BASE, "tccompat": TC_BASE}
BUNDLE_REL = "Warhammer 40K Battlesector_Data/StreamingAssets/startup_assets_all.bundle"


def flat_thresholds(cap: int) -> list[int]:
    return [STEP * (i + 1) for i in range(cap - 1)]


def _bf(d: dict, needle: str) -> str | None:
    for k in d:
        if needle in k:
            return k
    return None


# vanilla-ish drop value just below the boundary (keeps early levels ~normal)
_LOW_BELOW = {2: 0.15, 3: 0.0}  # Rare, Legendary


def _step_curve(template: dict, rarity: int) -> list:
    """Rebuild a DropRate curve: ~vanilla-low until RARITY_FULL_FROM, then 1.0."""
    low = _LOW_BELOW.get(rarity, 0.0)
    points = [(0.0, 0.0), (RARITY_FULL_FROM - 0.01, low), (RARITY_FULL_FROM, 1.0), (1.0, 1.0)]
    out = []
    for time, value in points:
        kf = dict(template)
        kf["time"] = time
        kf["value"] = value
        kf["inSlope"] = 0.0
        kf["outSlope"] = 0.0
        kf["inWeight"] = 0.0
        kf["outWeight"] = 0.0
        kf["weightedMode"] = 0
        out.append(kf)
    return out


def apply_edits(env) -> list[str]:
    changes: list[str] = []
    thresholds = flat_thresholds(LEVEL_CAP)
    for o in env.objects:
        if o.type.name != "MonoBehaviour":
            continue
        try:
            t = o.read_typetree()
        except Exception:  # noqa: BLE001
            continue
        if not isinstance(t, dict):
            continue
        rc = t.get("RewardConfig")
        if not (isinstance(rc, dict) and _bf(rc, "expNeededToLevelUp")):
            continue

        # 1) leveling curve + cap
        exp_bf = _bf(rc, "expNeededToLevelUp")
        old_exp = list(rc[exp_bf])
        rc[exp_bf] = list(thresholds)
        changes.append(
            f"expNeededToLevelUp {old_exp} -> {rc[exp_bf]} (flat +{STEP}, cap {LEVEL_CAP})"
        )

        # 2) card rarity: top-tier (Rare/Legendary) guaranteed at the upper levels
        cdp = _bf(rc, "CardDropProbabilities")
        if cdp:
            for entry in rc[cdp]:
                rarity = entry.get(_bf(entry, "Rarity"))
                dr = _bf(entry, "DropRate")
                if rarity in TOP_TIER_RARITIES and dr:
                    curve = entry[dr].get("m_Curve")
                    if isinstance(curve, list) and curve:
                        entry[dr]["m_Curve"] = _step_curve(curve[0], rarity)
            changes.append(
                f"CardDropProbabilities: rarities {TOP_TIER_RARITIES} -> 1.0 from "
                f"progression {RARITY_FULL_FROM} (level ~8+)"
            )

        # 3) extend levelMul to the new cap (safety)
        rm = _bf(rc, "rewardModifiers")
        if rm:
            for zone in rc[rm]:
                lm = zone.get("levelMul")
                if isinstance(lm, list) and lm:
                    while len(lm) < LEVEL_CAP + 1:
                        clone = dict(lm[-1])
                        clone["name"] = f"Level {len(lm) + 1} (extended)"
                        lm.append(clone)
            changes.append(f"levelMul extended to {LEVEL_CAP + 1} rows/zone")

        o.save_typetree(t)
    return changes


def verify(bundle_path: Path) -> None:
    env = UnityPy.load(str(bundle_path))
    for o in env.objects:
        if o.type.name != "MonoBehaviour":
            continue
        try:
            t = o.read_typetree()
        except Exception:  # noqa: BLE001
            continue
        if not isinstance(t, dict):
            continue
        rc = t.get("RewardConfig")
        if isinstance(rc, dict) and _bf(rc, "expNeededToLevelUp"):
            exp = list(rc[_bf(rc, "expNeededToLevelUp")])
            assert exp == flat_thresholds(LEVEL_CAP), f"exp: {exp}"
            cdp = rc[_bf(rc, "CardDropProbabilities")]
            drops = {}
            for e in cdp:
                r = e.get(_bf(e, "Rarity"))
                vals = [kf["value"] for kf in e[_bf(e, "DropRate")]["m_Curve"]]
                drops[r] = vals
            for r in TOP_TIER_RARITIES:
                # step curve: starts low, ends at 1.0 (guaranteed at high levels)
                assert drops[r][0] == 0.0 and drops[r][-1] == 1.0, f"rarity {r}: {drops[r]}"
            lens = [len(z.get("levelMul", [])) for z in rc[_bf(rc, "rewardModifiers")]]
            assert all(n >= LEVEL_CAP + 1 for n in lens), f"levelMul: {lens}"
            top = {r: drops[r] for r in TOP_TIER_RARITIES}
            print(
                f"  verify OK: cap={len(exp) + 1} thresholds={exp[:3]}... "
                f"topTierDrops={top} levelMul={lens}"
            )
            return
    raise SystemExit("verify: RewardConfig not found in output")


def modinfo(base_kind: str) -> dict:
    tc = base_kind == "tccompat"
    return {
        "id": "the-great-crusade" + ("-tccompat" if tc else ""),
        "name": "The Great Crusade" + (" (TC-compatible)" if tc else ""),
        "game": "warhammer-40k-battlesector",
        "version": VERSION,
        "author": "crystal-mods",
        "category": "Gameplay",
        "platforms": ["windows", "linux-proton"],
        "supportedVersions": ["1.7.7"],
        "engine": "Unity 6000.0.62f1 (IL2CPP)",
        "description": (
            f"Crusade / Planetary Supremacy tuning: flat {STEP} XP per level up to "
            f"level {LEVEL_CAP} (more upgrade picks), and top-tier (Rare/Legendary) "
            "upgrade cards guaranteed at the upper levels (~8+)."
        )
        + (
            " Built on the Traditional Chinese localization bundle (keeps TC fonts)."
            if tc
            else " Standalone build on the vanilla bundle."
        ),
        "mode": "Crusade / Planetary Supremacy (Warzone)",
        "changes": {
            "maxLevel": LEVEL_CAP,
            "expNeededToLevelUp": flat_thresholds(LEVEL_CAP),
            "cardRarity": f"Rare & Legendary drop rate = 1.0 from level ~8+ "
            f"(progression >= {RARITY_FULL_FROM})",
        },
        "deployFiles": [BUNDLE_REL],
        "conflicts": [
            "Any mod replacing "
            "Warhammer 40K Battlesector_Data/StreamingAssets/startup_assets_all.bundle "
            "(e.g. Traditional Chinese Localization). Use the TC-compatible build "
            "and let it win the conflict if you also run TC localization."
        ],
    }


def build(base_kind: str) -> Path:
    if base_kind not in BASES:
        raise SystemExit(f"unknown base {base_kind!r}; choices: {list(BASES)}")
    base = BASES[base_kind]
    if not base.exists():
        raise SystemExit(
            f"base bundle not found: {base}\n"
            "For 'standalone', point BS_VANILLA_BUNDLE at a pristine "
            "startup_assets_all.bundle (Steam -> Verify integrity of game files, or "
            "a Vortex .vortex_backup). For 'tccompat', build the TC localization "
            "mod first so its dist bundle exists."
        )

    print(f"[{base_kind}] base={base}")
    env = UnityPy.load(str(base))
    for c in apply_edits(env):
        print("   *", c)

    if VANILLA_CARDS_JSON.exists() and base_kind == "standalone":
        drift = cards_mod.check_vanilla(env, cards_mod.load_cards(VANILLA_CARDS_JSON))
        if drift:
            print(f"   ! WARNING: base bundle differs from cards-vanilla.json ({len(drift)} field(s)):")
            for m in drift[:8]:
                print(f"       {m}")
            print("     -> the base may not be pristine vanilla; verify BS_VANILLA_BUNDLE.")
        else:
            print("   * base bundle matches cards-vanilla.json (pristine vanilla)")

    card_docs = []
    for label, path in (("cards.json", CARDS_JSON), ("cards-nonplayer.json", CARDS_NONPLAYER_JSON)):
        if path.exists():
            card_docs.append(cards_mod.load_cards(path))
        else:
            print(f"   * {label} not found — those card effects left vanilla")
    if card_docs:
        card_changes = cards_mod.apply_card_effects(env, *card_docs)
        print(f"   * card effects: {len(card_changes)} card(s) edited")

    stage = STAGE / base_kind
    bundle_out = stage / BUNDLE_REL
    bundle_out.parent.mkdir(parents=True, exist_ok=True)
    with open(bundle_out, "wb") as f:
        f.write(env.file.save(packer="original"))

    verify(bundle_out)

    (stage / "modinfo.json").write_text(
        json.dumps(modinfo(base_kind), indent=2, ensure_ascii=False)
    )
    readme = HERE / "README.md"
    if readme.exists():
        (stage / "README.md").write_text(readme.read_text())

    DIST.mkdir(parents=True, exist_ok=True)
    suffix = "-tccompat" if base_kind == "tccompat" else ""
    out_zip = DIST / f"the-great-crusade{suffix}-v{VERSION}.zip"
    if out_zip.exists():
        out_zip.unlink()
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(stage.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(stage).as_posix())
    print(f"  packaged -> {out_zip.name} ({out_zip.stat().st_size / 1048576:.1f} MB)")
    return out_zip


def export_cards_json(force: bool) -> int:
    """Regenerate cards.json from the vanilla (standalone) base bundle."""
    base = BASES["standalone"]
    if not base.exists():
        raise SystemExit(
            f"vanilla base bundle not found: {base}\n"
            "Set BS_VANILLA_BUNDLE / BS_GAME_DIR to a pristine "
            "startup_assets_all.bundle to export card defaults."
        )
    print(f"[export-cards] base={base}")
    env = UnityPy.load(str(base))
    cards_mod.write_cards(env, CARDS_JSON, player=True, force=force)
    cards_mod.write_cards(env, CARDS_NONPLAYER_JSON, player=False, force=force)

    # frozen vanilla reference (all 55 cards) from the authoritative pristine bundle
    ref_bundle = VANILLA_REF_BUNDLE if VANILLA_REF_BUNDLE.exists() else base
    print(f"[export-cards] vanilla reference base={ref_bundle}")
    ref_env = UnityPy.load(str(ref_bundle))
    cards_mod.write_cards(ref_env, VANILLA_CARDS_JSON, player=None, force=True)
    return 0


def apply_cost_policy_cmd() -> int:
    """Rewrite costMultiplier in the card files: vanilla cost - per-tier reduction."""
    if not VANILLA_CARDS_JSON.exists():
        raise SystemExit(
            f"{VANILLA_CARDS_JSON.name} not found — run `make export-cards` first "
            "to generate the vanilla reference."
        )
    vanilla = cards_mod.load_cards(VANILLA_CARDS_JSON)
    vanilla_by_id = {int(c["id"]): c for c in vanilla.get("cards", [])}
    deltas = ", ".join(f"{k} -{v:g}" for k, v in cards_mod.TIER_COST_DELTA.items())
    print(f"[cost-policy] costMultiplier = vanilla - ({deltas})")
    for path in (CARDS_JSON, CARDS_NONPLAYER_JSON):
        if not path.exists():
            print(f"   * {path.name} not found — skipped")
            continue
        doc = cards_mod.load_cards(path)
        n = cards_mod.apply_cost_policy(doc, vanilla_by_id)
        path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
        print(f"   * {path.name}: updated cost on {n} card(s)")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[1] == "export-cards":
        return export_cards_json(force="--force" in argv[2:])
    if len(argv) >= 2 and argv[1] == "cost-policy":
        return apply_cost_policy_cmd()
    if len(argv) != 2 or argv[1] not in BASES:
        print(__doc__)
        print("bases:", ", ".join(BASES))
        print("also: export-cards [--force]  (regenerate card files + vanilla ref)")
        print("      cost-policy             (set costs = vanilla - per-tier reduction)")
        return 2
    build(argv[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
