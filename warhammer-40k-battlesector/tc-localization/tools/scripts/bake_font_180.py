#!/usr/bin/env python3
"""bake_font_180.py — bake Traditional-Chinese glyphs into a 1.8.0 TMP font.

1.8.0 moved the fonts into sharedassets2.assets and the startup/mapbuilder
bundles; the main CJK font ("NotoSansCJKjp-Regular SDF") is dynamic and only
covers the Simplified-Chinese glyphs the vanilla text uses. This script renders
the missing Traditional glyphs from Noto Sans CJK TC and appends them to a NEW
band at the top of the font's last atlas, then forces the font Static. Existing
glyphs are untouched (bottom-up TMP coordinates stay valid).

Usage:
  python bake_font_180.py <file> <font_pid> <atlas_index> [--dry-run]
"""
import math
import os
import sys

import freetype
import numpy as np
import UnityPy
from PIL import Image
from scipy.ndimage import distance_transform_edt
from UnityPy.helpers import TypeTreeHelper
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
from UnityPy.helpers.TypeTreeNode import TypeTreeNode

TypeTreeHelper.read_typetree_boost = False

GAME = "/mnt/d/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector"
DATA = os.path.join(GAME, "Warhammer 40K Battlesector_Data")
UNITY = "6000.0.62f1"
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OTF = os.environ.get(
    "MOD_FONT_OTF",
    os.path.join(REPO, "..", "..", ".agent_workspace", "fonts", "NotoSansCJKtc-Regular.otf"),
)
OVERSAMPLE = 4
GROW_STEP = 2048
MAX_ATLAS_H = 8192


def is_relevant(cp):
    return (
        0x3400 <= cp <= 0x9FFF
        or 0xF900 <= cp <= 0xFAFF
        or 0x3000 <= cp <= 0x303F
        or 0xFF00 <= cp <= 0xFFEF
        or 0x2010 <= cp <= 0x2027
        or cp == 0x221E
    )


def generate_sdf(face, cp, point_size, padding):
    render_size = point_size * OVERSAMPLE
    face.set_pixel_sizes(0, render_size)
    try:
        face.load_char(cp, 0x0006)  # FT_LOAD_RENDER | FT_LOAD_NO_HINTING
    except Exception:
        return None, 0, 0, None
    slot = face.glyph
    advance = slot.advance.x / 64.0 / OVERSAMPLE
    bearing_x = slot.bitmap_left / OVERSAMPLE
    bearing_y = slot.bitmap_top / OVERSAMPLE
    bmp = slot.bitmap
    bw, bh = bmp.width, bmp.rows
    metrics = {
        "m_HorizontalAdvance": float(round(advance)),
        "m_HorizontalBearingX": bearing_x,
        "m_HorizontalBearingY": bearing_y,
        "m_Width": bw / OVERSAMPLE,
        "m_Height": bh / OVERSAMPLE,
    }
    if bw == 0 or bh == 0:
        return None, 0, 0, metrics
    hi = np.frombuffer(bytes(bmp.buffer), dtype=np.uint8).reshape(bh, bw)
    binary = hi > 127
    pad_hi = padding * OVERSAMPLE
    binary = np.pad(binary, pad_hi, mode="constant", constant_values=False)
    dist_in = distance_transform_edt(binary)
    dist_out = distance_transform_edt(~binary)
    signed = np.where(binary, dist_in, -dist_out)
    spread = padding * OVERSAMPLE
    sdf = np.clip(128.0 + signed * (128.0 / spread), 0.0, 255.0).astype(np.uint8)
    tw = int(math.ceil(bw / OVERSAMPLE))
    th = int(math.ceil(bh / OVERSAMPLE))
    img = Image.fromarray(sdf, mode="L").resize((tw + 2 * padding, th + 2 * padding), Image.LANCZOS)
    return np.array(img, dtype=np.uint8), tw, th, metrics


