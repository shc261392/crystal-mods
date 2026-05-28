"""Library discovery + ACF/VDF parsing."""

from __future__ import annotations

import os
import re
import string
from dataclasses import dataclass
from pathlib import Path

# ── VDF / ACF tiny parser ────────────────────────────────────────────────────
# Steam's text VDF is a tree of "key" "value" pairs with nested blocks.
# We only need leaf string values — a regex pass is enough.

_PAIR_RE = re.compile(r'"([^"]+)"\s+"([^"]*)"')


def parse_vdf_flat(text: str) -> dict[str, str]:
    """Return a flat last-wins map of "key" "value" pairs (ignores nesting)."""
    return dict(_PAIR_RE.findall(text))


def parse_libraryfolders(text: str) -> list[str]:
    """Extract all `path` values from a libraryfolders.vdf file."""
    paths: list[str] = []
    for m in re.finditer(r'"path"\s+"([^"]+)"', text):
        # VDF escapes backslashes — collapse \\ to \ (Windows paths).
        paths.append(m.group(1).replace("\\\\", "\\"))
    return paths


# ── Platform discovery ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class Library:
    path: Path
    platform: str  # "windows" | "wsl" | "linux" | "linux-flatpak"


def _is_wsl() -> bool:
    if os.name != "posix":
        return False
    try:
        return "microsoft" in Path("/proc/version").read_text().lower()
    except OSError:
        return False


def _windows_drive_candidates() -> list[Path]:
    # Native Windows
    if os.name == "nt":
        return [Path(f"{d}:\\") for d in string.ascii_uppercase if Path(f"{d}:\\").exists()]
    # WSL — Windows drives are mounted under /mnt/<letter>
    if _is_wsl():
        return [Path(f"/mnt/{d.lower()}") for d in "CDEFGHIJ" if Path(f"/mnt/{d.lower()}").exists()]
    return []


def _windows_steam_roots() -> list[Library]:
    """Find Steam install paths on Windows/WSL via common locations + registry."""
    platform = "wsl" if _is_wsl() else "windows"
    found: list[Path] = []

    # Registry (native Windows only — winreg).
    if os.name == "nt":
        try:
            import winreg

            for hive, sub in [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam"),
                (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"),
            ]:
                try:
                    with winreg.OpenKey(hive, sub) as k:
                        val, _ = winreg.QueryValueEx(k, "InstallPath")
                        p = Path(val)
                        if p.exists():
                            found.append(p)
                except OSError:
                    continue
        except ImportError:
            pass

    for drive in _windows_drive_candidates():
        for sub in (
            "Program Files (x86)/Steam",
            "Program Files/Steam",
            "Steam",
            "SteamLibrary",
        ):
            p = drive / sub
            if p.exists():
                found.append(p)

    # De-dupe preserving order.
    seen: set[str] = set()
    out: list[Library] = []
    for p in found:
        key = str(p).rstrip("/\\").lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(Library(path=p, platform=platform))
    return out


def _linux_steam_roots() -> list[Library]:
    home = Path.home()
    candidates: list[tuple[Path, str]] = [
        (home / ".steam/steam", "linux"),
        (home / ".local/share/Steam", "linux"),
        (home / ".var/app/com.valvesoftware.Steam/.local/share/Steam", "linux-flatpak"),
    ]
    out: list[Library] = []
    for path, plat in candidates:
        # ~/.steam/steam may be a symlink to ~/.local/share/Steam — resolve.
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if resolved.exists() and not any(str(resolved) == str(lib.path) for lib in out):
            out.append(Library(path=resolved, platform=plat))
    return out


def discover_steam_roots() -> list[Library]:
    """All Steam install roots reachable from this host."""
    roots = _windows_steam_roots()
    if os.name == "posix":
        roots.extend(_linux_steam_roots())
    return roots


def discover_libraries() -> list[Library]:
    """Expand each Steam root with libraries listed in libraryfolders.vdf."""
    expanded: list[Library] = []
    seen: set[str] = set()
    for root in discover_steam_roots():
        for lib_path in [root.path] + _libraries_from_vdf(root):
            key = str(lib_path).rstrip("/\\").lower()
            if key in seen:
                continue
            seen.add(key)
            expanded.append(Library(path=lib_path, platform=root.platform))
    return expanded


def _libraries_from_vdf(root: Library) -> list[Path]:
    vdf = root.path / "steamapps" / "libraryfolders.vdf"
    if not vdf.exists():
        return []
    try:
        text = vdf.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    out: list[Path] = []
    for raw in parse_libraryfolders(text):
        path = _translate_windows_path(raw, root.platform)
        if path and path.exists():
            out.append(path)
    return out


def _translate_windows_path(raw: str, platform: str) -> Path | None:
    """Map e.g. 'D:\\SteamLibrary' to '/mnt/d/SteamLibrary' when running in WSL."""
    if platform == "wsl" and re.match(r"^[A-Za-z]:[\\/]", raw):
        drive = raw[0].lower()
        rest = raw[2:].replace("\\", "/").lstrip("/")
        return Path(f"/mnt/{drive}/{rest}")
    return Path(raw)


# ── Game enumeration ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Game:
    appid: str
    name: str
    installdir: str
    install_path: Path
    library_path: Path
    size_on_disk: int | None

    def to_dict(self) -> dict[str, object]:
        return {
            "appid": self.appid,
            "name": self.name,
            "installdir": self.installdir,
            "install_path": str(self.install_path),
            "library_path": str(self.library_path),
            "size_on_disk": self.size_on_disk,
        }


def enumerate_games(libraries: list[Library]) -> list[Game]:
    out: list[Game] = []
    seen: set[str] = set()
    for lib in libraries:
        steamapps = lib.path / "steamapps"
        if not steamapps.is_dir():
            continue
        for acf in sorted(steamapps.glob("appmanifest_*.acf")):
            try:
                text = acf.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            fields = parse_vdf_flat(text)
            appid = fields.get("appid") or ""
            name = fields.get("name") or ""
            installdir = fields.get("installdir") or ""
            if not appid or not installdir:
                continue
            key = f"{appid}@{lib.path}"
            if key in seen:
                continue
            seen.add(key)
            install_path = steamapps / "common" / installdir
            try:
                size = int(fields.get("SizeOnDisk") or 0) or None
            except ValueError:
                size = None
            out.append(
                Game(
                    appid=appid,
                    name=name,
                    installdir=installdir,
                    install_path=install_path,
                    library_path=lib.path,
                    size_on_disk=size,
                )
            )
    return out
