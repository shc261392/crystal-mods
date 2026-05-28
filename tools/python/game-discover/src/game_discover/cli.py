from __future__ import annotations

from pathlib import Path

import typer

from . import __version__
from .discover import inspect, render_markdown, to_json


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


def main(
    path: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    out: Path = typer.Option(None, "--out", "-o", help="Write markdown report to this path."),
    json_out: Path = typer.Option(None, "--json", help="Write JSON report to this path."),
    title: str = typer.Option(None, "--title", help="Override report title."),
    version: bool = typer.Option(
        False, "--version", callback=_version_callback, is_eager=True, help="Show version and exit."
    ),
) -> None:
    """Inspect a PC game install directory."""
    report = inspect(path)
    md = render_markdown(report, title=title)
    if out is not None:
        out.write_text(md, encoding="utf-8")
        typer.echo(f"Wrote {out}")
    else:
        typer.echo(md)
    if json_out is not None:
        json_out.write_text(to_json(report), encoding="utf-8")
        typer.echo(f"Wrote {json_out}")


def app() -> None:
    typer.run(main)
