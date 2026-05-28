"""CLI for the translation tool."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from .backends import get_backend
from .glossary import load_glossary, protect, restore
from .project import Project, init_project

app = typer.Typer(add_completion=False, no_args_is_help=True, help=__doc__)
console = Console()


@app.command()
def init(
    project_dir: Path = typer.Argument(..., help="Project directory to create."),
    source: Path = typer.Option(..., "--source", "-s", exists=True, help="Source file (jsonl/json/csv/tsv)."),
    src_lang: str = typer.Option("en", "--src-lang"),
    tgt_lang: str = typer.Option("zh-TW", "--tgt-lang"),
    backend: str = typer.Option("manual", "--backend", help="manual|google|gemini"),
    model: str = typer.Option("gemini-3.1-flash-lite", "--model"),
) -> None:
    """Create a project from a source file."""
    p = init_project(project_dir, source, src_lang, tgt_lang, backend, model)
    console.print(f"[green]Initialised[/] project at {p.root} ({len(p.units)} units)")


@app.command()
def translate(
    project_dir: Path = typer.Argument(..., exists=True, file_okay=False),
    backend: Optional[str] = typer.Option(None, "--backend", help="Override project backend"),
    model: Optional[str] = typer.Option(None, "--model"),
    limit: int = typer.Option(0, "--limit", help="Only translate first N pending units (0 = all)"),
    redo: bool = typer.Option(False, "--redo", help="Re-translate units that already have a machine output"),
) -> None:
    """Run the backend on pending units."""
    p = Project.load(project_dir)
    cfg_backend = backend or p.config.backend
    cfg_model = model or p.config.model
    if cfg_backend == "manual":
        console.print("[yellow]Backend is 'manual' \u2014 nothing to translate. Use `tl review` to fill in manually.[/]")
        return
    rules = load_glossary(p.glossary_tsv)
    be = get_backend(cfg_backend, cfg_model)
    done = 0
    for u in p.units:
        st = p.state[u.id]
        if st.machine is not None and not redo:
            continue
        if limit and done >= limit:
            break
        protected, mapping = protect(u.text, rules)
        try:
            raw = be.translate(protected, p.config.src_lang, p.config.tgt_lang)
        except Exception as e:  # noqa: BLE001
            console.print(f"[red]Failed[/] id={u.id}: {e}")
            break
        st.machine = restore(raw, mapping)
        if st.status == "pending":
            st.status = "translated"
        done += 1
        if done % 10 == 0:
            p.save_state()
            console.print(f"  ... {done} translated, autosaved")
    p.save_state()
    console.print(f"[green]Done[/]: {done} units translated, state saved")


@app.command()
def review(
    project_dir: Path = typer.Argument(..., exists=True, file_okay=False),
    only_status: Optional[str] = typer.Option(None, "--status", help="Filter: pending|translated|reviewed|final"),
) -> None:
    """Interactive review loop. Accept (a), edit (e), skip (s), quit (q)."""
    p = Project.load(project_dir)
    queue = [u for u in p.units if (only_status is None or p.state[u.id].status == only_status)]
    if not queue:
        console.print("[yellow]Nothing to review.[/]")
        return
    console.print(f"[cyan]Reviewing {len(queue)} units. Commands: (a)ccept (e)dit (s)kip (q)uit[/]")
    for i, u in enumerate(queue, 1):
        st = p.state[u.id]
        console.rule(f"[{i}/{len(queue)}] id={u.id} status={st.status}")
        console.print(Panel(u.text, title=f"source ({p.config.src_lang})", border_style="blue"))
        console.print(
            Panel(st.final_text() or "", title=f"current ({p.config.tgt_lang})", border_style="green")
        )
        cmd = input("> ").strip().lower()
        if cmd == "q":
            break
        if cmd == "s":
            continue
        if cmd == "e":
            console.print("[dim]Enter new text. End with a single '.' on a line.[/]")
            lines: list[str] = []
            while True:
                line = input()
                if line == ".":
                    break
                lines.append(line)
            st.manual = "\n".join(lines)
            st.status = "reviewed"
        elif cmd == "a":
            if st.manual is None and st.machine is not None:
                st.manual = st.machine
            st.status = "final"
        p.save_state()
    console.print("[green]Review session ended, state saved[/]")


@app.command()
def export(
    project_dir: Path = typer.Argument(..., exists=True, file_okay=False),
    out: Path = typer.Option(..., "--out", "-o"),
    fmt: str = typer.Option("jsonl", "--format", "-f", help="jsonl|json|autotranslator"),
    require_final: bool = typer.Option(False, "--require-final", help="Only export units with status=final"),
) -> None:
    """Emit the target translations to a file."""
    p = Project.load(project_dir)
    rows: list[tuple[str, str, str]] = []  # (id, source, target)
    for u in p.units:
        st = p.state[u.id]
        if require_final and st.status != "final":
            continue
        tgt = st.final_text()
        if tgt is None:
            continue
        rows.append((u.id, u.text, tgt))
    out.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "jsonl":
        out.write_text(
            "\n".join(json.dumps({"id": i, "source": s, "target": t}, ensure_ascii=False) for i, s, t in rows) + "\n",
            encoding="utf-8",
        )
    elif fmt == "json":
        out.write_text(
            json.dumps({i: t for i, _, t in rows}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    elif fmt == "autotranslator":
        # XUnity AutoTranslator format: source=target on each line
        out.write_text(
            "\n".join(f"{_at_escape(s)}={_at_escape(t)}" for _, s, t in rows) + "\n",
            encoding="utf-8",
        )
    else:
        raise typer.BadParameter(f"Unknown format: {fmt}")
    console.print(f"[green]Wrote[/] {out} ({len(rows)} entries)")


@app.command()
def status(project_dir: Path = typer.Argument(..., exists=True, file_okay=False)) -> None:
    """Show counts per status."""
    p = Project.load(project_dir)
    counts: dict[str, int] = {}
    for u in p.units:
        s = p.state[u.id].status
        counts[s] = counts.get(s, 0) + 1
    console.print(f"Project: {p.root}")
    console.print(f"Languages: {p.config.src_lang} \u2192 {p.config.tgt_lang}")
    console.print(f"Backend: {p.config.backend} (model={p.config.model})")
    console.print(f"Total units: {len(p.units)}")
    for s in ("pending", "translated", "reviewed", "final"):
        console.print(f"  {s}: {counts.get(s, 0)}")


def _at_escape(s: str) -> str:
    # XUnity AutoTranslator: escape \r \n as literal \r \n
    return s.replace("\\", "\\\\").replace("\r", "\\r").replace("\n", "\\n").replace("=", "\\=")


if __name__ == "__main__":
    app()
