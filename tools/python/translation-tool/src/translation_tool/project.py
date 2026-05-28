"""Project layout and state model.

A project is a directory containing:
  - project.json   config (src lang, tgt lang, backend defaults)
  - source.jsonl   input units, one per line: {"id": str, "text": str}
  - glossary.tsv   tab-separated src<TAB>tgt rules
  - state.jsonl    per-unit state: {"id": str, "machine": str|null,
                                    "manual": str|null, "status": str}

Status values: "pending" | "translated" | "reviewed" | "final".
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class ProjectConfig:
    src_lang: str
    tgt_lang: str
    backend: str = "manual"
    model: str = "gemini-3.1-flash-lite"


@dataclass
class Unit:
    id: str
    text: str


@dataclass
class State:
    id: str
    machine: str | None = None
    manual: str | None = None
    status: str = "pending"

    def final_text(self) -> str | None:
        return self.manual if self.manual is not None else self.machine


@dataclass
class Project:
    root: Path
    config: ProjectConfig
    units: list[Unit] = field(default_factory=list)
    state: dict[str, State] = field(default_factory=dict)

    @property
    def project_json(self) -> Path:
        return self.root / "project.json"

    @property
    def source_jsonl(self) -> Path:
        return self.root / "source.jsonl"

    @property
    def glossary_tsv(self) -> Path:
        return self.root / "glossary.tsv"

    @property
    def state_jsonl(self) -> Path:
        return self.root / "state.jsonl"

    @classmethod
    def load(cls, root: Path) -> Project:
        cfg = ProjectConfig(**json.loads((root / "project.json").read_text("utf-8")))
        units = [
            Unit(**json.loads(line))
            for line in (root / "source.jsonl").read_text("utf-8").splitlines()
            if line.strip()
        ]
        state: dict[str, State] = {}
        state_path = root / "state.jsonl"
        if state_path.exists():
            for line in state_path.read_text("utf-8").splitlines():
                if not line.strip():
                    continue
                rec = json.loads(line)
                state[rec["id"]] = State(**rec)
        for u in units:
            state.setdefault(u.id, State(id=u.id))
        return cls(root=root, config=cfg, units=units, state=state)

    def save_state(self) -> None:
        lines = [json.dumps(asdict(self.state[u.id]), ensure_ascii=False) for u in self.units]
        self.state_jsonl.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def save_config(self) -> None:
        self.project_json.write_text(
            json.dumps(asdict(self.config), indent=2, ensure_ascii=False), encoding="utf-8"
        )


def init_project(
    root: Path,
    source: Path,
    src_lang: str,
    tgt_lang: str,
    backend: str,
    model: str,
) -> Project:
    root.mkdir(parents=True, exist_ok=True)
    cfg = ProjectConfig(src_lang=src_lang, tgt_lang=tgt_lang, backend=backend, model=model)
    units = _read_source(source)
    project = Project(root=root, config=cfg, units=units, state={u.id: State(id=u.id) for u in units})
    project.save_config()
    project.source_jsonl.write_text(
        "\n".join(json.dumps(asdict(u), ensure_ascii=False) for u in units) + "\n",
        encoding="utf-8",
    )
    if not project.glossary_tsv.exists():
        project.glossary_tsv.write_text("# src\ttgt\n", encoding="utf-8")
    project.save_state()
    return project


def _read_source(path: Path) -> list[Unit]:
    text = path.read_text("utf-8")
    if path.suffix.lower() == ".jsonl":
        return [
            Unit(**json.loads(line))
            for line in text.splitlines()
            if line.strip()
        ]
    if path.suffix.lower() == ".json":
        data = json.loads(text)
        if isinstance(data, dict):
            return [Unit(id=k, text=v) for k, v in data.items()]
        return [Unit(**d) for d in data]
    if path.suffix.lower() in {".csv", ".tsv"}:
        sep = "\t" if path.suffix.lower() == ".tsv" else ","
        out: list[Unit] = []
        for i, line in enumerate(text.splitlines()):
            if not line.strip():
                continue
            parts = line.split(sep, 1)
            if len(parts) == 2:
                out.append(Unit(id=parts[0], text=parts[1]))
            else:
                out.append(Unit(id=str(i), text=parts[0]))
        return out
    raise ValueError(f"Unsupported source format: {path.suffix}")
