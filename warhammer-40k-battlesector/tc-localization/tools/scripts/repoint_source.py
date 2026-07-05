#!/usr/bin/env python3
"""Repoint a dynamic TMP font's source font to the embedded NotoSansCJK Font so
it dynamically generates CJK glyphs at runtime. Serializes the modified font
object bytes for injection via AssetsTools.NET.

Usage: python3 repoint_source.py <bundle> <font_pid> <notocjk_font_pid> <out_bin>
"""
import sys, os
import UnityPy
from UnityPy.helpers import TypeTreeHelper
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
from UnityPy.helpers.TypeTreeNode import TypeTreeNode
from UnityPy.streams import EndianBinaryWriter

TypeTreeHelper.read_typetree_boost = False
GR = "/mnt/d/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector"

bundle = sys.argv[1]; font_pid = int(sys.argv[2]); noto_pid = int(sys.argv[3]); out_bin = sys.argv[4]
NOTO_GUID = "21c853a80b54e694cb38e92c3bff9e61"

gen = TypeTreeGenerator("6000.0.62f1"); gen.load_local_game(GR)
b = gen.get_nodes("Unity.TextMeshPro", "TMPro.TMP_FontAsset")
node = TypeTreeNode.from_list([TypeTreeNode(n.m_Level,n.m_Type,n.m_Name,0,0,m_MetaFlag=n.m_MetaFlag) for n in b])

env = UnityPy.load(bundle)
o = next(x for x in env.objects if x.path_id == font_pid)
t = o.read_typetree(node, check_read=False)
print("before: PopMode", t.get("m_AtlasPopulationMode"), "source", t.get("m_SourceFontFile"), "guid", (t.get("m_CreationSettings") or {}).get("sourceFontFileGUID"))

# Ensure dynamic population so runtime glyph generation is enabled.
t["m_AtlasPopulationMode"] = 1
t["m_SourceFontFile"] = {"m_FileID": 0, "m_PathID": noto_pid}
cs = t.get("m_CreationSettings")
if isinstance(cs, dict):
    cs["sourceFontFileGUID"] = NOTO_GUID

w = EndianBinaryWriter(endian="<")
TypeTreeHelper.write_typetree(t, node, w)
data = bytes(w.bytes)
os.makedirs(os.path.dirname(out_bin), exist_ok=True)
with open(out_bin, "wb") as f:
    f.write(data)
print("after: PopMode", t["m_AtlasPopulationMode"], "source", t["m_SourceFontFile"])
print(f"wrote {out_bin}: {len(data):,} bytes")