class ShelfPacker:
    """Row-based packer for a fresh band; coordinates are bottom-up."""

    def __init__(self, width, y0, height):
        self.width = width
        self.y = y0
        self.cursor = 0
        self.shelf_h = 0
        self.top = y0 + height

    def place(self, w, h):
        if h > self.top - self.y:
            return None
        if self.cursor + w > self.width:
            self.y += self.shelf_h
            self.cursor = 0
            self.shelf_h = 0
            if self.y + h > self.top:
                return None
        x = self.cursor
        self.cursor += w
        self.shelf_h = max(self.shelf_h, h)
        return x, self.y

    def fits_after_reset(self, w, h):
        return h <= self.top - self.y


def tc_codepoints():
    manifest = os.path.join(REPO, ".build/text/manifest.txt")
    used = set()
    for line in open(manifest):
        _, binp = line.rstrip("\n").split("\t")
        data = open(binp, "rb").read()

        def rstr(off):
            n = int.from_bytes(data[off : off + 4], "little", signed=True)
            off += 4
            return data[off : off + n].decode("utf-8", "replace"), off + n

        _, off = rstr(0)
        off = (off + 3) // 4 * 4
        script, _ = rstr(off)
        for ch in script:
            if is_relevant(ord(ch)):
                used.add(ord(ch))
    return used


