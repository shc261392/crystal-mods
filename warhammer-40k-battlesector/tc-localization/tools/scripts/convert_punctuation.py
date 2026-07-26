#!/usr/bin/env python3
"""
convert_punctuation.py — Convert half-width ASCII punctuation to full-width CJK
punctuation in the 7 Chinese TextAssets, only where adjacent to CJK (so decimals,
thousands separators, version numbers, and Latin text are untouched).

Rules:
  , . ! ? : ;   -> ，。！？：；   when immediately preceded by a CJK character
  ( )           -> （）           ( when followed by CJK / ) when preceded by CJK
  runs of 2+ .  -> ……            (ellipsis) when preceded by CJK
  a single space right after a full-width closing/sentence punct is removed;
  a single space right before a full-width open paren is removed.

Modes:
  dry   : print counts + samples, modify nothing
  write <out_subdir> : write text_<pid>.bin per TextAsset for FontTool `replace`

Usage:
  python3 tools/scripts/convert_punctuation.py dry
  python3 tools/scripts/convert_punctuation.py write punct_out
"""
import os
import re
import sys

from UnityPy.helpers import TypeTreeHelper
from UnityPy.streams import EndianBinaryWriter

import UnityPy

TypeTreeHelper.read_typetree_boost = False

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
A = os.path.join(REPO, "translation", "zh-TW", "dist", "resources.assets")
CHINESE = {
    "text_repository-barks_chinese",
    "text_repository-campaign_chinese",
    "text_repository-campaign-external_chinese",
    "text_repository-default_chinese",
    "text_repository-default-external_chinese",
    "text_repository-units_chinese",
    "text_repository-units-external_chinese",
}

FW = {",": "，", ".": "。", "!": "！", "?": "？", ":": "：", ";": "；"}
_CJK = "\u3400-\u9fff\uf900-\ufaff"
# Full-width punctuation that also counts as "CJK context" when it immediately
# precedes a sentence punctuation (so e.g. a period after a full-width close
# paren still becomes 。).
_FW_CTX = set("，。！？：；）】》」』…")


def is_cjk(ch):
    return bool(ch) and ("\u3400" <= ch <= "\u9fff" or "\uf900" <= ch <= "\ufaff")


def is_ctx(ch):
    return is_cjk(ch) or ch in _FW_CTX


def convert(text):
    # 1) ellipsis: runs of 2+ dots preceded by CJK -> ……
    text = re.sub(rf"(?<=[{_CJK}])\.{{2,}}", "……", text)

    # 2) sentence punctuation + balanced parentheses, char by char
    out = []
    paren_stack = []
    n = len(text)
    for i, ch in enumerate(text):
        nxt = text[i + 1] if i + 1 < n else ""
        prev_out = out[-1] if out else ""
        # opening paren: convert if it introduces CJK; remember the decision
        if ch == "(":
            conv = is_cjk(nxt)
            out.append("（" if conv else "(")
            paren_stack.append(conv)
            continue
        # closing paren: match its opener so brackets stay balanced
        if ch == ")":
            conv = paren_stack.pop() if paren_stack else is_cjk(prev_out)
            out.append("）" if conv else ")")
            continue
        if ch in FW and is_ctx(prev_out):
            if ch == "." and (nxt == "." or nxt.isdigit()):
                out.append(ch)
                continue
            if ch == "," and nxt.isdigit():
                out.append(ch)
                continue
            out.append(FW[ch])
            continue
        out.append(ch)
    result = "".join(out)

    # 3) tidy spaces around the new full-width punctuation
    result = re.sub(r"([，。！？：；）…]) ", r"\1", result)
    result = re.sub(r" (（)", r"\1", result)
    return result


def as_text(d):
    s = d.m_Script
    b = s.encode("utf-8", "surrogateescape") if isinstance(s, str) else bytes(s)
    return b.decode("utf-8", "replace")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "dry"
    env = UnityPy.load(A)
    out_dir = None
    if mode == "write":
        out_dir = os.path.join(REPO, ".copilot_workspace", sys.argv[2])
        os.makedirs(out_dir, exist_ok=True)

    total = 0
    paren_samples = []
    ell_samples = []
    for o in env.objects:
        if o.type.name != "TextAsset":
            continue
        d = o.read()
        name = getattr(d, "m_Name", "")
        if name not in CHINESE:
            continue
        text = as_text(d)
        new = convert(text)
        # count char-level differences roughly by counting new full-width puncts added
        diff = sum(1 for a, b in zip(text, new) if a != b)
        total += diff
        for ol, nl in zip(text.split("\r\n"), new.split("\r\n")):
            if ol != nl:
                if ("（" in nl or "）" in nl) and len(paren_samples) < 8:
                    paren_samples.append((ol[:60], nl[:60]))
                if "…" in nl and len(ell_samples) < 8:
                    ell_samples.append((ol[:60], nl[:60]))
        print(f"{name}: bytes {len(text.encode('utf-8'))} -> {len(new.encode('utf-8'))}")

        if mode == "write":
            node = o._get_typetree_node()
            td = o.read_typetree()
            td["m_Script"] = new
            w = EndianBinaryWriter(endian="<")
            TypeTreeHelper.write_typetree(td, node, w)
            with open(os.path.join(out_dir, f"text_{o.path_id}.bin"), "wb") as f:
                f.write(bytes(w.bytes))
            print(f"   wrote text_{o.path_id}.bin")

    print(f"\napprox changed chars: {total}")
    print("\n=== PAREN samples ===")
    for ob, nb in paren_samples:
        print(f"  - {ob}\n    {nb}")
    print("\n=== ELLIPSIS samples ===")
    for ob, nb in ell_samples:
        print(f"  - {ob}\n    {nb}")


if __name__ == "__main__":
    main()
