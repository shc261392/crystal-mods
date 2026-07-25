#!/usr/bin/env python3
"""
rebuild_font_tc.py — In-place Traditional-Chinese glyph re-render (approach A).

The earlier bakes rendered CJK glyphs from NotoSansCJKjp (Japanese letterforms).
This re-renders every CJK codepoint in a static TMP font from a Traditional-
Chinese OTF (NotoSansCJKtc) and blits each new SDF into the glyph's EXISTING
atlas rectangle (resized to fit when the TC bounding box differs). It does NOT
repack, grow, or change the atlas dimensions, and it does NOT touch the font's
CharacterTable / GlyphTable / metrics or the material — only CJK atlas pixels
change. This is safe for atlases shared by multiple fonts (e.g. 782 + 785 share
atlas 295) because the glyph layout is preserved exactly.

The target font must already be Static (m_AtlasPopulationMode == 0); the shotgun
build made 782/783/785/3644 static, so the pre-baked CharacterTable is used at
runtime and these atlas edits take effect.

Outputs (consumed by FontTool `replace`, texture only):
  OUT_DIR/tex_<texpid>.bin      new atlas Texture2D bytes   (inline atlas)
  OUT_DIR/<assets>.resS         edited sidecar              (.resS atlas)

Usage:
  python3 tools/scripts/rebuild_font_tc.py <assets_path> <font_pid> <out_subdir>

Env:
  MOD_TC_OTF   Traditional-Chinese OTF (default: NotoSansCJKtc-Regular.otf)
"""

import json
import os
import sys

import freetype
import numpy as np
from PIL import Image
from UnityPy.helpers import TypeTreeHelper
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
from UnityPy.helpers.TypeTreeNode import TypeTreeNode
from UnityPy.streams import EndianBinaryWriter

import UnityPy
from bake_font_generic import (
    GAME_ROOT,
    UNITY_VERSION,
    generate_sdf,
    get_image_bytes,
    is_relevant,
)

TypeTreeHelper.read_typetree_boost = False

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TC_OTF = os.environ.get(
    "MOD_TC_OTF",
    os.path.join(REPO, ".copilot_workspace", "fonts", "NotoSansCJKtc-Regular.otf"),
)


