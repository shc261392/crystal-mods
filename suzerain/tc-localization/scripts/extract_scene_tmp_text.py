# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "UnityPy>=1.20",
#   "typer>=0.12",
#   "rich>=13.7",
# ]
# ///
"""Extract runtime scene UI text (TextMeshProUGUI.m_text) for translation.

Safety: this extractor intentionally ignores `StaticUIText.locaId` because
those are localization keys and changing them can break runtime linkage.
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

SCENE_GLOB = "scenes_scenes_assets_scenes_*.bundle"
TMP_TEXT_SCRIPT = 7477354737935883349  # TextMeshProUGUI


def _is_meaningful(text: str) -> bool:
    return bool(text and text.strip())


@app.command()
def main(
    input_dir: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),
    out: Path = typer.Option(..., "--out", "-o"),
) -> None:
    unique: "OrderedDict[str, None]" = OrderedDict()
    bundles = 0

    for bundle in sorted(input_dir.glob(SCENE_GLOB)):
        bundles += 1
        env = UnityPy.load(str(bundle))
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
            text = tree.get("m_text")
            if isinstance(text, str) and _is_meaningful(text):
                unique.setdefault(text, None)

    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps({"id": f"scene-tmp-{i:05d}", "text": text}, ensure_ascii=False)
        for i, text in enumerate(unique.keys(), 1)
    ]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    console.print(
        f"[green]Done[/]: extracted {len(unique)} unique TMP texts from {bundles} scene bundles -> {out}"
    )


if __name__ == "__main__":
    app()
