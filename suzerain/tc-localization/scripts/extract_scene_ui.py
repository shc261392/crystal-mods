# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "UnityPy>=1.20",
#     "typer>=0.12",
#     "rich>=13.7",
# ]
# ///
"""Extract unique runtime UI strings from Suzerain scene bundles.

Targets the three shipped scene bundles and collects strings from:
- `StaticUIText.locaId`
- `TextMeshProUGUI.m_text`

The output is a JSONL source file suitable for the `tl` translation tool.
IDs are synthetic (`scene-ui-00001`, ...); repacking uses source-text matching,
so IDs only need to be stable within this project.
"""

from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path

import typer
import UnityPy
from rich.console import Console

app = typer.Typer(add_completion=False)
console = Console()

STATIC_UI_SCRIPT = 7343663649919329368
TMP_TEXT_SCRIPT = 7477354737935883349
SCENE_GLOB = "scenes_scenes_assets_scenes_*.bundle"


def _human(text: str) -> bool:
    return bool(text and text.strip())


@app.command()
def main(
    input_dir: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),
    out: Path = typer.Option(..., "--out", "-o"),
) -> None:
    """Extract unique scene UI strings into JSONL."""
    unique: "OrderedDict[str, None]" = OrderedDict()
    bundle_count = 0

    for bundle in sorted(input_dir.glob(SCENE_GLOB)):
        bundle_count += 1
        env = UnityPy.load(str(bundle))
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
                text = tree.get("locaId")
            elif path_id == TMP_TEXT_SCRIPT:
                text = tree.get("m_text")
            else:
                continue
            if isinstance(text, str) and _human(text):
                unique.setdefault(text, None)

    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps({"id": f"scene-ui-{i:05d}", "text": text}, ensure_ascii=False)
        for i, text in enumerate(unique.keys(), 1)
    ]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    console.print(
        f"[green]Done[/]: extracted {len(unique)} unique strings from {bundle_count} scene bundles -> {out}"
    )


if __name__ == "__main__":
    app()
