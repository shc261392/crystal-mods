# /// script
# requires-python = ">=3.12"
# dependencies = ["typer>=0.12"]
# ///
"""Convert raw_strings.jsonl (from extract_entitytext.py) into a
source.jsonl suitable for `tl init --source`.

ID scheme: `<object_index:05d>::<path>`. Stable across reruns as long as
the bundle and the extractor's iteration order are unchanged.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

app = typer.Typer(add_completion=False)


@app.command()
def main(
    raw: Path = typer.Argument(..., exists=True, dir_okay=False),
    out: Path = typer.Option(..., "--out", "-o"),
) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with raw.open("r", encoding="utf-8") as r_f, out.open("w", encoding="utf-8") as o_f:
        for line in r_f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            uid = f"{rec['object_index']:05d}::{rec['path']}"
            o_f.write(json.dumps({"id": uid, "text": rec["text"]}, ensure_ascii=False) + "\n")
            n += 1
    typer.echo(f"Wrote {n} units -> {out}")


if __name__ == "__main__":
    app()
