# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "UnityPy>=1.20",
#     "typer>=0.12",
#     "rich>=13.7",
# ]
# ///
"""Patch Suzerain scene bundles with translated UI strings.

Rewrites two runtime UI component fields across the shipped scene bundles:
- `StaticUIText.locaId`
- `TextMeshProUGUI.m_text`

Translations are loaded from a `tl` project directory by matching the source
English text to `final = manual else machine` in `state.jsonl`.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
import UnityPy
from rich.console import Console

app = typer.Typer(add_completion=False)
console = Console()

STATIC_UI_SCRIPT = 7343663649919329368
TMP_TEXT_SCRIPT = 7477354737935883349
SCENE_GLOB = "scenes_scenes_assets_scenes_*.bundle"


def _load_text_map(project: Path, reverse: bool = False) -> dict[str, str]:
    source_path = project / "source.jsonl"
    state_path = project / "state.jsonl"
    source_by_id: dict[str, str] = {}
    for line in source_path.read_text("utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        source_by_id[rec["id"]] = rec["text"]

    mapping: dict[str, str] = {}
    for line in state_path.read_text("utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        tgt = rec.get("manual") if rec.get("manual") is not None else rec.get("machine")
        src = source_by_id.get(rec["id"])
        if src and tgt and src != tgt:
            if reverse:
                mapping[tgt] = src
            else:
                mapping[src] = tgt
    return mapping


@app.command()
def main(
    input_dir: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),
    project: Path = typer.Option(..., "--project", "-p", exists=True, file_okay=False),
    out_dir: Path = typer.Option(..., "--out-dir", "-o"),
    reverse: bool = typer.Option(False, "--reverse", help="Invert the mapping (zh-TW -> original source)."),
) -> None:
    """Patch all runtime scene bundles in INPUT_DIR and write them to OUT_DIR."""
    mapping = _load_text_map(project, reverse=reverse)
    out_dir.mkdir(parents=True, exist_ok=True)

    bundles = 0
    static_hits = 0
    tmp_hits = 0

    for bundle in sorted(input_dir.glob(SCENE_GLOB)):
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
            if not isinstance(script, dict):
                continue
            path_id = script.get("m_PathID")
            if path_id == STATIC_UI_SCRIPT:
                src = tree.get("locaId")
                tgt = mapping.get(src) if isinstance(src, str) else None
                if tgt and tgt != src:
                    tree["locaId"] = tgt
                    obj.save_typetree(tree)
                    static_hits += 1
                    changed = True
            elif path_id == TMP_TEXT_SCRIPT:
                src = tree.get("m_text")
                tgt = mapping.get(src) if isinstance(src, str) else None
                if tgt and tgt != src:
                    tree["m_text"] = tgt
                    obj.save_typetree(tree)
                    tmp_hits += 1
                    changed = True
        out_path = out_dir / bundle.name
        out_path.write_bytes(env.file.save(packer="lz4"))
        bundles += 1
        status = "patched" if changed else "copied"
        console.print(f"[cyan]{status}[/]: {bundle.name} -> {out_path}")

    console.print(
        f"[green]Done[/]: {bundles} scene bundles written, "
        f"{static_hits} StaticUIText updates, {tmp_hits} TextMeshProUGUI updates"
    )


if __name__ == "__main__":
    app()
