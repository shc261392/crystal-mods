#!/usr/bin/env python3
"""
edit_material_weight.py — Reduce the TMP `<b>` bold weight of the Traditional-
Chinese fonts by lowering `_WeightBold` on the shared Noto SDF materials in
sharedassets0.assets (pids 2, 8, 9 — used by fonts 782/783/785, the fonts TCFix
swaps garbled text to).

Writes edited MonoBehaviour bytes for each material; a separate FontTool `replace`
step swaps them into the .assets file (UnityPy cannot reserialize Unity 6 .assets):

  dotnet fonttool.dll replace <in.assets> <out.assets> <pid> mat_<pid>.bin

Usage:
  python3 tools/scripts/edit_material_weight.py <sharedassets0.assets> <out_subdir>

Env:
  MOD_WEIGHT_BOLD   new _WeightBold value (default 0.4; vanilla is 0.75)
"""

import os
import sys

from UnityPy.helpers import TypeTreeHelper
from UnityPy.streams import EndianBinaryWriter

import UnityPy

TypeTreeHelper.read_typetree_boost = False

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TARGET_PIDS = {2, 8, 9}
NEW_BOLD = float(os.environ.get("MOD_WEIGHT_BOLD", "0.4"))


def main():
    assets_path = sys.argv[1]
    out_dir = os.path.join(REPO, ".copilot_workspace", sys.argv[2])
    os.makedirs(out_dir, exist_ok=True)

    env = UnityPy.load(assets_path)
    for o in env.objects:
        if o.path_id not in TARGET_PIDS or o.type.name != "Material":
            continue
        node = o._get_typetree_node()
        td = o.read_typetree()
        floats = td["m_SavedProperties"]["m_Floats"]
        newfloats = []
        old = None
        for pair in floats:
            k, v = pair[0], pair[1]
            if k == "_WeightBold":
                old = v
                v = NEW_BOLD
            newfloats.append((k, v))
        td["m_SavedProperties"]["m_Floats"] = newfloats

        w = EndianBinaryWriter(endian="<")
        TypeTreeHelper.write_typetree(td, node, w)
        data = bytes(w.bytes)
        with open(os.path.join(out_dir, f"mat_{o.path_id}.bin"), "wb") as f:
            f.write(data)
        print(f"mat {o.path_id}: _WeightBold {old} -> {NEW_BOLD}  ({len(data)} bytes)")
    print("done")


if __name__ == "__main__":
    main()
