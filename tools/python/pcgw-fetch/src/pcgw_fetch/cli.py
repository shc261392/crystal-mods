"""`pcgw-fetch` CLI."""

from __future__ import annotations

import sys
import urllib.parse
from pathlib import Path
from typing import Annotated

import typer

from .client import PCGWClient
from .jsonc import read_jsonc, write_metadata
from .normalize import build_metadata

app = typer.Typer(add_completion=False, help="Fetch PCGW metadata → metadata.jsonc")


def _pcgw_url(page: str) -> str:
    return "https://www.pcgamingwiki.com/wiki/" + urllib.parse.quote(page.replace(" ", "_"))


def _resolve_page(
    client: PCGWClient,
    *,
    steam_appid: str | None,
    page: str | None,
    search: str | None,
) -> str:
    if page:
        return page
    if steam_appid:
        resolved = client.resolve_by_steam_appid(steam_appid)
        if not resolved:
            typer.secho(f"No PCGW page found for Steam App ID {steam_appid}", fg="red")
            raise typer.Exit(2)
        return resolved
    if search:
        hits = client.opensearch(search, limit=5)
        if not hits:
            typer.secho(f"No PCGW match for '{search}'", fg="red")
            raise typer.Exit(2)
        if len(hits) > 1:
            typer.secho(f"Multiple matches for '{search}':", fg="yellow")
            for h in hits:
                typer.echo(f"  - {h}")
            typer.secho(f"Using first: {hits[0]}", fg="yellow")
        return hits[0]
    typer.secho("Provide one of --steam-appid / --page / --search / --refresh", fg="red")
    raise typer.Exit(2)


def _do_fetch(page: str, out: Path, *, merge_existing: bool) -> None:
    with PCGWClient() as client:
        infobox = client.fetch_infobox(page)
        if not infobox:
            typer.secho(f"Page '{page}' has no Infobox_game data", fg="red")
            raise typer.Exit(3)
        api_row = client.fetch_api_table(page)
        os_row = client.fetch_os_support(page)

    data = build_metadata(
        page=page,
        infobox=infobox,
        api_row=api_row,
        os_row=os_row,
        pcgw_url=_pcgw_url(page),
    )
    write_metadata(out, data, merge_existing=merge_existing)
    typer.secho(f"Wrote {out}", fg="green")


@app.command()
def fetch(
    out: Annotated[Path, typer.Option("--out", "-o", help="Output metadata.jsonc path")],
    steam_appid: Annotated[str | None, typer.Option("--steam-appid")] = None,
    page: Annotated[str | None, typer.Option("--page", help="Exact PCGW page name")] = None,
    search: Annotated[str | None, typer.Option("--search", help="Fuzzy game name search")] = None,
) -> None:
    """Fetch metadata for a game and write metadata.jsonc."""
    with PCGWClient() as client:
        resolved = _resolve_page(client, steam_appid=steam_appid, page=page, search=search)
    _do_fetch(resolved, out, merge_existing=False)


@app.command()
def refresh(
    path: Annotated[Path, typer.Argument(help="Existing metadata.jsonc to refresh")],
) -> None:
    """Re-fetch using the pcgwPage in the file; preserve fields marked _manual."""
    if not path.exists():
        typer.secho(f"File not found: {path}", fg="red")
        raise typer.Exit(2)
    existing = read_jsonc(path)
    page = existing.get("pcgwPage")
    if not page:
        typer.secho(f"{path} has no 'pcgwPage' field", fg="red")
        raise typer.Exit(2)
    _do_fetch(page, path, merge_existing=True)


def main() -> None:  # pragma: no cover
    app()


if __name__ == "__main__":  # pragma: no cover
    sys.exit(app())
