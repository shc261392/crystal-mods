"""
extract_textures.py — extract PNG textures from a Digimon Survive asset bundle.

Usage:
    uv run python extract_textures.py <bundle_path> <output_dir> [--max N]

Requires: UnityPy
"""

import argparse
import sys
from pathlib import Path

import UnityPy
from UnityPy.enums import ClassIDType


def extract(bundle_path: Path, output_dir: Path, max_count: int | None) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    env = UnityPy.load(str(bundle_path))

    saved: list[Path] = []
    for obj in env.objects:
        if obj.type not in (ClassIDType.Texture2D, ClassIDType.Sprite):
            continue
        data = obj.read()
        name = getattr(data, "name", None) or f"tex_{obj.path_id}"
        # Sanitise name
        safe_name = "".join(c if c.isalnum() or c in "-_." else "_" for c in name)
        out_path = output_dir / f"{safe_name}.png"
        img = data.image
        if img is None:
            continue
        img.save(out_path)
        saved.append(out_path)
        print(f"  extracted: {out_path.name}  ({img.width}x{img.height})")
        if max_count and len(saved) >= max_count:
            break

    return saved


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("bundle", type=Path, help="Asset bundle file path")
    ap.add_argument("output_dir", type=Path, help="Directory to write PNGs into")
    ap.add_argument("--max", type=int, default=None, dest="max_count",
                    help="Stop after extracting this many textures")
    args = ap.parse_args()

    if not args.bundle.exists():
        sys.exit(f"Bundle not found: {args.bundle}")

    print(f"Loading bundle: {args.bundle}")
    paths = extract(args.bundle, args.output_dir, args.max_count)
    print(f"\nDone. {len(paths)} texture(s) saved to {args.output_dir}")


if __name__ == "__main__":
    main()
