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
and the original bundle, then rewrites:

1) standalone TextAsset JSON copies (path-precise)
2) runtime "Entity Text Assets" MonoBehaviour ``*DataJson`` fields (also path-precise)

Important safety rule:
- Runtime identity/linkage fields are excluded from DataJson patching:
  StoryPackDataJson, AppBundleDataJson.
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

_STEP_RE = re.compile(r"([^\.\[\]]+)|\[(\d+)\]")
_RUNTIME_ID_FIELDS = {"StoryPackDataJson", "AppBundleDataJson"}

# Map field names (after Json strip) to TextAsset m_Names (where names differ)
# e.g., CodexEntriesData (field) -> CodexEntryData (TextAsset)
_ASSET_NAME_MAPPING = {
    "CodexEntriesData": "CodexEntryData",  # Plural field -> singular TextAsset
}


def _parse_path(path: str) -> list[object]:
    steps: list[object] = []
    for m in _STEP_RE.finditer(path):
        key, idx = m.group(1), m.group(2)
        if idx is not None:
            steps.append(int(idx))
        else:
            steps.append(key)
    return steps


def _set_by_path(root: object, steps: list[object], value: str) -> bool:
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
    out: dict[str, str] = {}
    for line in (project / "source.jsonl").read_text("utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        text = rec.get("text")
        if isinstance(text, str):
            out[rec["id"]] = text
    return out


def _load_override_tsv(path: Path) -> dict[str, str]:
    rows = [ln for ln in path.read_text("utf-8").splitlines() if ln.strip()]
    if not rows:
        return {}
    header = rows[0].split("\t")
    try:
        src_idx = header.index("source")
        tgt_idx = header.index("target")
    except ValueError as e:
        raise typer.BadParameter("override TSV must include source/target columns") from e

    out: dict[str, str] = {}
    for ln in rows[1:]:
        cols = ln.split("\t")
        if len(cols) <= max(src_idx, tgt_idx):
            continue
        src = cols[src_idx]
        tgt = cols[tgt_idx]
        if src and tgt:
            out[src] = tgt
    return out


def _patch_database(
    env: UnityPy.Environment, by_asset_name: dict[str, list[tuple[str, str]]]
) -> tuple[int, int]:
    """Patch runtime DataJson fields with exact path updates.

    BillsDataJson -> BillsData (TextAsset m_Name) mapping is used to target
    precise fields/paths and avoid global replacement side effects.
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
            if key in _RUNTIME_ID_FIELDS:
                continue

            asset_name = key[: -len("Json")]
            # Apply mapping for field names that differ from TextAsset m_Names
            asset_name = _ASSET_NAME_MAPPING.get(asset_name, asset_name)
            pairs = by_asset_name.get(asset_name)
            if not pairs:
                continue

            try:
                data = json.loads(value)
            except json.JSONDecodeError:
                continue

            n = 0
            for path, text in pairs:
                if _set_by_path(data, _parse_path(path), text):
                    n += 1

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
    require_final: bool = typer.Option(False, "--require-final", help="Only apply units with status=final."),
    override_tsv: Path | None = typer.Option(
        None,
        "--override-tsv",
        help="Optional TSV with source/target overrides for untranslated proper names.",
    ),
) -> None:
    finals = _load_final(project)
    if require_final:
        finals = {}
        for line in (project / "state.jsonl").read_text("utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("status") != "final":
                continue
            final = rec.get("manual") if rec.get("manual") is not None else rec.get("machine")
            if final:
                finals[rec["id"]] = final

    console.print(f"[cyan]Loaded[/] {len(finals)} translated units from {project}")

    source_by_id = _load_source(project)
    overrides = _load_override_tsv(override_tsv) if override_tsv is not None else {}
    if overrides:
        patched = 0
        for uid, current in list(finals.items()):
            src = source_by_id.get(uid)
            if not isinstance(src, str):
                continue
            mapped = overrides.get(src)
            if mapped and current == src:
                finals[uid] = mapped
                patched += 1
        console.print(f"[cyan]Overrides[/]: applied {patched} source-text replacements")

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
    by_asset_name: dict[str, list[tuple[str, str]]] = {}

    for idx, obj in enumerate(env.objects):
        pairs = by_index.get(idx)
        if not pairs:
            continue
        if obj.type.name != "TextAsset":
            continue

        tree = obj.read_typetree()
        script = tree.get("m_Script")
        if not isinstance(script, str):
            continue

        try:
            data = json.loads(script)
        except json.JSONDecodeError:
            continue

        changed = 0
        for path, text in pairs:
            if _set_by_path(data, _parse_path(path), text):
                changed += 1
                applied += 1
            else:
                missed += 1

        if changed:
            tree["m_Script"] = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            obj.save_typetree(tree)
            objects_touched += 1

        name = tree.get("m_Name")
        if isinstance(name, str) and name:
            by_asset_name.setdefault(name, []).extend(pairs)

    db_replaced, db_fields = _patch_database(env, by_asset_name)
    console.print(
        f"[green]Database[/]: {db_replaced} path updates across {db_fields} *DataJson fields"
    )

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(env.file.save(packer="lz4"))
    console.print(
        f"[green]Done[/]: {applied} path updates across {objects_touched} TextAssets, "
        f"{missed} missed -> {out}"
    )


if __name__ == "__main__":
    app()
