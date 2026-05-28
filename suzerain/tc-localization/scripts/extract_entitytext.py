# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "UnityPy>=1.20",
#     "typer>=0.12",
#     "rich>=13.7",
# ]
# ///
"""Extract every object from a Suzerain EntityTextAssets bundle as JSON.

The goal is schema discovery: dump each object's typetree so we can see
where strings live before writing a repack/translation pipeline.

Outputs into <out>/:
  - manifest.json              summary: counts by class_id, object list
  - objects/<idx>_<name>.json  per-object typetree dump
  - raw_strings.jsonl          best-effort extraction of {id, text} candidates
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import typer
import UnityPy
from rich.console import Console

app = typer.Typer(add_completion=False)
console = Console()

_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_name(s: str) -> str:
    return _SAFE.sub("_", s)[:80] or "unnamed"


@app.command()
def main(
    bundle: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    out: Path = typer.Option(..., "--out", "-o"),
    string_keys: str = typer.Option(
        "Title,Description,Notes,Text,Body,Content,Message,Label,Tooltip,Header,Subtitle,DisplayName,Summary,Prompt,Question,Answer,Choice,FullName,ShortName",
        "--string-keys",
        help="Comma-separated keys to harvest into raw_strings.jsonl. Matched inside TextAsset m_Script JSON.",
    ),
    min_len: int = typer.Option(2, "--min-len", help="Minimum string length to harvest."),
) -> None:
    out.mkdir(parents=True, exist_ok=True)
    objects_dir = out / "objects"
    objects_dir.mkdir(exist_ok=True)
    keys = [k.strip() for k in string_keys.split(",") if k.strip()]

    env = UnityPy.load(str(bundle))
    manifest: list[dict[str, object]] = []
    raw_strings_path = out / "raw_strings.jsonl"
    raw_count = 0

    with raw_strings_path.open("w", encoding="utf-8") as raw_f:
        for idx, obj in enumerate(env.objects):
            entry: dict[str, object] = {
                "index": idx,
                "type": obj.type.name,
                "path_id": getattr(obj, "path_id", None),
            }
            tree = None
            try:
                tree = obj.read_typetree()
            except Exception as e:  # noqa: BLE001
                entry["read_error"] = str(e)
                manifest.append(entry)
                continue

            name = ""
            if isinstance(tree, dict):
                name = str(tree.get("m_Name") or tree.get("name") or "")
            entry["name"] = name

            file_name = f"{idx:05d}_{obj.type.name}_{_safe_name(name)}.json"
            (objects_dir / file_name).write_text(
                json.dumps(tree, ensure_ascii=False, indent=2, default=_jsonable),
                encoding="utf-8",
            )
            entry["file"] = file_name
            manifest.append(entry)

            # For TextAsset, parse m_Script as JSON and harvest from the parsed tree.
            harvest_root: object = tree
            if obj.type.name == "TextAsset" and isinstance(tree, dict):
                script = tree.get("m_Script")
                if isinstance(script, str):
                    try:
                        harvest_root = json.loads(script)
                    except json.JSONDecodeError:
                        harvest_root = {"_raw": script}

            for path, value in _walk_strings(harvest_root, keys):
                if not isinstance(value, str) or not value.strip():
                    continue
                if len(value) < min_len or len(value) > 8000:
                    continue
                rec = {
                    "object_index": idx,
                    "object_name": name,
                    "path": path,
                    "text": value,
                }
                raw_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                raw_count += 1

    type_counts: dict[str, int] = {}
    for e in manifest:
        t = str(e["type"])
        type_counts[t] = type_counts.get(t, 0) + 1

    (out / "manifest.json").write_text(
        json.dumps(
            {
                "bundle": str(bundle),
                "object_count": len(manifest),
                "type_counts": type_counts,
                "raw_string_count": raw_count,
                "string_keys": keys,
                "objects": manifest,
            },
            ensure_ascii=False,
            indent=2,
            default=_jsonable,
        ),
        encoding="utf-8",
    )
    console.print(
        f"[green]Done[/]: {len(manifest)} objects, {raw_count} string candidates -> {out}"
    )


def _jsonable(o: object) -> object:
    if isinstance(o, bytes):
        try:
            return o.decode("utf-8")
        except UnicodeDecodeError:
            return o.hex()
    return repr(o)


def _walk_strings(node: object, keys: list[str], path: str = ""):
    if isinstance(node, dict):
        for k, v in node.items():
            sub = f"{path}.{k}" if path else str(k)
            if k in keys and isinstance(v, str):
                yield sub, v
            yield from _walk_strings(v, keys, sub)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk_strings(v, keys, f"{path}[{i}]")


if __name__ == "__main__":
    app()
