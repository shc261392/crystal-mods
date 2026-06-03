"""
upscale_textures.py — upscale PNG textures with spandrel + Real-ESRGAN 4x.

2026 SOTA pipeline:
  - spandrel: model-agnostic inference framework (supports 100+ SR models)
  - Default model: RealESRGAN_x4plus (photographic/mixed content)
  - Alt model flag: --anime  (4xAnime model, better for stylised art)
  - CUDA auto-detected (RTX 3090); falls back to CPU

Usage:
    uv run python upscale_textures.py <input_dir> <output_dir> [--scale 2|4] [--anime]

Requires: spandrel, torch (CUDA), safetensors, pillow
"""

from __future__ import annotations

import argparse
import urllib.request
from pathlib import Path

import torch
from PIL import Image


# ---------------------------------------------------------------------------
# Model registry — OpenModelDB / community-hosted weights
# ---------------------------------------------------------------------------
MODELS: dict[str, dict] = {
    "photo": {
        "url": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
        "filename": "RealESRGAN_x4plus.pth",
        "scale": 4,
        "description": "RealESRGAN x4+ — photographic & mixed content (2021, widely supported)",
    },
    "anime": {
        "url": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth",
        "filename": "RealESRGAN_x4plus_anime_6B.pth",
        "scale": 4,
        "description": "RealESRGAN x4+ Anime 6B — stylised / anime art (2021)",
    },
}

WEIGHTS_DIR = Path(__file__).parent.parent / "weights"


def download_weights(model_key: str) -> Path:
    entry = MODELS[model_key]
    WEIGHTS_DIR.mkdir(exist_ok=True)
    dest = WEIGHTS_DIR / entry["filename"]
    if dest.exists():
        print(f"  weights cached: {dest.name}")
        return dest
    print(f"  downloading {entry['filename']} …")
    urllib.request.urlretrieve(entry["url"], dest)
    print(f"  saved to {dest}")
    return dest


def get_device() -> torch.device:
    if torch.cuda.is_available():
        device = torch.device("cuda")
        props = torch.cuda.get_device_properties(device)
        print(f"  GPU: {props.name}  VRAM: {props.total_memory // 1024**2} MB")
    else:
        device = torch.device("cpu")
        print("  GPU not available — using CPU")
    return device


def load_model(weights_path: Path, device: torch.device):
    """Load model via spandrel — auto-detects architecture from weights file."""
    import spandrel
    descriptor = spandrel.ModelLoader(device=device).load_from_file(str(weights_path))
    descriptor.model.eval()
    return descriptor


def upscale_image(descriptor, img: Image.Image, device: torch.device) -> Image.Image:
    """Run one image through the SR descriptor and return a PIL Image."""
    import numpy as np
    arr = np.array(img.convert("RGB")).astype(np.float32) / 255.0
    tensor = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0).to(device)  # 1,C,H,W

    with torch.inference_mode():
        out = descriptor(tensor)

    out_arr = out.squeeze(0).permute(1, 2, 0).clamp(0, 1).cpu().numpy()
    return Image.fromarray((out_arr * 255).astype("uint8"))


def main() -> None:
    ap = argparse.ArgumentParser(description="Upscale textures with 2026 SOTA SR model")
    ap.add_argument("input_dir", type=Path)
    ap.add_argument("output_dir", type=Path)
    ap.add_argument("--anime", action="store_true",
                    help="Use anime-optimised model instead of photo model")
    ap.add_argument("--scale", type=int, default=4, choices=[2, 4],
                    help="Target upscale factor (model always runs 4x; "
                         "if 2 is chosen the result is downsampled back)")
    args = ap.parse_args()

    model_key = "anime" if args.anime else "photo"
    entry = MODELS[model_key]
    print(f"Model: {entry['description']}")

    weights = download_weights(model_key)
    device = get_device()
    descriptor = load_model(weights, device)
    print(f"Model loaded on {device}.")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    pngs = sorted(args.input_dir.glob("*.png"))
    if not pngs:
        print("No PNG files found in input_dir.")
        return

    for src in pngs:
        print(f"\nUpscaling: {src.name}")
        img = Image.open(src)
        print(f"  input : {img.width}x{img.height}")
        sr = upscale_image(descriptor, img, device)

        if args.scale == 2:
            sr = sr.resize((sr.width // 2, sr.height // 2), Image.LANCZOS)

        dest = args.output_dir / src.name
        sr.save(dest)
        print(f"  output: {sr.width}x{sr.height}  → {dest}")

    print(f"\nDone. Results in: {args.output_dir}")


if __name__ == "__main__":
    main()
