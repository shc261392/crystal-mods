# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "UnityPy>=1.20",
#   "typer>=0.12",
#   "rich>=13.7",
# ]
# ///
"""Patch runtime scene UI text safely (TextMeshProUGUI.m_text only).

Safety guard: never edits `StaticUIText.locaId` or any key-like field.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
import UnityPy
from rich.console import Console

app = typer.Typer(add_completion=False)
console = Console()

TMP_TEXT_SCRIPT = 7477354737935883349  # TextMeshProUGUI
SAFE_SCENE_FILES = (
    "scenes_scenes_assets_scenes_mainmenu.unity_6dd6ca6b71e2733b13cf2860d4a95134.bundle",
    "scenes_scenes_assets_scenes_rizia.unity_f3aa16cfb48dca20773754a9c19d5c1d.bundle",
)
SORDLAND_FILE = "scenes_scenes_assets_scenes_sordland.unity_6a29f2cab2ef8b301931a992da045ec1.bundle"


def _load_map(project: Path) -> dict[str, str]:
    src = {}
    for line in (project / "source.jsonl").read_text("utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            src[rec["id"]] = rec["text"]

    out: dict[str, str] = {}
    for line in (project / "state.jsonl").read_text("utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        tgt = rec.get("manual") if rec.get("manual") is not None else rec.get("machine")
        s = src.get(rec["id"])
        if s and tgt and s != tgt:
            out[s] = tgt
    return out


@app.command()
def main(
    input_dir: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),
    project: Path = typer.Option(..., "--project", "-p", exists=True, file_okay=False),
    out_dir: Path = typer.Option(..., "--out-dir", "-o"),
    include_sordland: bool = typer.Option(
        False,
        "--include-sordland",
        help="Also patch the Sordland scene bundle (known to trigger load-game crash in current build).",
    ),
) -> None:
    mapping = _load_map(project)
    out_dir.mkdir(parents=True, exist_ok=True)

    bundles = 0
    hits = 0

    names = list(SAFE_SCENE_FILES)
    if include_sordland:
        names.append(SORDLAND_FILE)

    for name in names:
        bundle = input_dir / name
        if not bundle.exists():
            console.print(f"[yellow]missing[/]: {bundle}")
            continue
        env = UnityPy.load(str(bundle))
        changed = False

        for obj in env.objects:
            if obj.type.name != "MonoBehaviour":
                continue
            try:
                tree = obj.read_typetree()
            except Exception:
                continue
            script = tree.get("m_Script")
            if not isinstance(script, dict) or script.get("m_PathID") != TMP_TEXT_SCRIPT:
                continue
            src = tree.get("m_text")
            tgt = mapping.get(src) if isinstance(src, str) else None
            if tgt and tgt != src:
                tree["m_text"] = tgt
                obj.save_typetree(tree)
                hits += 1
                changed = True

        out_path = out_dir / bundle.name
        out_path.write_bytes(env.file.save(packer="lz4"))
        bundles += 1
        console.print(f"[cyan]{'patched' if changed else 'copied'}[/]: {bundle.name} -> {out_path}")

    console.print(f"[green]Done[/]: {bundles} scene bundles written, {hits} TextMeshProUGUI updates")


if __name__ == "__main__":
    app()
