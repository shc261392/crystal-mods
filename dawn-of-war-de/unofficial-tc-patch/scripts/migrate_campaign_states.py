#!/usr/bin/env python3
"""migrate_campaign_states.py — Migrate DoW campaign state files between locale
statenames to preserve player campaign progress when switching locales.

Background
----------
Dawn of War stores campaign progress in per-profile Lua files:
  %APPDATA%\\Relic Entertainment\\Dawn of War\\Profiles\\<Profile>\\
    <Expansion>\\singleplayer\\campaign\\state<N>\\campaignstate.lua

Each file records the faction name in `statename`.  The game finds the right
slot by matching `statename` against the current locale's translation of the
faction name.  Because the original Simplified Chinese SGA and this TC mod use
different translations, the game creates new (empty) state slots when first
running under each locale -- ignoring the player's existing progress.

This script copies progress between state slots to ensure campaigns are never
silently reset.

Modes
-----
Forward (deploy, default): copies progress from any non-TC state (SC, EN, ...)
  into the corresponding TC mod state slot.
Reverse (uninstall, --reverse): copies progress from each TC mod state slot
  back into ALL matching non-TC state slots (SC, EN, ...), so that returning to
  any other locale still shows current progress.

Safety
------
* A full backup of every touched expansion's campaign directory is written to
  <repo>/backup/campaign_states/<timestamp>/ BEFORE any file is modified.
* Individual .bak.<timestamp> files are also written beside each overwritten
  state file as a second safety net.
* Source state files are NEVER deleted.
* If --dry-run is given, no files are written and no backups are created.

Recovery
--------
If something goes wrong, restore your saves:
  1. Close Dawn of War: Definitive Edition completely.
  2. Find the backup stamped before the migration in:
       <repo>/backup/campaign_states/<timestamp>/
  3. Copy the backed-up campaignstate.lua files back to:
       %APPDATA%\\Relic Entertainment\\Dawn of War\\Profiles\\<Profile>\\
         <Expansion>\\singleplayer\\campaign\\state<N>\\

Usage
-----
    uv run python scripts/migrate_campaign_states.py [--dry-run] [--reverse]

Exit codes: 0 = success, 1 = error
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Statename translation tables
# Only WXP (Winter Assault) has been confirmed to have mismatched translations.
# Add more entries here if DXP2/DXP3 are found to have the same issue.
# ---------------------------------------------------------------------------

# All known non-TC statenames -> TC statename  (forward: any locale -> TC mod)
_FORWARD_MAP: dict[str, str] = {
    # Simplified Chinese SGA (original bundled locale)
    "\u8ecd\u968a\u7d00\u5f8b": "\u79e9\u5e8f\u9663\u71df",   # WXP Forces of Order
    "\u8ecd\u968a\u6df7\u4e82": "\u6df7\u4e82\u9663\u71df",   # WXP Forces of Disorder
    # English -- covers players who previously played in English
    "Forces of Order": "\u79e9\u5e8f\u9663\u71df",
    "Forces of Disorder": "\u6df7\u4e82\u9663\u71df",
}

# The set of TC mod statenames (identifies TC mod state slots)
_TC_STATENAMES: frozenset[str] = frozenset(_FORWARD_MAP.values())

# Expansions to scan
EXPANSIONS = ["WXP", "DXP2", "DXP3"]

# Repo root (scripts/ is one level below)
_REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# AppData discovery
# ---------------------------------------------------------------------------

def find_dow_appdata() -> Path | None:
    """Auto-detect the DoW AppData directory."""
    import os

    candidates: list[Path] = []

    # WSL2: scan /mnt/{c..g}/Users/<any-user>/AppData/...
    for drv in "cdefg":
        users = Path(f"/mnt/{drv}/Users")
        if not users.is_dir():
            continue
        for user_dir in users.iterdir():
            if not user_dir.is_dir():
                continue
            c = user_dir / "AppData" / "Roaming" / "Relic Entertainment" / "Dawn of War"
            candidates.append(c)

    # Native Windows Python via APPDATA env var
    if appdata := os.environ.get("APPDATA"):
        candidates.append(Path(appdata) / "Relic Entertainment" / "Dawn of War")

    # Native Linux Steam (uncommon)
    candidates.append(Path.home() / ".local" / "share" / "Relic Entertainment" / "Dawn of War")

    return next((c for c in candidates if c.is_dir()), None)


# ---------------------------------------------------------------------------
# Lua helpers -- surgical read/write (avoids full parse/reformat)
# ---------------------------------------------------------------------------

def _read_lua(path: Path) -> str:
    """Read a Lua file trying UTF-8-BOM, UTF-16, Latin-1 in order."""
    for enc in ("utf-8-sig", "utf-16", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ValueError(f"Cannot decode: {path}")


def _extract_value(content: str, key: str) -> str | None:
    """Extract a quoted or unquoted Lua assignment value for `key`."""
    if m := re.search(rf'^{re.escape(key)}\s*=\s*"([^"]*)"', content, re.MULTILINE):
        return m.group(1)
    if m := re.search(rf'^{re.escape(key)}\s*=\s*(\S+)', content, re.MULTILINE):
        return m.group(1)
    return None


def _replace_statename(content: str, new_statename: str) -> str:
    """Replace only the statename value; all other lines are untouched."""
    return re.sub(
        r'(statename\s*=\s*")[^"]*(")',
        rf'\g<1>{new_statename}\2',
        content,
        flags=re.MULTILINE,
    )


def _maxmission(content: str) -> int:
    v = _extract_value(content, "maxmission")
    try:
        return int(v) if v else 0
    except ValueError:
        return 0


# ---------------------------------------------------------------------------
# Backup helpers
# ---------------------------------------------------------------------------

def _backup_campaign_dir(
    campaign_dir: Path,
    stamp: str,
    dry_run: bool,
    log_fn,
) -> Path:
    """Copy all state files to <repo>/backup/campaign_states/<stamp>/... ."""
    # Build relative path from Profiles/ downward for a descriptive subdir
    try:
        profiles_parent = campaign_dir.parents[3]   # .../Profiles/
        rel = campaign_dir.relative_to(profiles_parent)
    except ValueError:
        rel = Path(campaign_dir.name)

    backup_root = _REPO_ROOT / "backup" / "campaign_states" / stamp / rel

    if not dry_run:
        backup_root.mkdir(parents=True, exist_ok=True)
        for src in sorted(campaign_dir.glob("state*/campaignstate.lua")):
            dst_dir = backup_root / src.parent.name
            dst_dir.mkdir(exist_ok=True)
            shutil.copy2(src, dst_dir / "campaignstate.lua")

    log_fn(f"  Backup : {backup_root}")
    log_fn(f"  Recover: copy files from the backup directory back to:")
    log_fn(f"           {campaign_dir}")
    return backup_root


# ---------------------------------------------------------------------------
# Core migration logic
# ---------------------------------------------------------------------------

def _load_states(campaign_dir: Path, log_fn) -> list[dict]:
    states: list[dict] = []
    for f in sorted(campaign_dir.glob("state*/campaignstate.lua")):
        try:
            content = _read_lua(f)
        except ValueError as exc:
            log_fn(f"  WARN: could not read {f}: {exc}")
            continue
        states.append({
            "path": f,
            "content": content,
            "statename": _extract_value(content, "statename") or "",
            "campaignid": _extract_value(content, "campaignid") or "",
            "maxmission": _maxmission(content),
        })
    return states


def _write_state(
    src: dict,
    dst_file: Path,
    new_statename: str,
    stamp: str,
    dry_run: bool,
    log_fn,  # noqa: ARG001
) -> None:
    """Overwrite dst_file with src's progress data, updating statename."""
    new_content = _replace_statename(src["content"], new_statename)
    if not dry_run:
        if dst_file.exists():
            bak = dst_file.with_suffix(f".bak.{stamp}")
            shutil.copy2(dst_file, bak)
        dst_file.write_text(new_content, encoding="utf-8")


