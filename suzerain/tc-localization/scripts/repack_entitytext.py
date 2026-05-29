# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "UnityPy>=1.20",
#     "typer>=0.12",
#     "rich>=13.7",
# ]
# ///
"""Repack translated strings back into a Suzerain EntityTextAssets bundle.

Reads the translation project's ``state.jsonl`` (final = manual else machine)
and the original bundle, then rewrites each TextAsset's ``m_Script`` JSON with
the translated values at their recorded paths. Object iteration order matches
``extract_entitytext.py`` so the ``<object_index:05d>::<path>`` IDs line up.

The original bundle is never modified in place: output goes to ``--out``.

Usage:
    uv run --script repack_entitytext.py \\
        <original.bundle> \\
        --project ../translation \\
        --out ../build/<original.bundle name>
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

# Splits an ID path like "items[1662].ReportProperties.Description" into steps.
# Each match is either a dict key or a list index.
_STEP_RE = re.compile(r"([^.\[\]]+)|\[(\d+)\]")


def _parse_path(path: str) -> list[object]:
    """Turn a dotted/indexed path into a list of str keys and int indices."""
    steps: list[object] = []
    for m in _STEP_RE.finditer(path):
        key, idx = m.group(1), m.group(2)
        if idx is not None:
            steps.append(int(idx))
        else:
            steps.append(key)
    return steps


def _set_by_path(root: object, steps: list[object], value: str) -> bool:
    """Set ``value`` at the location described by ``steps``. Returns success."""
    node = root
    for step in steps[:-1]:
        if isinstance(step, int):
            if not isinstance(node, list) or step >= len(node):
                return False
            node = node[step]
        else:
            if not isinstance(node, dict) or step not in node:
                return False
            node = node[step]
    last = steps[-1]
    if isinstance(last, int):
        if not isinstance(node, list) or last >= len(node):
            return False
        node[last] = value
        return True
    if not isinstance(node, dict) or last not in node:
        return False
    node[last] = value
    return True


def _load_final(project: Path) -> dict[str, str]:
    """Return {unit_id: final_text} from the project's state.jsonl."""
    state_path = project / "state.jsonl"
    out: dict[str, str] = {}
    for line in state_path.read_text("utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        final = rec.get("manual") if rec.get("manual") is not None else rec.get("machine")
        if final:
            out[rec["id"]] = final
    return out


def _load_source(project: Path) -> dict[str, str]:
    """Return {unit_id: english_text} from the project's source.jsonl."""
    src_path = project / "source.jsonl"
    out: dict[str, str] = {}
    for line in src_path.read_text("utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("text"):
            out[rec["id"]] = rec["text"]
    return out


def _build_text_map(project: Path) -> dict[str, str]:
    """Map English source string -> translated string.

    The runtime database (the "Entity Text Assets" MonoBehaviour) stores its
    content as ``*DataJson`` strings whose values mirror the standalone
    TextAssets, so a value-keyed map lets us patch it without re-deriving the
    per-field path layout.
    """
    source = _load_source(project)
    finals = _load_final(project)
    mapping: dict[str, str] = {}
    for uid, tgt in finals.items():
        src = source.get(uid)
        if src and tgt and src != tgt and src not in mapping:
            mapping[src] = tgt
    return mapping


def _replace_strings(node: object, mapping: dict[str, str]) -> int:
    """Recursively replace matching string leaves in-place. Returns count."""
    count = 0
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(value, str):
                tgt = mapping.get(value)
                if tgt is not None:
                    node[key] = tgt
                    count += 1
            else:
                count += _replace_strings(value, mapping)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            if isinstance(value, str):
                tgt = mapping.get(value)
                if tgt is not None:
                    node[i] = tgt
                    count += 1
            else:
                count += _replace_strings(value, mapping)
    return count


def _patch_database(env: UnityPy.Environment, mapping: dict[str, str]) -> tuple[int, int]:
    """Patch the runtime "Entity Text Assets" MonoBehaviour *DataJson fields.

    Returns (strings_replaced, fields_touched).
    """
    replaced = 0
    fields = 0
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        tree = obj.read_typetree()
        if tree.get("m_Name") != "Entity Text Assets":
            continue
        touched = False
        for key, value in tree.items():
            if not (key.endswith("DataJson") and isinstance(value, str) and value.strip()):
                continue
            try:
                data = json.loads(value)
            except json.JSONDecodeError:
                continue
            n = _replace_strings(data, mapping)
            if n:
                tree[key] = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
                replaced += n
                fields += 1
                touched = True
        if touched:
            obj.save_typetree(tree)
        break
    return replaced, fields


@app.command()
def main(
    bundle: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    project: Path = typer.Option(..., "--project", "-p", exists=True, file_okay=False),
    out: Path = typer.Option(..., "--out", "-o"),
    require_final: bool = typer.Option(
        False, "--require-final", help="Only apply units with status=final."
    ),
) -> None:
    """Inject translations into ``bundle`` and write the result to ``out``."""
    finals = _load_final(project)
    if require_final:
        # Re-filter using status when strict mode is requested.
        state_path = project / "state.jsonl"
        finals = {}
        for line in state_path.read_text("utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("status") != "final":
                continue
            final = rec.get("manual") if rec.get("manual") is not None else rec.get("machine")
            if final:
                finals[rec["id"]] = final
    console.print(f"[cyan]Loaded[/] {len(finals)} translated units from {project}")

    # Group translations by object index for efficient per-object application.
    by_index: dict[int, list[tuple[str, str]]] = {}
    for uid, text in finals.items():
        idx_str, _, path = uid.partition("::")
        try:
            idx = int(idx_str)
        except ValueError:
            console.print(f"[yellow]Skipping malformed id[/] {uid!r}")
            continue
        by_index.setdefault(idx, []).append((path, text))

    env = UnityPy.load(str(bundle))
    applied = 0
    missed = 0
    objects_touched = 0

    for idx, obj in enumerate(env.objects):
        pairs = by_index.get(idx)
        if not pairs:
            continue
        if obj.type.name != "TextAsset":
            console.print(f"[yellow]Object {idx} is {obj.type.name}, not TextAsset; skipping[/]")
            continue
        tree = obj.read_typetree()
        script = tree.get("m_Script")
        if not isinstance(script, str):
            console.print(f"[yellow]Object {idx} has no string m_Script; skipping[/]")
            continue
        try:
            data = json.loads(script)
        except json.JSONDecodeError:
            console.print(f"[yellow]Object {idx} m_Script is not JSON; skipping[/]")
            continue

        changed = 0
        for path, text in pairs:
            if _set_by_path(data, _parse_path(path), text):
                changed += 1
                applied += 1
            else:
                missed += 1
        if changed:
            # Compact separators keep the asset size close to the original.
            tree["m_Script"] = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            obj.save_typetree(tree)
            objects_touched += 1

    # Primary target: the runtime "Entity Text Assets" MonoBehaviour. The game
    # deserializes its ``*DataJson`` string fields at load time; the standalone
    # TextAssets above are editor source copies and are NOT read in-game.
    db_replaced, db_fields = _patch_database(env, _build_text_map(project))
    console.print(
        f"[green]Database[/]: {db_replaced} strings replaced across {db_fields} "
        f"*DataJson fields in the 'Entity Text Assets' MonoBehaviour"
    )

    out.parent.mkdir(parents=True, exist_ok=True)
    # Match the original bundle's LZ4 block compression. Unity Addressables can
    # silently refuse to mount a bundle saved with a different format, so we do
    # NOT leave it uncompressed (the UnityPy default).
    out.write_bytes(env.file.save(packer="lz4"))
    console.print(
        f"[green]Done[/]: {applied} strings applied across {objects_touched} TextAssets, "
        f"{missed} missed -> {out}"
    )
    if missed:
        console.print(
            "[yellow]Note:[/] missed paths usually mean the bundle differs from the "
            "one used for extraction. Re-run extraction if the game updated."
        )


if __name__ == "__main__":
    app()
