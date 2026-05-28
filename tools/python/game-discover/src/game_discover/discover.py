"""Inspect a PC game install and report what's there.

Heuristics-only: no game files are modified. Output is consumable by a
human and/or a downstream mod-planner.

Performance: walks the install root exactly once with os.walk and derives
all stats from the captured (path, size) list. This matters on WSL DrvFs
where each syscall against /mnt/<drive> costs ~1 ms.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

_HUMAN_UNITS = ("B", "KB", "MB", "GB", "TB")


def human_size(n: int) -> str:
    f = float(n)
    for u in _HUMAN_UNITS:
        if f < 1024 or u == _HUMAN_UNITS[-1]:
            return f"{f:.1f} {u}"
        f /= 1024
    return f"{f:.1f} TB"


@dataclass(frozen=True)
class FileRow:
    rel: str
    size: int


def _walk(root: Path) -> list[FileRow]:
    rows: list[FileRow] = []
    root_str = str(root)
    for dirpath, dirnames, filenames in os.walk(root_str, followlinks=False):
        dirnames.sort()
        for name in filenames:
            full = os.path.join(dirpath, name)
            try:
                st = os.stat(full, follow_symlinks=False)
            except OSError:
                continue
            rel = os.path.relpath(full, root_str).replace(os.sep, "/")
            rows.append(FileRow(rel, st.st_size))
    return rows


@dataclass
class FileEntry:
    path: str
    size: int

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "size": self.size, "size_human": human_size(self.size)}


@dataclass
class UnityReport:
    data_dir: str
    scripting_backend: str
    unity_version: str | None
    managed_dll_count: int
    plugins: list[str] = field(default_factory=list)
    streaming_assets_present: bool = False
    streaming_assets_top: list[FileEntry] = field(default_factory=list)
    bundles_top: list[FileEntry] = field(default_factory=list)
    locale_candidates: list[FileEntry] = field(default_factory=list)
    bepinex_installed: bool = False
    melonloader_installed: bool = False


@dataclass
class UnrealReport:
    paks_dir: str
    paks: list[FileEntry] = field(default_factory=list)


@dataclass
class GameReport:
    root: str
    total_size: int
    file_count: int
    engine: str
    executables: list[FileEntry] = field(default_factory=list)
    unity: UnityReport | None = None
    unreal: UnrealReport | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["total_size_human"] = human_size(self.total_size)
        return d


_UNITY_VERSION_RE = re.compile(rb"(\d+\.\d+\.\d+[a-z]?\d*)\x00")
_BUNDLE_EXTS = {".assets", ".resource", ".bundle", ".ress", ".resS"}
_LOCALE_RE = re.compile(r"(loc|lang|text|translat|i18n|string|message)", re.IGNORECASE)


def _detect_unity_version(root: Path, data_dir_rel: str) -> str | None:
    data_dir = root / data_dir_rel
    for cand in ("globalgamemanagers", "data.unity3d"):
        p = data_dir / cand
        if not p.is_file():
            continue
        try:
            with p.open("rb") as f:
                blob = f.read(4096)
        except OSError:
            continue
        m = _UNITY_VERSION_RE.search(blob)
        if m:
            return m.group(1).decode("ascii", errors="ignore")
    bc = data_dir / "boot.config"
    if bc.is_file():
        try:
            for line in bc.read_text(errors="ignore").splitlines():
                if line.startswith("unity-version="):
                    return line.split("=", 1)[1].strip()
        except OSError:
            pass
    return None


def _find_unity_data_dir(rows: list[FileRow]) -> str | None:
    for r in rows:
        parts = r.rel.split("/")
        if len(parts) == 2 and parts[0].endswith("_Data") and parts[1] in (
            "globalgamemanagers",
            "data.unity3d",
        ):
            return parts[0]
    return None


def _scan_unity(root: Path, rows: list[FileRow], data_dir_rel: str) -> UnityReport:
    data_prefix = data_dir_rel + "/"
    managed_prefix = data_prefix + "Managed/"
    plugins_prefix = data_prefix + "Plugins/"
    sa_prefix = data_prefix + "StreamingAssets/"

    has_il2cpp = any(r.rel in ("GameAssembly.dll", "GameAssembly.so") for r in rows)
    managed_dlls = [r for r in rows if r.rel.startswith(managed_prefix) and r.rel.endswith(".dll")]
    if has_il2cpp:
        backend = "il2cpp"
    elif managed_dlls:
        backend = "mono"
    else:
        backend = "unknown"

    plugins = sorted(
        {r.rel[len(plugins_prefix):].split("/", 1)[0] for r in rows if r.rel.startswith(plugins_prefix)}
    )[:40]

    sa_rows = [r for r in rows if r.rel.startswith(sa_prefix)]
    sa_rows.sort(key=lambda r: r.size, reverse=True)
    sa_top = [FileEntry(r.rel, r.size) for r in sa_rows[:25]]

    bundle_rows = [r for r in rows if Path(r.rel).suffix in _BUNDLE_EXTS]
    bundle_rows.sort(key=lambda r: r.size, reverse=True)
    bundle_top = [FileEntry(r.rel, r.size) for r in bundle_rows[:20]]

    loc_rows = [r for r in rows if _LOCALE_RE.search(os.path.basename(r.rel))]
    loc_rows.sort(key=lambda r: r.size, reverse=True)
    loc_top = [FileEntry(r.rel, r.size) for r in loc_rows[:40]]

    bepinex = any(r.rel.startswith("BepInEx/") for r in rows) or any(
        r.rel == "winhttp.dll" for r in rows
    )
    melon = any(r.rel.startswith("MelonLoader/") for r in rows)

    return UnityReport(
        data_dir=data_dir_rel,
        scripting_backend=backend,
        unity_version=_detect_unity_version(root, data_dir_rel),
        managed_dll_count=len(managed_dlls),
        plugins=plugins,
        streaming_assets_present=bool(sa_rows),
        streaming_assets_top=sa_top,
        bundles_top=bundle_top,
        locale_candidates=loc_top,
        bepinex_installed=bepinex,
        melonloader_installed=melon,
    )


def _find_unreal_paks(rows: list[FileRow]) -> tuple[str | None, list[FileRow]]:
    by_pakdir: dict[str, list[FileRow]] = {}
    for r in rows:
        if not r.rel.endswith(".pak"):
            continue
        parent = os.path.dirname(r.rel)
        if parent.endswith("/Content/Paks") or parent == "Content/Paks":
            by_pakdir.setdefault(parent, []).append(r)
    if not by_pakdir:
        return None, []
    parent = max(by_pakdir, key=lambda k: sum(r.size for r in by_pakdir[k]))
    return parent, by_pakdir[parent]


def _scan_unreal(paks_dir: str, paks: list[FileRow]) -> UnrealReport:
    paks_sorted = sorted(paks, key=lambda r: r.size, reverse=True)
    return UnrealReport(
        paks_dir=paks_dir,
        paks=[FileEntry(r.rel, r.size) for r in paks_sorted[:50]],
    )


def _executables(rows: list[FileRow]) -> list[FileEntry]:
    exes = [r for r in rows if "/" not in r.rel and r.rel.lower().endswith(".exe")]
    exes.sort(key=lambda r: r.size, reverse=True)
    return [FileEntry(r.rel, r.size) for r in exes[:10]]


def inspect(root: Path) -> GameReport:
    root = root.resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Not a directory: {root}")

    rows = _walk(root)
    total_size = sum(r.size for r in rows)

    notes: list[str] = []
    engine = "unknown"
    unity: UnityReport | None = None
    unreal: UnrealReport | None = None

    data_dir_rel = _find_unity_data_dir(rows)
    if data_dir_rel is not None:
        engine = "unity"
        unity = _scan_unity(root, rows, data_dir_rel)
    else:
        paks_dir, paks = _find_unreal_paks(rows)
        if paks_dir is not None:
            engine = "unreal"
            unreal = _scan_unreal(paks_dir, paks)

    if engine == "unknown":
        notes.append("Could not auto-detect engine; manual inspection required.")

    return GameReport(
        root=str(root),
        total_size=total_size,
        file_count=len(rows),
        engine=engine,
        executables=_executables(rows),
        unity=unity,
        unreal=unreal,
        notes=notes,
    )


def _files_md(files: list[FileEntry]) -> str:
    if not files:
        return "_(none)_\n"
    return "\n".join(f"- `{f.path}` — {human_size(f.size)}" for f in files) + "\n"


def render_markdown(report: GameReport, title: str | None = None) -> str:
    out: list[str] = []
    out.append(f"# Discovery report: {title or Path(report.root).name}\n")
    out.append(f"- **Install root:** `{report.root}`")
    out.append(f"- **Total size:** {human_size(report.total_size)} ({report.file_count} files)")
    out.append(f"- **Detected engine:** `{report.engine}`")
    if report.notes:
        out.append("\n**Notes:**")
        for n in report.notes:
            out.append(f"- {n}")
    out.append("\n## Executables")
    out.append(_files_md(report.executables))

    if report.unity is not None:
        u = report.unity
        out.append("## Unity")
        out.append(f"- **Data folder:** `{u.data_dir}`")
        out.append(f"- **Scripting backend:** `{u.scripting_backend}`")
        out.append(f"- **Unity version (best-effort):** `{u.unity_version or 'unknown'}`")
        out.append(f"- **Managed DLLs:** {u.managed_dll_count}")
        out.append(f"- **BepInEx installed:** {u.bepinex_installed}")
        out.append(f"- **MelonLoader installed:** {u.melonloader_installed}")
        out.append(f"- **StreamingAssets present:** {u.streaming_assets_present}")
        if u.plugins:
            out.append("\n### Native plugins (top 40)\n")
            out.append("\n".join(f"- `{p}`" for p in u.plugins) + "\n")
        out.append("\n### StreamingAssets (top 25 by size)\n")
        out.append(_files_md(u.streaming_assets_top))
        out.append("### Asset bundles (top 20 by size)\n")
        out.append(_files_md(u.bundles_top))
        out.append("### Locale candidates (filename heuristic)\n")
        out.append(_files_md(u.locale_candidates))

    if report.unreal is not None:
        ue = report.unreal
        out.append("## Unreal")
        out.append(f"- **Paks dir:** `{ue.paks_dir}`")
        out.append("\n### Pak files (top 50 by size)\n")
        out.append(_files_md(ue.paks))

    return "\n".join(out)


def to_json(report: GameReport) -> str:
    return json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