def main():
    assets_path = sys.argv[1]
    font_pid = int(sys.argv[2])
    out_sub = sys.argv[3]
    out_dir = os.path.join(REPO, ".copilot_workspace", out_sub)
    os.makedirs(out_dir, exist_ok=True)

    gen = TypeTreeGenerator(UNITY_VERSION)
    gen.load_local_game(GAME_ROOT)
    base = gen.get_nodes("Unity.TextMeshPro", "TMPro.TMP_FontAsset")
    node = TypeTreeNode.from_list(
        [TypeTreeNode(b.m_Level, b.m_Type, b.m_Name, 0, 0, m_MetaFlag=b.m_MetaFlag) for b in base]
    )

    env = UnityPy.load(assets_path)
    fobj = next(o for o in env.objects if o.path_id == font_pid)
    tree = fobj.read_typetree(node, check_read=False)

    point_size = int(round(tree["m_FaceInfo"]["m_PointSize"]))
    padding = int(tree["m_AtlasPadding"])
    aw, ah = int(tree["m_AtlasWidth"]), int(tree["m_AtlasHeight"])
    tex_pid = (tree["m_AtlasTextures"] or [])[0]["m_PathID"]
    pop = int(tree.get("m_AtlasPopulationMode", 0))
    print(
        f"font {font_pid}: {tree.get('m_Name')} pointSize={point_size} pad={padding} "
        f"atlas={aw}x{ah} texpid={tex_pid} pop={pop} chars={len(tree['m_CharacterTable'])}"
    )
    if pop != 0:
        print("  WARNING: font is DYNAMIC (pop!=0); in-place atlas edits may be ignored")

    # ---- load current atlas (inline vs .resS) --------------------------------
    tex = next(o for o in env.objects if o.path_id == tex_pid)
    td = tex.read_typetree()
    sd = td.get("m_StreamData") or {}
    inline = not sd.get("path")
    if inline:
        buf = get_image_bytes(td)
        assert len(buf) >= aw * ah, f"inline image {len(buf)} < {aw * ah}"
        atlas = np.frombuffer(bytes(buf[: aw * ah]), dtype=np.uint8).reshape(ah, aw).copy()
    else:
        ress_path = (
            assets_path + ".resS"
            if os.path.isfile(assets_path + ".resS")
            else os.path.join(os.path.dirname(assets_path), sd["path"])
        )
        off = int(sd["offset"])
        with open(ress_path, "rb") as f:
            ress = bytearray(f.read())
        atlas = (
            np.frombuffer(bytes(ress[off : off + aw * ah]), dtype=np.uint8).reshape(ah, aw).copy()
        )

    glyphs_by_idx = {int(g["m_Index"]): g for g in tree["m_GlyphTable"]}
    orig_atlas = atlas.copy()  # keep pre-edit pixels for the verification montage

    face = freetype.Face(TC_OTF)
    replaced = resized = missing_tc = skipped_bounds = 0
    for ch in tree["m_CharacterTable"]:
        cp = int(ch["m_Unicode"])
        if not is_relevant(cp):
            continue
        g = glyphs_by_idx.get(int(ch["m_GlyphIndex"]))
        if g is None:
            continue
        rect = g["m_GlyphRect"]
        gw, gh = int(rect["m_Width"]), int(rect["m_Height"])
        if gw == 0 or gh == 0:
            continue

        sdf, tw, th, _ = generate_sdf(face, cp, point_size, padding)
        if sdf is None:
            missing_tc += 1  # TC font lacks this glyph — keep existing
            continue

        # Blit ONLY the exact m_GlyphRect inner region. Glyph rects never overlap,
        # so this can never corrupt a neighbour. (Writing the padded box would, at
        # small point sizes where cells are packed tighter than 2*padding.) The
        # existing padding-zone SDF falloff is left in place.
        inner = sdf[padding : sdf.shape[0] - padding, padding : sdf.shape[1] - padding]
        if inner.shape[0] <= 0 or inner.shape[1] <= 0:
            missing_tc += 1
            continue
        if inner.shape != (gh, gw):
            inner = np.array(
                Image.fromarray(inner).resize((gw, gh), Image.LANCZOS),
                dtype=np.uint8,
            )
            resized += 1
        mx, my = int(rect["m_X"]), int(rect["m_Y"])
        if mx < 0 or my < 0 or mx + gw > aw or my + gh > ah:
            skipped_bounds += 1
            continue
        atlas[my : my + gh, mx : mx + gw] = np.flipud(inner)
        replaced += 1

    print(
        f"CJK glyphs: re-rendered_TC={replaced} resized={resized} "
        f"missing_in_TC={missing_tc} skipped_oob={skipped_bounds}"
    )

    # ---- optional before/after montage for visual verification ---------------
    verify_chars = os.environ.get("MOD_VERIFY_CHARS", "")
    if verify_chars:
        char_to_rect = {}
        for ch in tree["m_CharacterTable"]:
            g = glyphs_by_idx.get(int(ch["m_GlyphIndex"]))
            if g:
                char_to_rect[int(ch["m_Unicode"])] = g["m_GlyphRect"]
        scale = 4
        cells = []
        for c in verify_chars:
            r = char_to_rect.get(ord(c))
            if not r:
                continue
            mx, my = int(r["m_X"]), int(r["m_Y"])
            gw, gh = int(r["m_Width"]), int(r["m_Height"])
            if gw <= 0 or gh <= 0:
                continue
            old_c = np.flipud(orig_atlas[my : my + gh, mx : mx + gw])
            new_c = np.flipud(atlas[my : my + gh, mx : mx + gw])
            cells.append((old_c, new_c))
        if cells:
            cw = max(c[0].shape[1] for c in cells)
            chh = max(c[0].shape[0] for c in cells)
            pad = 4
            row_h = (chh + pad) * scale
            col_w = (cw + pad) * scale
            montage = Image.new("L", (col_w * 2 + 20, row_h * len(cells)), 40)
            for i, (old_c, new_c) in enumerate(cells):
                for j, cell in enumerate((old_c, new_c)):
                    im = Image.fromarray(cell).resize(
                        (cell.shape[1] * scale, cell.shape[0] * scale), Image.NEAREST
                    )
                    montage.paste(im, (j * (col_w + 20) + 4, i * row_h + 4))
            mp = os.path.join(out_dir, "verify.png")
            montage.save(mp)
            print(f"verify montage (left=OLD/JP, right=NEW/TC): {mp}")

    # ---- serialize atlas only (font tables unchanged) ------------------------
    if inline:
        td["m_CompleteImageSize"] = aw * ah
        td["image data"] = atlas.tobytes()
        node_tex = tex._get_typetree_node()
        tw_ = EndianBinaryWriter(endian="<")
        TypeTreeHelper.write_typetree(td, node_tex, tw_)
        tex_bytes = bytes(tw_.bytes)
        with open(os.path.join(out_dir, f"tex_{tex_pid}.bin"), "wb") as f:
            f.write(tex_bytes)
        print(f"tex_{tex_pid}.bin: {len(tex_bytes):,}")
    else:
        ress[off : off + aw * ah] = atlas.tobytes()
        base_ress = os.path.basename(assets_path) + ".resS"
        with open(os.path.join(out_dir, base_ress), "wb") as f:
            f.write(ress)
        print(f"{base_ress}: {len(ress):,}")

    with open(os.path.join(out_dir, f"report_{font_pid}.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "font_pid": font_pid,
                "tex_pid": tex_pid,
                "inline": inline,
                "replaced": replaced,
                "resized": resized,
                "missing_in_tc": missing_tc,
                "skipped_oob": skipped_bounds,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print("done")


if __name__ == "__main__":
    main()
