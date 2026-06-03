#!/usr/bin/env python3
"""Extract representative 2D character test images from Digimon Survive bundles.

Purpose:
- Generate a stable test-image set for cloth editing experiments.
- Focus on `slgchara/bu###` bundles (likely character 2D art).
- Keep only top-N largest textures per bundle as practical test targets.

Usage:
  python extract_test_images.py \
    --game-root "/mnt/d/SteamLibrary/steamapps/common/Digimon Survive" \
    --out-dir "/home/shado/crystal-mods/digimon-survive/cloth-edit-lab/extracted" \
    --preview-dir "/home/shado/crystal-mods/digimon-survive/cloth-edit-lab/preview" \
    --per-bundle 2

Requires:
- UnityPy
- Pillow
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

import UnityPy
from PIL import Image, ImageOps, ImageDraw
from UnityPy.enums import ClassIDType


DEFAULT_BUNDLES = [
    "slgchara/bu001",
    "slgchara/bu101",
    "slgchara/bu201",
    "slgchara/bu301",
    "slgchara/bu901",
]


@dataclass
class ExtractedTexture:
    bundle: str
    path_id: int
    width: int
    height: int
    area: int
    output_png: str


def safe_name(value: str) -> str:
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in value)


def iter_bundle_textures(bundle_path: Path) -> Iterable[tuple[int, Image.Image]]:
    env = UnityPy.load(str(bundle_path))
    for obj in env.objects:
        if obj.type != ClassIDType.Texture2D:
            continue
        data = obj.read()
        img = data.image
        if img is None:
            continue
        yield obj.path_id, img


def extract_bundle(bundle_root: Path, bundle_rel: str, out_dir: Path, per_bundle: int) -> list[ExtractedTexture]:
    bundle_path = bundle_root / bundle_rel
    if not bundle_path.exists():
        print(f"[skip] missing bundle: {bundle_rel}")
        return []

    textures: list[tuple[int, Image.Image]] = list(iter_bundle_textures(bundle_path))
    if not textures:
        print(f"[skip] no textures: {bundle_rel}")
        return []

    textures.sort(key=lambda item: item[1].width * item[1].height, reverse=True)
    chosen = textures[:per_bundle]

    bundle_out = out_dir / safe_name(bundle_rel)
    bundle_out.mkdir(parents=True, exist_ok=True)

    records: list[ExtractedTexture] = []
    for path_id, img in chosen:
        out_name = f"path_{path_id}_{img.width}x{img.height}.png"
        out_path = bundle_out / out_name
        img.save(out_path)
        rec = ExtractedTexture(
            bundle=bundle_rel,
            path_id=path_id,
            width=img.width,
            height=img.height,
            area=img.width * img.height,
            output_png=str(out_path),
        )
        records.append(rec)
        print(f"[ok] {bundle_rel} -> {out_name}")

    return records


def build_contact_sheet(image_paths: list[Path], out_path: Path, thumb_size: int = 320, columns: int = 4) -> None:
    if not image_paths:
        return

    rows = (len(image_paths) + columns - 1) // columns
    cell_w = thumb_size + 8
    cell_h = thumb_size + 40
    canvas = Image.new("RGB", (columns * cell_w + 8, rows * cell_h + 8), color=(24, 24, 24))
    draw = ImageDraw.Draw(canvas)

    for i, src in enumerate(image_paths):
        col = i % columns
        row = i // columns
        x = 8 + col * cell_w
        y = 8 + row * cell_h

        with Image.open(src) as im:
            thumb = ImageOps.contain(im.convert("RGB"), (thumb_size, thumb_size))
            tx = x + (thumb_size - thumb.width) // 2
            ty = y + (thumb_size - thumb.height) // 2
            canvas.paste(thumb, (tx, ty))

        label = src.name
        draw.text((x, y + thumb_size + 8), label, fill=(220, 220, 220))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract character test images from Digimon Survive bundles")
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--preview-dir", type=Path, required=True)
    parser.add_argument("--per-bundle", type=int, default=2)
    parser.add_argument("--bundles", nargs="*", default=DEFAULT_BUNDLES)
    args = parser.parse_args()

    bundle_root = args.game_root / "DigimonSurvive_Data" / "StreamingAssets" / "StandaloneWindows64"
    if not bundle_root.exists():
        raise SystemExit(f"Bundle root not found: {bundle_root}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.preview_dir.mkdir(parents=True, exist_ok=True)

    all_records: list[ExtractedTexture] = []
    for bundle_rel in args.bundles:
        all_records.extend(extract_bundle(bundle_root, bundle_rel, args.out_dir, args.per_bundle))

    if not all_records:
        raise SystemExit("No textures extracted.")

    manifest = {
        "game_root": str(args.game_root),
        "bundle_root": str(bundle_root),
        "per_bundle": args.per_bundle,
        "bundles": args.bundles,
        "count": len(all_records),
        "textures": [asdict(r) for r in all_records],
    }

    manifest_path = args.out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    image_paths = [Path(rec.output_png) for rec in all_records]
    sheet_path = args.preview_dir / "contact_sheet.png"
    build_contact_sheet(image_paths, sheet_path)

    print(f"\n[done] Extracted {len(all_records)} textures")
    print(f"[done] Manifest: {manifest_path}")
    print(f"[done] Contact sheet: {sheet_path}")


if __name__ == "__main__":
    main()
