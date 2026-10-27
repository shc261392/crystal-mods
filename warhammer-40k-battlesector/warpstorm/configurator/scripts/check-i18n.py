#!/usr/bin/env python3
"""Warpstorm configurator — validate the UI string tables (i18n/<code>.json).

    python3 scripts/check-i18n.py            # validate; exit 1 on problems
    python3 scripts/check-i18n.py --sync-en  # add field/group/option labels from shared/fields.json to en.json

Checks: every key the C# code uses exists in en.json; every locale has every
en.json key; {n} placeholders match English.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
I18N = HERE / "i18n"
FIELDS = HERE.parent / "shared" / "fields.json"
LOCALES = ["en", "de", "es", "fr", "ko", "pl", "pt-BR", "ru", "zh-CN", "zh-TW"]
KEY_RE = re.compile(r'"([a-z][A-Za-z]*\.[A-Za-z0-9.]+)"')
SKIP = re.compile(r"^(data|i18n|units|weapons|ui)\.|\.(json|png|cfg|lnk)$|^com\.|^warpstorm-")
PH = re.compile(r"\{\d+\}")


def load(code: str) -> dict[str, str]:
    p = I18N / f"{code}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def field_keys() -> dict[str, str]:
    data = json.loads(FIELDS.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for kind in ("unit", "weapon"):
        for f in data[kind]:
            out[f"field.{kind}.{f['key']}"] = f["label"]
            out[f"group.{f['group']}"] = f["group"]
            for o in f.get("options", []):
                out[f"option.{f['key']}.{o['value']}"] = o["label"]
    return out


def sync_en() -> None:
    en = load("en")
    added = 0
    for k, v in field_keys().items():
        if k not in en:
            en[k] = v
            added += 1
    (I18N / "en.json").write_text(json.dumps(en, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"en.json: added {added} field/group/option key(s)")


def main() -> int:
    if "--sync-en" in sys.argv:
        sync_en()
        return 0

    problems: list[str] = []
    en = load("en")
    used = {k for f in HERE.glob("*.cs") for k in KEY_RE.findall(f.read_text(encoding="utf-8")) if not SKIP.search(k)}
    used = {k for k in used if not k.endswith(".")}  # prefixes like "field.unit."
    for k in sorted(used - en.keys()):
        problems.append(f"en: key used in code but missing: {k}")
    for k in sorted(field_keys().keys() - en.keys()):
        problems.append(f"en: missing field key (run --sync-en): {k}")

    for code in LOCALES[1:]:
        table = load(code)
        if not table:
            problems.append(f"{code}: file missing")
            continue
        missing = [k for k in en if k not in table or not str(table[k]).strip()]
        extra = [k for k in table if k not in en]
        bad_ph = [k for k in en if k in table and sorted(PH.findall(en[k])) != sorted(PH.findall(table[k]))]
        if missing:
            problems.append(f"{code}: {len(missing)} missing, e.g. {missing[:5]}")
        if extra:
            problems.append(f"{code}: {len(extra)} unknown key(s), e.g. {extra[:5]}")
        for k in bad_ph:
            problems.append(f"{code}: placeholder mismatch in {k}: {table[k]!r}")

    for p in problems:
        print(p)
    print(f"{len(en)} English strings, {len(LOCALES)} locales, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
