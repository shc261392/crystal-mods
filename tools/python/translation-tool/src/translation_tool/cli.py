"""CLI for the translation tool."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from .backends import get_backend
from .glossary import (
    GlossaryRule,
    detect_terms,
    load_glossary,
    protect,
    restore,
    split_glossary,
    write_glossary,
)
from .project import Project, init_project

app = typer.Typer(add_completion=False, no_args_is_help=True, help=__doc__)
glossary_app = typer.Typer(add_completion=False, no_args_is_help=True, help="Build/manage the glossary.")
app.add_typer(glossary_app, name="glossary")
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


@glossary_app.command("build")
def glossary_build(
    project_dir: Path = typer.Argument(..., exists=True, file_okay=False),
    min_count: int = typer.Option(5, "--min-count", help="Minimum corpus frequency for a candidate term"),
    max_terms: int = typer.Option(400, "--max-terms", help="Cap on number of auto terms"),
    backend: Optional[str] = typer.Option(None, "--backend", help="Override project backend"),
    model: Optional[str] = typer.Option(None, "--model"),
    context: str = typer.Option("", "--context", help="Short game description to guide term translation"),
    batch_size: int = typer.Option(50, "--batch-size", help="Terms per request when the backend supports batching"),
    rebuild: bool = typer.Option(False, "--rebuild", help="Re-translate all auto terms (ignore cached auto block)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Only detect & list candidate terms; no API calls or writes"),
) -> None:
    """Discover recurring proper nouns/named entities and translate them once.

    Detected terms are merged into glossary.tsv (manual entries preserved and
    given precedence). Run this before `translate` so names stay consistent.
    """
    p = Project.load(project_dir)
    texts = [u.text for u in p.units]
    candidates = detect_terms(texts, min_count=min_count, max_terms=max_terms)
    console.print(f"[cyan]Detected {len(candidates)} candidate terms[/] (min_count={min_count})")

    manual, prev_auto = split_glossary(p.glossary_tsv)
    manual_keys = {r.src for r in manual}
    prev_auto_map = {} if rebuild else {r.src: r.tgt for r in prev_auto}

    if dry_run:
        for term, count in candidates[:60]:
            mark = " (manual)" if term in manual_keys else ""
            console.print(f"  {count:>5}  {term}{mark}")
        if len(candidates) > 60:
            console.print(f"  ... and {len(candidates) - 60} more")
        return

    # Terms needing translation = detected, not already manual, not already auto-translated.
    to_translate = [t for t, _ in candidates if t not in manual_keys and t not in prev_auto_map]
    console.print(f"[cyan]{len(to_translate)} new terms to translate[/] "
                  f"({len(candidates) - len(to_translate)} already known)")

    cfg_backend = backend or p.config.backend
    cfg_model = model or p.config.model
    translations: dict[str, str] = dict(prev_auto_map)

    if to_translate:
        if cfg_backend == "manual":
            raise typer.BadParameter("Cannot translate terms with the 'manual' backend.")
        be = get_backend(cfg_backend, cfg_model)
        done = 0
        if hasattr(be, "translate_glossary") and batch_size > 1:
            for start in range(0, len(to_translate), batch_size):
                chunk = to_translate[start : start + batch_size]
                # Anchor consistency on manual terms + everything translated so far.
                known = {**{r.src: r.tgt for r in manual}, **translations}
                try:
                    results = be.translate_glossary(  # type: ignore[attr-defined]
                        chunk, p.config.src_lang, p.config.tgt_lang, context, known
                    )
                except Exception as e:  # noqa: BLE001
                    console.print(f"[red]Batch failed[/] at offset {start}: {e}")
                    break
                for term, tgt in zip(chunk, results):
                    if tgt:
                        translations[term] = tgt
                    done += 1
                console.print(f"  ... {min(start + batch_size, len(to_translate))}/{len(to_translate)} terms")
        else:
            for term in to_translate:
                try:
                    translations[term] = be.translate(term, p.config.src_lang, p.config.tgt_lang)
                except Exception as e:  # noqa: BLE001
                    console.print(f"[red]Failed[/] term={term!r}: {e}")
                    break
                done += 1

    # Build the auto block in detection rank order, only for translated terms.
    auto_rules = [
        GlossaryRule(src=term, tgt=translations[term])
        for term, _ in candidates
        if term in translations and translations[term]
    ]
    write_glossary(p.glossary_tsv, manual, auto_rules)
    console.print(
        f"[green]Wrote[/] {p.glossary_tsv} "
        f"({len(manual)} manual + {len(auto_rules)} auto terms)"
    )


@app.command()
def translate(
    project_dir: Path = typer.Argument(..., exists=True, file_okay=False),
    backend: Optional[str] = typer.Option(None, "--backend", help="Override project backend"),
    model: Optional[str] = typer.Option(None, "--model"),
    limit: int = typer.Option(0, "--limit", help="Only translate first N pending units (0 = all)"),
    redo: bool = typer.Option(False, "--redo", help="Re-translate units that already have a machine output"),
    batch_size: int = typer.Option(25, "--batch-size", help="Units per request when the backend supports batching"),
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

    todo = [u for u in p.units if u.text.strip() and (redo or p.state[u.id].machine is None)]
    if limit:
        todo = todo[:limit]
    total = len(todo)
    if total == 0:
        console.print("[yellow]Nothing to translate.[/]")
        return

    use_batch = hasattr(be, "translate_batch") and batch_size > 1
    done = 0

    if use_batch:
        for start in range(0, total, batch_size):
            chunk = todo[start : start + batch_size]
            protected_pairs = [protect(u.text, rules) for u in chunk]
            protected_texts = [pp[0] for pp in protected_pairs]
            try:
                results = be.translate_batch(  # type: ignore[attr-defined]
                    protected_texts, p.config.src_lang, p.config.tgt_lang
                )
            except Exception as e:  # noqa: BLE001
                console.print(f"[red]Batch failed[/] at offset {start}: {e}")
                p.save_state()
                break
            for u, (_, mapping), raw in zip(chunk, protected_pairs, results):
                st = p.state[u.id]
                if not raw:
                    # Fallback to a single-item call for this unit.
                    try:
                        single, smap = protect(u.text, rules)
                        raw = restore(be.translate(single, p.config.src_lang, p.config.tgt_lang), smap)
                    except Exception:  # noqa: BLE001
                        raw = ""
                    if raw:
                        st.machine = raw
                else:
                    st.machine = restore(raw, mapping)
                if st.machine and st.status == "pending":
                    st.status = "translated"
                done += 1
            p.save_state()
            console.print(f"  ... {min(start + batch_size, total)}/{total} processed, autosaved")
    else:
        for u in todo:
            st = p.state[u.id]
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
                console.print(f"  ... {done}/{total} translated, autosaved")
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