def main():
    path = sys.argv[1]
    font_pid = int(sys.argv[2])
    atlas_index = int(sys.argv[3])
    dry = "--dry-run" in sys.argv

    path = path if os.path.isabs(path) else os.path.join(DATA, path)
    gen = TypeTreeGenerator(UNITY)
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
    fobj = byid[font_pid]
    tree = fobj.read_typetree(node, check_read=False)

    name = tree["m_Name"]
    point_size = int(round(tree["m_FaceInfo"]["m_PointSize"]))
    padding = int(tree["m_AtlasPadding"])
    aw = int(tree["m_AtlasWidth"])
    ah = int(tree["m_AtlasHeight"])
    tex_pid = tree["m_AtlasTextures"][atlas_index]["m_PathID"]
    print(f"font {font_pid} {name!r} pt={point_size} pad={padding} atlas={aw}x{ah} tex={tex_pid}")

    if int(tree.get("m_AtlasPopulationMode", 0)) != 0:
        print("  forcing Static")
        tree["m_AtlasPopulationMode"] = 0

    baked = {int(c["m_Unicode"]) for c in tree["m_CharacterTable"]}
    missing = sorted(tc_codepoints() - baked)
    print(f"  missing TC codepoints: {len(missing)}")
    if not missing:
        return

    face = freetype.Face(OTF)
    rendered = []
    for cp in missing:
        sdf, cw, ch, metrics = generate_sdf(face, cp, point_size, padding)
        if sdf is None:
            continue
        rendered.append((cp, sdf, cw, ch, metrics))
    rendered.sort(key=lambda r: (-r[1].shape[0], -r[1].shape[1]))
    print(f"  rendered {len(rendered)}")

    cur_h = ah
    packer = ShelfPacker(aw, cur_h, GROW_STEP)
    cur_h += GROW_STEP
    placements = []
    for item in rendered:
        ph, pw = item[1].shape
        pos = packer.place(pw, ph)
        if pos is None and cur_h + GROW_STEP <= MAX_ATLAS_H:
            packer = ShelfPacker(aw, cur_h, GROW_STEP)
            cur_h += GROW_STEP
            pos = packer.place(pw, ph)
        if pos is None:
            break
        placements.append((item, pos[0], pos[1]))

    print(f"  placed {len(placements)} / {len(rendered)} final_atlas_h={cur_h}")
    if dry:
        return
    if len(placements) != len(rendered):
        raise SystemExit("ERROR: not all glyphs fit")

    tex = byid[tex_pid]
    td = tex.read_typetree()
    sd = td.get("m_StreamData") or {}
    streamed = bool(sd.get("path"))
    if streamed:
        # Streamed atlas (.resS inside the bundle/assets pair): use UnityPy's
        # Texture2D helper, which resolves and rewrites the stream.
        tex_obj = tex.read()
        img = np.array(tex_obj.image)
        plane = img[:, :, 3].copy()
        if plane.shape != (ah, aw):
            raise SystemExit(f"streamed atlas shape {plane.shape} != {ah}x{aw}")
    else:
        raw = td.get("image data")
        plane = np.frombuffer(bytes(raw)[: aw * ah], dtype=np.uint8).reshape(ah, aw).copy()

    if cur_h != ah:
        grown = np.zeros((cur_h, aw), dtype=np.uint8)
        grown[cur_h - ah :, :] = plane
        plane = grown
        ah = cur_h
        tree["m_AtlasHeight"] = ah

    next_index = max(int(g["m_Index"]) for g in tree["m_GlyphTable"]) + 1
    new_glyphs, new_chars, new_used = [], [], []
    for (cp, sdf, cw, ch, metrics), px, py_bu in placements:
        ph, pw = sdf.shape
        top = ah - py_bu - ph
        plane[top : top + ph, px : px + pw] = sdf
        new_glyphs.append(
            {
                "m_Index": next_index,
                "m_Metrics": {
                    k: metrics[k]
                    for k in (
                        "m_Width",
                        "m_Height",
                        "m_HorizontalBearingX",
                        "m_HorizontalBearingY",
                        "m_HorizontalAdvance",
                    )
                },
                "m_GlyphRect": {
                    "m_X": px + padding,
                    "m_Y": py_bu + padding,
                    "m_Width": cw,
                    "m_Height": ch,
                },
                "m_Scale": 1.0,
                "m_AtlasIndex": atlas_index,
                "m_ClassDefinitionType": 0,
            }
        )
        new_chars.append(
            {"m_ElementType": 1, "m_Unicode": cp, "m_GlyphIndex": next_index, "m_Scale": 1.0}
        )
        new_used.append({"m_X": px, "m_Y": py_bu, "m_Width": pw, "m_Height": ph})
        next_index += 1

    tree["m_GlyphTable"].extend(new_glyphs)
    tree["m_CharacterTable"].extend(new_chars)
    tree["m_CharacterTable"].sort(key=lambda c: int(c["m_Unicode"]))
    tree["m_GlyphTable"].sort(key=lambda g: int(g["m_Index"]))
    tree["m_UsedGlyphRects"] = (tree.get("m_UsedGlyphRects") or []) + new_used
    fobj.save_typetree(tree, node)

    td["m_Height"] = ah
    td["m_CompleteImageSize"] = aw * ah
    if streamed:
        out_img = np.zeros((ah, aw, 4), dtype=np.uint8)
        out_img[:, :, 3] = plane
        tex_obj.image = Image.fromarray(out_img, mode="RGBA")
        tex_obj.save()
    else:
        td["image data"] = plane.tobytes()
        tex.save_typetree(td)

    # Keep TMP material texture-size properties in sync when they exist.
    mat_pid = (tree.get("m_Material") or {}).get("m_PathID")
    if mat_pid and mat_pid in byid:
        mobj = byid[mat_pid]
        try:
            mt = mobj.read_typetree()
            saved = ((mt.get("m_SavedProperties") or {}).get("m_Floats")) or []
            changed = False
            for i, prop in enumerate(saved):
                if isinstance(prop, (tuple, list)) and len(prop) >= 2:
                    key, val = prop[0], prop[1]
                    if key == "_TextureHeight":
                        saved[i] = (key, float(ah))
                        changed = True
                    elif key == "_TextureWidth":
                        saved[i] = (key, float(aw))
                        changed = True
                elif hasattr(prop, "get"):
                    if prop.get("first") == "_TextureHeight":
                        prop["second"] = float(ah)
                        changed = True
                    elif prop.get("first") == "_TextureWidth":
                        prop["second"] = float(aw)
                        changed = True
            if changed:
                mobj.save_typetree(mt)
                print("  material texture-size properties updated")
        except Exception as e:
            print(f"  material update skipped: {e}")

    ext = os.path.splitext(path)[1].lower()
    if ext in (".bundle", ""):
        env.file.dataflags = type(env.file.dataflags)(579)
        env.file._block_info_flags = 64
        out = env.file.save(packer="original")
    else:
        out = env.file.save()
    with open(path, "wb") as f:
        f.write(out)
    print(f"  wrote {path}: {len(out):,} bytes")


if __name__ == "__main__":
    main()
