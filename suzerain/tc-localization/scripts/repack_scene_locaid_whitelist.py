# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "UnityPy>=1.20",
#   "typer>=0.12",
#   "rich>=13.7",
# ]
# ///
"""Whitelist-only patcher for scene `locaId` fields.

This is intentionally narrow and dangerous-by-design: it only updates exact
`locaId` values listed in a TSV mapping and only in the bundles you point it at.
Use it for tiny, tested UI-key trials only.
"""

from __future__ import annotations

from pathlib import Path

import typer
import UnityPy
from rich.console import Console

app = typer.Typer(add_completion=False)
console = Console()


def _load_map(tsv: Path) -> dict[str, str]:
    lines = [ln for ln in tsv.read_text("utf-8").splitlines() if ln.strip()]
    if not lines:
        return {}
    header = lines[0].split("\t")
    try:
        src_idx = header.index("source")
        tgt_idx = header.index("target")
    except ValueError as e:
        raise typer.BadParameter("TSV must include `source` and `target` columns") from e

    out: dict[str, str] = {}
    for ln in lines[1:]:
        cols = ln.split("\t")
        if len(cols) <= max(src_idx, tgt_idx):
            continue
        src = cols[src_idx].replace(r"\n", "\n").replace(r"\t", "\t")
        tgt = cols[tgt_idx].replace(r"\n", "\n").replace(r"\t", "\t")
        if src and tgt:
            out[src] = tgt
    return out


def _load_project_map(project: Path) -> dict[str, str]:
    src_by_id: dict[str, str] = {}
    for ln in (project / "source.jsonl").read_text("utf-8").splitlines():
        if not ln.strip():
            continue
        rec = __import__("json").loads(ln)
        src_by_id[rec["id"]] = rec["text"]

    out: dict[str, str] = {}
    for ln in (project / "state.jsonl").read_text("utf-8").splitlines():
        if not ln.strip():
            continue
        rec = __import__("json").loads(ln)
        src = src_by_id.get(rec["id"])
        tgt = rec.get("manual") if rec.get("manual") is not None else rec.get("machine")
        if isinstance(src, str) and isinstance(tgt, str) and src != tgt:
            out[src] = tgt
    return out


def _lookup_target(mapping: dict[str, str], src: str) -> str | None:
    tgt = mapping.get(src)
    if tgt is not None:
        return tgt

    # Some locaId keys include trailing CR/LF variants; allow normalized fallback.
    norm_src = src.rstrip("\r\n")
    if norm_src != src:
        tgt = mapping.get(norm_src)
        if tgt is not None:
            return tgt

    return None


@app.command()
def main(
    input_dir: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),
    whitelist_tsv: Path | None = typer.Option(
        None, "--whitelist-tsv", exists=True, dir_okay=False
    ),
    project: Path | None = typer.Option(
        None,
        "--project",
        help="Optional tl project dir (source.jsonl/state.jsonl). If set, uses all translated source->target pairs.",
    ),
    out_dir: Path = typer.Option(..., "--out-dir", "-o"),
    bundles: list[str] = typer.Option(
        [],
        "--bundle",
        help="Bundle filename(s) to patch. If omitted, patches all .bundle files in input_dir.",
    ),
) -> None:
    if whitelist_tsv is None and project is None:
        raise typer.BadParameter("Provide either --whitelist-tsv or --project")

    mapping: dict[str, str] = {}
    if project is not None:
        mapping.update(_load_project_map(project))
    if whitelist_tsv is not None:
        mapping.update(_load_map(whitelist_tsv))

    if not mapping:
        raise typer.BadParameter("No source/target mappings found from provided inputs")

    names = bundles or sorted(p.name for p in input_dir.glob("*.bundle"))
    out_dir.mkdir(parents=True, exist_ok=True)

    total_hits = 0
    total_bundles = 0

    for name in names:
        bundle = input_dir / name
        if not bundle.exists():
            console.print(f"[yellow]missing[/]: {bundle}")
            continue

        env = UnityPy.load(str(bundle))
        hits = 0

        for obj in env.objects:
            if obj.type.name != "MonoBehaviour":
                continue
            try:
                tree = obj.read_typetree()
            except Exception:
                continue
            src = tree.get("locaId")
            if not isinstance(src, str):
                continue
            tgt = _lookup_target(mapping, src)
            if tgt and tgt != src:
                tree["locaId"] = tgt
                obj.save_typetree(tree)
                hits += 1

        out_path = out_dir / name
        out_path.write_bytes(env.file.save(packer="lz4"))
        total_hits += hits
        total_bundles += 1
        console.print(f"[cyan]{'patched' if hits else 'copied'}[/]: {name} ({hits} locaId updates)")

    console.print(f"[green]Done[/]: {total_bundles} bundles written, {total_hits} locaId updates")


if __name__ == "__main__":
    app()