def _migrate_forward(
    states: list[dict],
    campaign_dir: Path,
    stamp: str,
    dry_run: bool,
    log_fn,
) -> int:
    """Forward: copy progress from SC/EN states into the corresponding TC slot."""
    migrated = 0
    for src_name, tc_name in _FORWARD_MAP.items():
        for src in [s for s in states if s["statename"] == src_name]:
            cid = src["campaignid"]
            src_progress = src["maxmission"]
            tc_matches = [
                s for s in states
                if s["campaignid"] == cid and s["statename"] == tc_name
            ]

            if tc_matches:
                tc = tc_matches[0]
                tc_progress = tc["maxmission"]
                if src_progress > tc_progress:
                    log_fn(
                        f"  UPDATE {tc['path'].parent.name}/ "
                        f"<- {src['path'].parent.name}/ "
                        f"(progress {src_progress} > {tc_progress}, "
                        f"statename kept as {tc_name!r})"
                    )
                    _write_state(src, tc["path"], tc_name, stamp, dry_run, log_fn)
                    migrated += 1
                else:
                    log_fn(
                        f"  SKIP   {tc['path'].parent.name}/ "
                        f"(TC {tc_progress} >= source {src_progress})"
                    )
            else:
                existing_nums = [
                    int(m.group(1))
                    for s in states
                    if (m := re.match(r"state(\d+)", s["path"].parent.name))
                ]
                next_num = max(existing_nums, default=0) + 1
                new_file = campaign_dir / f"state{next_num}" / "campaignstate.lua"
                log_fn(
                    f"  CREATE state{next_num}/ "
                    f"<- {src['path'].parent.name}/ "
                    f"({src_name!r} -> {tc_name!r}, maxmission={src_progress})"
                )
                if not dry_run:
                    new_file.parent.mkdir(parents=True, exist_ok=True)
                _write_state(src, new_file, tc_name, stamp, dry_run, log_fn)
                migrated += 1
    return migrated


