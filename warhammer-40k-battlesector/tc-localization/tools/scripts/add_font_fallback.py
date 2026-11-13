#!/usr/bin/env python3
"""add_font_fallback.py — make sure TMP fonts fall back to a full-CJK font.

Usage:
  python add_font_fallback.py <bundle|assets> <fallback_pid> <font_pid> [<font_pid> ...]
"""
import os
import sys

import UnityPy
from UnityPy.helpers import TypeTreeHelper
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
from UnityPy.helpers.TypeTreeNode import TypeTreeNode

TypeTreeHelper.read_typetree_boost = False
GAME = "/mnt/d/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector"
DATA = os.path.join(GAME, "Warhammer 40K Battlesector_Data")

path = sys.argv[1]
fallback = int(sys.argv[2])
pids = [int(x) for x in sys.argv[3:]]
path = path if os.path.isabs(path) else os.path.join(DATA, path)

gen = TypeTreeGenerator("6000.0.62f1")
gen.load_il2cpp(
    open(os.path.join(GAME, "GameAssembly.dll"), "rb").read(),
    open(os.path.join(DATA, "il2cpp_data", "Metadata", "global-metadata.dat"), "rb").read(),
)
base = gen.get_nodes("Unity.TextMeshPro", "TMPro.TMP_FontAsset")
node = TypeTreeNode.from_list(
    [TypeTreeNode(b.m_Level, b.m_Type, b.m_Name, 0, 0, m_MetaFlag=b.m_MetaFlag) for b in base]
)

env = UnityPy.load(path)
byid = {o.path_id: o for o in env.objects}
for pid in pids:
    o = byid[pid]
    t = o.read_typetree(node, check_read=False)
    fb = t.get("m_FallbackFontAssetTable") or []
    if any(int(f.get("m_PathID", 0)) == fallback for f in fb):
        print(f"{t['m_Name']}: already has fallback")
        continue
    fb.insert(0, {"m_FileID": 0, "m_PathID": fallback})
    t["m_FallbackFontAssetTable"] = fb
    o.save_typetree(t, node)
    print(f"{t['m_Name']}: fallback -> {fallback}")

if path.endswith(".bundle"):
    env.file.dataflags = type(env.file.dataflags)(579)
    env.file._block_info_flags = 64
    out = env.file.save(packer="original")
else:
    out = env.file.save()
with open(path, "wb") as f:
    f.write(out)
print(f"wrote {path}: {len(out):,} B")
