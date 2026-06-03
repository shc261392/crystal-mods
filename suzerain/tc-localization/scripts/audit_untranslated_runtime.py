# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "UnityPy>=1.20",
#   "typer>=0.12",
#   "rich>=13.7",
# ]
# ///
"""Audit untranslated runtime text in Suzerain bundles.

Scans:
- scene bundles: `locaId` and TMP `m_text`
- entity bundle TextAsset JSON leaf strings

Produces TSV + Markdown summary with concrete counts.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import typer
import UnityPy
from rich.console import Console

app = typer.Typer(add_completion=False)
console = Console()

TMP_TEXT_SCRIPT = 7477354737935883349
SCENE_FILES = (
    "scenes_scenes_assets_scenes_mainmenu.unity_6dd6ca6b71e2733b13cf2860d4a95134.bundle",
    "scenes_scenes_assets_scenes_rizia.unity_f3aa16cfb48dca20773754a9c19d5c1d.bundle",
    "scenes_scenes_assets_scenes_sordland.unity_6a29f2cab2ef8b301931a992da045ec1.bundle",
)
ENTITY_FILE = "defaultlocalgroup_assets_assets_database_entitytextassets.asset_7658ed792f0c4924d06b11829a6c36d1.bundle"

_RE_ASCII_ALPHA = re.compile(r"[A-Za-z]")
_RE_CJK = re.compile(r"[\u3400-\u9FFF]")


def _is_english_like(s: str) -> bool:
    s = s.strip()
    if not s:
        return False
    return bool(_RE_ASCII_ALPHA.search(s)) and not _RE_CJK.search(s)


def _load_project_map(project_dir: Path) -> dict[str, str]:
    src_by_id: dict[str, str] = {}
    for ln in (project_dir / "source.jsonl").read_text("utf-8").splitlines():
        if not ln.strip():
            continue
        rec = json.loads(ln)
        src_by_id[rec["id"]] = rec["text"]

    out: dict[str, str] = {}
    for ln in (project_dir / "state.jsonl").read_text("utf-8").splitlines():
        if not ln.strip():
            continue
        rec = json.loads(ln)
        src = src_by_id.get(rec["id"])
        tgt = rec.get("manual") if rec.get("manual") is not None else rec.get("machine")
        if isinstance(src, str) and isinstance(tgt, str):
            out[src] = tgt
    return out


def _iter_json_leaf_strings(node: Any):
    if isinstance(node, dict):
        for v in node.values():
            yield from _iter_json_leaf_strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from _iter_json_leaf_strings(v)
    elif isinstance(node, str):
        yield node


@app.command()
def main(
    game_aa_dir: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),
    translation_project: Path = typer.Option(..., "--translation-project", exists=True, file_okay=False),
    scene_project: Path = typer.Option(..., "--scene-project", exists=True, file_okay=False),
    out_dir: Path = typer.Option(Path("docs"), "--out-dir"),
) -> None:
    tr_map = _load_project_map(translation_project)
    sc_map = _load_project_map(scene_project)

    out_dir.mkdir(parents=True, exist_ok=True)
    scene_tsv = out_dir / "runtime-untranslated-scene.tsv"
    entity_tsv = out_dir / "runtime-untranslated-entity.tsv"
    report_md = out_dir / "runtime-untranslated-report.md"

    scene_rows: list[str] = ["bundle\tfield\tsource\ttarget\thas_mapping\tneeds_translation"]
    entity_rows: list[str] = ["source\ttarget\thas_mapping\tneeds_translation"]

    scene_counter = Counter()
    scene_unique: dict[tuple[str, str], set[str]] = defaultdict(set)

    for name in SCENE_FILES:
        bundle = game_aa_dir / name
        if not bundle.exists():
            continue
        env = UnityPy.load(str(bundle))
        for obj in env.objects:
            if obj.type.name != "MonoBehaviour":
                continue
            try:
                tree = obj.read_typetree()
            except Exception:
                continue

            # locaId
            loca = tree.get("locaId")
            if isinstance(loca, str) and loca.strip():
                scene_counter["loca_total_occ"] += 1
                scene_unique[(name, "locaId")].add(loca)
                if _is_english_like(loca):
                    scene_counter["loca_english_occ"] += 1
                    tgt = sc_map.get(loca.rstrip("\r\n"))
                    has_map = bool(tgt)
                    needs = has_map and (tgt == loca or _is_english_like(tgt))
                    scene_rows.append(
                        f"{name}\tlocaId\t{loca}\t{tgt or ''}\t{int(has_map)}\t{int(needs)}"
                    )

            # TMP m_text
            script = tree.get("m_Script")
            if isinstance(script, dict) and script.get("m_PathID") == TMP_TEXT_SCRIPT:
                txt = tree.get("m_text")
                if isinstance(txt, str) and txt.strip():
                    scene_counter["tmp_total_occ"] += 1
                    scene_unique[(name, "m_text")].add(txt)
                    if _is_english_like(txt):
                        scene_counter["tmp_english_occ"] += 1
                        tgt = sc_map.get(txt.rstrip("\r\n"))
                        has_map = bool(tgt)
                        needs = has_map and (tgt == txt or _is_english_like(tgt))
                        scene_rows.append(
                            f"{name}\tm_text\t{txt}\t{tgt or ''}\t{int(has_map)}\t{int(needs)}"
                        )

    # Entity TextAsset JSON leaves
    entity_counter = Counter()
    entity_unique: set[str] = set()
    entity_bundle = game_aa_dir / ENTITY_FILE
    if entity_bundle.exists():
        env = UnityPy.load(str(entity_bundle))
        for obj in env.objects:
            if obj.type.name != "TextAsset":
                continue
            tree = obj.read_typetree()
            script = tree.get("m_Script")
            if not isinstance(script, str) or not script.strip():
                continue
            try:
                data = json.loads(script)
            except Exception:
                continue
            for s in _iter_json_leaf_strings(data):
                if not s.strip():
                    continue
                entity_counter["total_occ"] += 1
                entity_unique.add(s)
                if _is_english_like(s):
                    entity_counter["english_occ"] += 1
                    tgt = tr_map.get(s.rstrip("\r\n"))
                    has_map = bool(tgt)
                    needs = has_map and (tgt == s or _is_english_like(tgt))
                    entity_rows.append(f"{s}\t{tgt or ''}\t{int(has_map)}\t{int(needs)}")

    scene_tsv.write_text("\n".join(scene_rows) + "\n", "utf-8")
    entity_tsv.write_text("\n".join(entity_rows) + "\n", "utf-8")

    scene_loca_unique = len({r.split("\t")[2] for r in scene_rows[1:] if "\tlocaId\t" in r})
    scene_tmp_unique = len({r.split("\t")[2] for r in scene_rows[1:] if "\tm_text\t" in r})
    entity_eng_unique = len({r.split("\t")[0] for r in entity_rows[1:]})

    mapped_scene = sum(1 for r in scene_rows[1:] if r.endswith("\t0") or r.endswith("\t1"))
    mapped_entity = sum(1 for r in entity_rows[1:] if "\t1\t" in r)

    report = [
        "# Runtime untranslated audit",
        "",
        "## Scene bundles",
        f"- locaId english-like occurrences: {scene_counter['loca_english_occ']}",
        f"- locaId english-like unique: {scene_loca_unique}",
        f"- TMP m_text english-like occurrences: {scene_counter['tmp_english_occ']}",
        f"- TMP m_text english-like unique: {scene_tmp_unique}",
        f"- Detailed rows: `{scene_tsv.name}`",
        "",
        "## Entity bundle",
        f"- english-like leaf-string occurrences: {entity_counter['english_occ']}",
        f"- english-like leaf-string unique: {entity_eng_unique}",
        f"- Detailed rows: `{entity_tsv.name}`",
        "",
        "## Notes",
        "- `has_mapping=1` means the text exists in the translation project map.",
        "- `needs_translation=1` marks mapped entries whose target remains english-like.",
    ]
    report_md.write_text("\n".join(report) + "\n", "utf-8")

    console.print(f"[green]Wrote[/] {scene_tsv}")
    console.print(f"[green]Wrote[/] {entity_tsv}")
    console.print(f"[green]Wrote[/] {report_md}")


if __name__ == "__main__":
    app()
