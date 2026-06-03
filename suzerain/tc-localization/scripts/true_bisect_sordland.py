# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "UnityPy>=1.20",
#   "typer>=0.12",
#   "rich>=13.7",
# ]
# ///
"""True bisect runner for Sordland TMP scene text with hard coverage gates.

This script enforces:
1) 100% extractable TMP text coverage in translation project source
2) 100% translatability (each extractable source has a non-empty final target)

If either gate fails, the script exits non-zero with explicit diagnostics.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

import typer
import UnityPy
from rich.console import Console

app = typer.Typer(add_completion=False)
console = Console()

TMP_TEXT_SCRIPT = 7477354737935883349  # TextMeshProUGUI
SORDLAND_FILE = "scenes_scenes_assets_scenes_sordland.unity_6a29f2cab2ef8b301931a992da045ec1.bundle"


@dataclass(frozen=True)
class Pair:
    source: str
    target: str


def _extract_unique_tmp_texts(bundle_path: Path) -> list[str]:
    env = UnityPy.load(str(bundle_path))
    out: list[str] = []
    seen: set[str] = set()

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
        if isinstance(text, str) and text.strip() and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _load_translation_map(project_dir: Path) -> dict[str, str]:
    src_by_id: dict[str, str] = {}
    for line in (project_dir / "source.jsonl").read_text("utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        src_by_id[rec["id"]] = rec["text"]

    mapping: dict[str, str] = {}
    for line in (project_dir / "state.jsonl").read_text("utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        tgt = rec.get("manual") if rec.get("manual") is not None else rec.get("machine")
        src = src_by_id.get(rec["id"])
        if not src or tgt is None:
            continue
        tgt = str(tgt)
        if src in mapping and mapping[src] != tgt:
            raise RuntimeError(
                f"Conflicting targets for source text: {src!r}\n"
                f"  existing={mapping[src]!r}\n"
                f"  incoming={tgt!r}"
            )
        mapping[src] = tgt
    return mapping


def _hard_gate_coverage(extractable: list[str], mapping: dict[str, str]) -> None:
    missing_in_project = [s for s in extractable if s not in mapping]
    empty_target = [s for s in extractable if s in mapping and not mapping[s].strip()]

    if missing_in_project or empty_target:
        console.print("[red]HARD GATE FAILED[/]: translation coverage is not 100%.")
        console.print(f"extractable unique TMP texts: {len(extractable)}")
        console.print(f"missing in translation map: {len(missing_in_project)}")
        console.print(f"empty translation target: {len(empty_target)}")

        preview = 20
        if missing_in_project:
            console.print("\n[red]Missing sources (first 20):[/]")
            for s in missing_in_project[:preview]:
                console.print(f"  - {s}")
        if empty_target:
            console.print("\n[red]Empty targets (first 20):[/]")
            for s in empty_target[:preview]:
                console.print(f"  - {s}")

        raise typer.Exit(code=2)


def _write_tsv(path: Path, rows: list[Pair], note: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["source\ttarget\tnote"]
    lines.extend(f"{r.source}\t{r.target}\t{note}" for r in rows)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _split_ab(rows: list[Pair]) -> tuple[list[Pair], list[Pair]]:
    n = len(rows)
    half = (n + 1) // 2
    return rows[:half], rows[half:]


def _load_tsv_source_target(path: Path) -> dict[str, str]:
    lines = [ln for ln in path.read_text("utf-8").splitlines() if ln.strip()]
    if not lines:
        return {}
    header = lines[0].split("\t")
    try:
        i_src = header.index("source")
        i_tgt = header.index("target")
    except ValueError as e:
        raise RuntimeError(f"TSV must have source/target columns: {path}") from e

    out: dict[str, str] = {}
    for ln in lines[1:]:
        cols = ln.split("\t")
        if len(cols) <= max(i_src, i_tgt):
            continue
        s = cols[i_src]
        t = cols[i_tgt]
        if s:
            out[s] = t
    return out


def _patch_sordland_tmp(base_bundle: Path, mapping: dict[str, str], out_bundle: Path) -> int:
    env = UnityPy.load(str(base_bundle))
    hits = 0

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
        if not isinstance(src, str):
            continue
        tgt = mapping.get(src)
        if tgt is not None and tgt != src:
            tree["m_text"] = tgt
            obj.save_typetree(tree)
            hits += 1

    out_bundle.parent.mkdir(parents=True, exist_ok=True)
    out_bundle.write_bytes(env.file.save(packer="lz4"))
    return hits


@app.command()
def prepare(
    game_aa_dir: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),
    project_dir: Path = typer.Option(..., "--project", "-p", exists=True, file_okay=False),
    docs_dir: Path = typer.Option(Path("docs"), "--docs-dir"),
) -> None:
    """Build full-corpus bisect files with hard 100% translation coverage gates."""
    source_bundle = game_aa_dir / SORDLAND_FILE
    if not source_bundle.exists():
        raise typer.BadParameter(f"Sordland bundle not found: {source_bundle}")

    extractable = _extract_unique_tmp_texts(source_bundle)
    mapping = _load_translation_map(project_dir)
    _hard_gate_coverage(extractable, mapping)

    full_rows = [Pair(source=s, target=mapping[s]) for s in extractable]
    a_rows, b_rows = _split_ab(full_rows)

    _write_tsv(docs_dir / "sordland-full-bisect.tsv", full_rows, "full-corpus")
    _write_tsv(docs_dir / "sordland-full-bisect-a.tsv", a_rows, "full-corpus-half-a")
    _write_tsv(docs_dir / "sordland-full-bisect-b.tsv", b_rows, "full-corpus-half-b")

    console.print("[green]Prepared true full-corpus bisect files[/]")
    console.print(f"extractable unique TMP strings: {len(extractable)}")
    console.print(f"A size: {len(a_rows)}")
    console.print(f"B size: {len(b_rows)}")


@app.command()
def apply(
    game_aa_dir: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),
    tsv: Path = typer.Option(..., "--tsv", exists=True, dir_okay=False),
    base_bundle: Path | None = typer.Option(
        None,
        "--base-bundle",
        help="Optional explicit base Sordland bundle. Defaults to current game bundle.",
    ),
    out_dir: Path = typer.Option(Path("build"), "--out-dir"),
    deploy: bool = typer.Option(True, "--deploy/--no-deploy"),
) -> None:
    """Apply one bisect TSV set to Sordland TMP text and optionally deploy."""
    mapping = _load_tsv_source_target(tsv)
    if not mapping:
        raise typer.BadParameter(f"No source/target rows found in {tsv}")

    source_bundle = base_bundle or (game_aa_dir / SORDLAND_FILE)
    if not source_bundle.exists():
        raise typer.BadParameter(f"Base Sordland bundle not found: {source_bundle}")

    out_bundle = out_dir / SORDLAND_FILE
    hits = _patch_sordland_tmp(source_bundle, mapping, out_bundle)
    console.print(f"[green]Patched[/]: {hits} TMP m_text replacements -> {out_bundle}")

    if deploy:
        target = game_aa_dir / SORDLAND_FILE
        shutil.copy2(out_bundle, target)
        console.print(f"[green]Deployed[/]: {target}")


if __name__ == "__main__":
    app()