def _migrate_reverse(
    states: list[dict],
    campaign_dir: Path,  # noqa: ARG001
    stamp: str,
    dry_run: bool,
    log_fn,
) -> int:
    """Reverse: copy TC mod progress back into ALL non-TC state slots.

    Handles SC, EN, and any other locale that has a state for the same campaign.
    """
    migrated = 0
    for tc in [s for s in states if s["statename"] in _TC_STATENAMES]:
        cid = tc["campaignid"]
        tc_progress = tc["maxmission"]

        # All non-TC states for same campaign (any legacy locale)
        legacy_states = [
            s for s in states
            if s["campaignid"] == cid and s["statename"] not in _TC_STATENAMES
        ]

        if not legacy_states:
            log_fn(f"  SKIP   {tc['path'].parent.name}/ -- no legacy state for {cid!r}")
            continue

        for legacy in legacy_states:
            legacy_progress = legacy["maxmission"]
            if tc_progress > legacy_progress:
                log_fn(
                    f"  UPDATE {legacy['path'].parent.name}/ "
                    f"<- {tc['path'].parent.name}/ "
                    f"(progress {tc_progress} > {legacy_progress}, "
                    f"statename kept as {legacy['statename']!r})"
                )
                _write_state(tc, legacy["path"], legacy["statename"], stamp, dry_run, log_fn)
                migrated += 1
            else:
                log_fn(
                    f"  SKIP   {legacy['path'].parent.name}/ "
                    f"({legacy['statename']!r} {legacy_progress} >= TC {tc_progress})"
                )
    return migrated


def migrate_expansion(
    campaign_dir: Path,
    reverse: bool,
    stamp: str,
    dry_run: bool = False,
    log_fn=print,
) -> int:
    """Migrate state files for one expansion. Returns count of updated files."""
    if not campaign_dir.is_dir():
        return 0

    states = _load_states(campaign_dir, log_fn)
    if not states:
        return 0

    # Backup ALL state files BEFORE touching anything
    _backup_campaign_dir(campaign_dir, stamp, dry_run, log_fn)

    if reverse:
        return _migrate_reverse(states, campaign_dir, stamp, dry_run, log_fn)
    else:
        return _migrate_forward(states, campaign_dir, stamp, dry_run, log_fn)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--dry-run", action="store_true",
        help="Show what would change without writing any files")
    parser.add_argument("--reverse", action="store_true",
        help="Sync TC mod progress back into all non-TC state slots (use on uninstall)")
    parser.add_argument("--appdata-dir", metavar="PATH",
        help="Override auto-detected DoW AppData directory")
    parser.add_argument("--profile", default="Profile1",
        help="Profile name (default: Profile1)")
    args = parser.parse_args()

    direction_label = (
        "TC -> all locales (uninstall sync)" if args.reverse
        else "SC/EN -> TC (deploy sync)"
    )
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    dow_appdata = Path(args.appdata_dir) if args.appdata_dir else find_dow_appdata()
    if not dow_appdata or not dow_appdata.is_dir():
        print("Error: DoW AppData directory not found.", file=sys.stderr)
        print("Pass --appdata-dir PATH to specify it manually.", file=sys.stderr)
        return 1

    profile_dir = dow_appdata / "Profiles" / args.profile
    if not profile_dir.is_dir():
        print(f"Error: Profile not found: {profile_dir}", file=sys.stderr)
        return 1

    print(f"DoW AppData : {dow_appdata}")
    print(f"Profile     : {args.profile}")
    print(f"Direction   : {direction_label}")
    if args.dry_run:
        print("[DRY RUN -- no files will be written and no backups created]")
    print()

    total = 0
    for exp in EXPANSIONS:
        campaign_dir = profile_dir / exp / "singleplayer" / "campaign"
        print(f"--- {exp} ---")
        count = migrate_expansion(
            campaign_dir,
            reverse=args.reverse,
            stamp=stamp,
            dry_run=args.dry_run,
            log_fn=print,
        )
        print(f"  Migrated: {count} state(s)" if count else "  Nothing to migrate.")
        total += count

    print()
    if total:
        if not args.dry_run:
            backup_path = _REPO_ROOT / "backup" / "campaign_states" / stamp
            print(f"Campaign state migration complete: {total} state(s) updated.")
            print()
            print("Pre-migration backup saved at:")
            print(f"  {backup_path}/")
            print()
            print("To restore saves manually if needed:")
            print("  1. Close Dawn of War: Definitive Edition")
            print("  2. Copy the backed-up campaignstate.lua files back to:")
            print(f"     {profile_dir}/<Expansion>/singleplayer/campaign/state<N>/")
        else:
            print(f"[DRY RUN] Would update {total} state(s). No files changed.")
    else:
        print("All campaign states are already up-to-date.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
