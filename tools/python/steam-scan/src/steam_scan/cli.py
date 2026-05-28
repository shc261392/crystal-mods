"""`steam-scan` CLI."""

from __future__ import annotations

import json
from typing import Annotated

import typer

from .discover import discover_libraries, enumerate_games

app = typer.Typer(add_completion=False, help="Locate Steam libraries and installed games.")


def _filter(games, *, name: str | None, appid: str | None):
    if name:
        needle = name.lower()
        games = [g for g in games if needle in g.name.lower() or needle in g.installdir.lower()]
    if appid:
        games = [g for g in games if g.appid == appid]
    return games


@app.callback(invoke_without_command=True)
def main(
    json_out: Annotated[bool, typer.Option("--json", help="Emit JSON")] = False,
    name: Annotated[str | None, typer.Option("--name", help="Substring filter")] = None,
    appid: Annotated[str | None, typer.Option("--appid", help="Steam App ID filter")] = None,
) -> None:
    libraries = discover_libraries()
    games = _filter(enumerate_games(libraries), name=name, appid=appid)

    if json_out:
        payload = {
            "libraries": [{"path": str(lib.path), "platform": lib.platform} for lib in libraries],
            "games": [g.to_dict() for g in games],
        }
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    if not libraries:
        typer.secho("No Steam libraries detected.", fg="yellow")
        raise typer.Exit(1)

    typer.secho(f"Steam libraries ({len(libraries)}):", fg="cyan", bold=True)
    for lib in libraries:
        typer.echo(f"  [{lib.platform}] {lib.path}")

    typer.echo()
    typer.secho(f"Installed games ({len(games)}):", fg="cyan", bold=True)
    if not games:
        typer.secho("  (none)", fg="yellow")
        return
    width = max(len(g.name) for g in games)
    for g in sorted(games, key=lambda x: x.name.lower()):
        size = f"{g.size_on_disk / (1024**3):.1f} GB" if g.size_on_disk else "—"
        typer.echo(f"  {g.appid:>10}  {g.name:<{width}}  {size:>8}  {g.install_path}")


if __name__ == "__main__":  # pragma: no cover
    app()
