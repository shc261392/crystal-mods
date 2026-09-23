#!/usr/bin/env python3
"""Build the potato-marines aggressive FPS pak for Space Marine 2.

Packages override .sso files (engine quality-settings + corpse/gib collector
data) into dist/potato-marines.pak as a ZIP with Store compression — the
official mod-pak format (see ../docs/modding-tools.md §3). No editor or
.resource files required: these are pure data overrides (verified: the base
pak has no .resource siblings for these paths).

Values are forced BELOW the lowest in-game quality tier (swarm coeff 0.7,
gibs 23/43, ragdolls 5/15, corpses 20/40) to maximize FPS on a poor CPU.

Usage: python3 scripts/build_pak.py [--out dist/potato-marines.pak]
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

# ── aggressive values (edit to tune) ──────────────────────────────────────
SWARM_COEFF = 0.2
GIB_SOFT, GIB_HARD = 6, 12
RAG_SOFT, RAG_HARD = 0, 2
RAG_FREEZE = 0
CORPSES_MIN, CORPSES_MAX = 3, 8
GORE_MIN, GORE_MAX = 6, 12

E = "\r\n"  # the engine's .sso text format uses CRLF


def _swarm_preset() -> str:
    mod = f"         SpawnExtensionModule   =   {{{E}            flockSpawnCoefficent   =   {SWARM_COEFF}{E}            crawlingSpawnCoefficent   =   {SWARM_COEFF}{E}            battlegroundSpawnCoefficent   =   {SWARM_COEFF}{E}         }}"
    low = f"   LOW   =   {{{E}      modules   =   {{{E}{mod}{E}      }}{E}      __type   =   \"QualitySettingsModules\"{E}   }}"
    high = f"   HIGH   =   {{{E}      modules   =   {{{E}{mod}{E}      }}{E}      __type   =   \"QualitySettingsModules\"{E}   }}"
    return f"swarmPresets   =   {{{E}{low}{E}{high}{E}}}{E}__type   =   \"QualitySettingsPresetsBase\"{E}"


def _physics_preset() -> str:
    gore = f"            goreGibSoftLimit   =   {GIB_SOFT}{E}            goreGibHardLimit   =   {GIB_HARD}"
    phys = (
        "            qualityMorpheme   =   \"Debris\""
        + E
        + "            qualityPhysObjecs   =   \"Debris\""
        + E
        + "            qualityGoreGib   =   \"Debris\""
    )
    rag = (
        f"            ragdollSoftLimit   =   {RAG_SOFT}"
        + E
        + f"            ragdollHardLimit   =   {RAG_HARD}"
        + E
        + f"            timerRagdollFreezeAfterLastCdt   =   {RAG_FREEZE}"
    )
    modules = "".join(
        f"         {name}   =   {{{E}{body}{E}         }}{E}" for name, body in (("GoreModule", gore), ("PhysicsModule", phys), ("RagdollModule", rag))
    )
    low = f"   LOW   =   {{{E}      modules   =   {{{E}{modules}      }}{E}      __type   =   \"QualitySettingsModules\"{E}   }}"
    high = (
        f"   HIGH   =   {{{E}      modules   =   {{{E}         GoreModule   =   {{{E}         }}{E}         PhysicsModule   =   {{{E}         }}{E}         RagdollModule   =   {{{E}         }}{E}      }}{E}      __type   =   \"QualitySettingsModules\"{E}   }}"
    )
    return f"physicsPresets   =   {{{E}{low}{E}{high}{E}}}{E}__type   =   \"QualitySettingsPresetsBase\"{E}"


def _cloth_preset() -> str:
    tier = "      modules   =   {" + E + "         ClothModule   =   {" + E + "            clothQuality   =   \"LOW\"" + E + "         }" + E + "      }" + E + "      __type   =   \"QualitySettingsModules\""
    return "clothPresets   =   {" + E + "   LOW   =   {" + E + tier + E + "   }" + E + "   NORMAL   =   {" + E + tier + E + "   }" + E + "   HIGH   =   {" + E + tier + E + "   }" + E + "}" + E + "__type   =   \"QualitySettingsPresetsBase\"" + E


FILES: dict[str, str] = {
    "ssl/main/user/quality_settings/quality_settings_presets/quality_settings_presets_swarm.sso": _swarm_preset(),
    "ssl/main/user/quality_settings/quality_settings_presets/quality_settings_presets_physics.sso": _physics_preset(),
    "ssl/main/user/quality_settings/quality_settings_presets/quality_settings_presets_cloth.sso": _cloth_preset(),
    "ssl/main/user/quality_settings/quality_settings_modules/cloth_module.sso": (
        'clothQuality   =   "LOW"' + E + '__type   =   "QualitySettingsModuleBase"' + E
    ),
    "ssl/main/user/quality_settings/quality_settings_modules/gore_module.sso": (
        f"goreGibSoftLimit   =   {GIB_SOFT}" + E + f"goreGibHardLimit   =   {GIB_HARD}" + E + '__type   =   "QualitySettingsModuleBase"' + E
    ),
    "ssl/main/user/quality_settings/quality_settings_modules/ragdoll_module.sso": (
        f"ragdollSoftLimit   =   {RAG_SOFT}"
        + E
        + f"ragdollHardLimit   =   {RAG_HARD}"
        + E
        + f"timerRagdollFreezeAfterLastCdt   =   {RAG_FREEZE}"
        + E
        + '__type   =   "QualitySettingsModuleBase"'
        + E
    ),
    "ssl/main/user/quality_settings/quality_settings_modules/physics_module.sso": (
        'qualityMorpheme   =   "Debris"'
        + E
        + 'qualityPhysObjecs   =   "Debris"'
        + E
        + 'qualityGoreGib   =   "Debris"'
        + E
        + '__type   =   "QualitySettingsModuleBase"'
        + E
    ),
    "ssl/main/user/quality_settings/quality_settings_modules/spawn_extension_module.sso": (
        f"flockSpawnCoefficent   =   {SWARM_COEFF}"
        + E
        + f"crawlingSpawnCoefficent   =   {SWARM_COEFF}"
        + E
        + f"battlegroundSpawnCoefficent   =   {SWARM_COEFF}"
        + E
        + '__type   =   "QualitySettingsModuleBase"'
        + E
    ),
    "ssl/spawn_system/despawn/corpse_collector.sso": (
        f"minCorpsesOnScene   =   {CORPSES_MIN}" + E + f"maxCorpsesOnScene   =   {CORPSES_MAX}" + E + '__type   =   "object"' + E
    ),
    "ssl/spawn_system/despawn/npc_corpse_collector.sso": (
        f"minCorpsesOnScene   =   {CORPSES_MIN}"
        + E
        + f"maxCorpsesOnScene   =   {CORPSES_MAX}"
        + E
        + "allowMaxValueOverflow   =   True"
        + E
        + "updateIntervalSec   =   0.2"
        + E
        + "maxCollectCountPerUpdate   =   5"
        + E
        + '__type   =   "CorpseCollector"'
        + E
    ),
    "ssl/spawn_system/despawn/swarm_actorless_corpse_collector.sso": (
        f"minCorpses   =   {CORPSES_MIN}" + E + "maxCollectCountPerUpdate   =   5" + E + '__type   =   "object"' + E
    ),
    "ssl/spawn_system/actorless_gore_collector.sso": (
        "updateInterval   =   1"
        + E
        + "maxCollectCountPerUpdate   =   -1"
        + E
        + f"minGibs   =   {GORE_MIN}"
        + E
        + f"maxGibs   =   {GORE_MAX}"
        + E
        + '__type   =   "object"'
        + E
    ),
}


def build(out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_STORED) as pak:
        for name, content in sorted(FILES.items()):
            pak.writestr(name, content.encode("utf-8"))
    print(f"wrote {out} ({out.stat().st_size} bytes, {len(FILES)} files, store/zip)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="dist/potato-marines.pak")
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    build(root / args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())