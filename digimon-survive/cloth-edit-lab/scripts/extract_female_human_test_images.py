#!/usr/bin/env python3
"""Extract female human character test textures from Digimon Survive talkchar bundles.

Defaults target IDs visually verified as female human in talkchar atlases.

Usage:
  python extract_female_human_test_images.py \
    --game-root "/mnt/d/SteamLibrary/steamapps/common/Digimon Survive" \
    --out-dir "/home/shado/crystal-mods/digimon-survive/cloth-edit-lab/extracted/female_human" \
    --preview-dir "/home/shado/crystal-mods/digimon-survive/cloth-edit-lab/preview" \
    --ids 920 939 949
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path

import UnityPy
from PIL import Image, ImageDraw, ImageOps
from UnityPy.enums import ClassIDType

DEFAULT_IDS = [920, 939, 949]


@dataclass
class Record:
    character_id: int
    variant_path: str
    path_id: int
    width: int
    height: int
    area: int
    output_png: str


def extract_top_texture(bundle_file: Path):
    env = UnityPy.load(str(bundle_file))
    best = None
    for obj in env.objects:
        if obj.type != ClassIDType.Texture2D:
            continue
        data = obj.read()
        img = data.image
        if img is None:
            continue
        area = img.width * img.height
        if best is None or area > best[0]:
            best = (area, img.copy(), obj.path_id)
    return best


def make_contact_sheet(paths: list[Path], out_path: Path, columns: int = 3, thumb: int = 420) -> None:
    if not paths:
        return

    rows = (len(paths) + columns - 1) // columns
    cell_w = thumb + 24
    cell_h = thumb + 52
    canvas = Image.new("RGB", (columns * cell_w + 24, rows * cell_h + 24), (18, 18, 18))
    draw = ImageDraw.Draw(canvas)

    for i, p in enumerate(paths):
        col = i % columns
        row = i // columns
        x = 24 + col * cell_w
        y = 24 + row * cell_h

        with Image.open(p) as im:
            t = ImageOps.contain(im.convert("RGB"), (thumb, thumb))
            tx = x + (thumb - t.width) // 2
            ty = y + (thumb - t.height) // 2
            canvas.paste(t, (tx, ty))

        draw.text((x, y + thumb + 10), p.stem, fill=(235, 235, 235))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--game-root", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--preview-dir", type=Path, required=True)
    ap.add_argument("--ids", nargs="*", type=int, default=DEFAULT_IDS)
    args = ap.parse_args()

    base = args.game_root / "DigimonSurvive_Data" / "StreamingAssets" / "StandaloneWindows64" / "talkchar" / "prefabs"
    if not base.exists():
        raise SystemExit(f"talkchar base not found: {base}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.preview_dir.mkdir(parents=True, exist_ok=True)

    records: list[Record] = []
    for cid in args.ids:
        cdir = base / f"{cid:03d}"
        if not cdir.exists():
            print(f"[skip] missing ID {cid}")
            continue

        variants = sorted(cdir.rglob("0101"))
        if not variants:
            print(f"[skip] no variant bundle files for ID {cid}")
            continue

        for vf in variants:
            top = extract_top_texture(vf)
            if top is None:
                continue
            area, img, path_id = top
            rel = vf.relative_to(base).as_posix().replace("/", "_")
            out_name = f"ID_{cid}_{rel}_path_{path_id}_{img.width}x{img.height}.png"
            out_path = args.out_dir / out_name
            img.save(out_path)

            records.append(
                Record(
                    character_id=cid,
                    variant_path=vf.relative_to(base).as_posix(),
                    path_id=path_id,
                    width=img.width,
                    height=img.height,
                    area=area,
                    output_png=str(out_path),
                )
            )
            print(f"[ok] {cid} {vf.relative_to(base)} -> {out_name}")

    if not records:
        raise SystemExit("No textures extracted.")

    manifest = {
        "ids": args.ids,
        "count": len(records),
        "records": [asdict(r) for r in records],
    }
    manifest_path = args.out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    image_paths = [Path(r.output_png) for r in records]
    sheet = args.preview_dir / "female_human_contact_sheet.png"
    make_contact_sheet(image_paths, sheet)

    print(f"\n[done] extracted {len(records)} female-human test textures")
    print(f"[done] manifest: {manifest_path}")
    print(f"[done] sheet: {sheet}")


if __name__ == "__main__":
    main()
