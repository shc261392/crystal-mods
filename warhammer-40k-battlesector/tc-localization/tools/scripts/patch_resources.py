#!/usr/bin/env python3
"""
patch_resources.py — Convert SC→TC in all Chinese TextAssets in resources.assets.

Reads the pristine resources.assets from the installation backup
($MOD_BACKUP_DIR/Warhammer 40K Battlesector_Data/resources.assets, created by
deploy.sh on first install) and writes the patched copy to
translation/zh-TW/dist/resources.assets.
"""

import os
import sys
import json
import UnityPy
import opencc

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

DEFAULT_GAME_DIR = "/mnt/d/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector"
GAME_DIR = os.environ.get("MOD_GAME_DIR", DEFAULT_GAME_DIR)
MOD_BACKUP_DIR = os.environ.get("MOD_BACKUP_DIR", os.path.join(GAME_DIR, ".zh-tw-mod-backup"))
DIST_DIR = os.environ.get("MOD_DIST_DIR", os.path.join(REPO_ROOT, "translation/zh-TW/dist"))
FALLBACK_CONFIG = os.path.join(REPO_ROOT, "translation", "zh-TW", "config", "description_fallback_chars.json")
# TC-first default: keep SC fallback OFF unless explicitly enabled.
# This prevents broad SC regression in campaign/units once font coverage is good.
ENABLE_SC_FALLBACK = os.environ.get("MOD_ENABLE_SC_FALLBACK", "0") == "1"

BACKUP_RESOURCES = os.path.join(MOD_BACKUP_DIR, "Warhammer 40K Battlesector_Data", "resources.assets")
DIST_FILE = os.path.join(DIST_DIR, "resources.assets")

# Runtime-proven missing glyphs from Player.log for
# [futura medium condensed bt SDF - No Underlay] in text objects
# [Description] and [TitleText].
#
# Keep fallback tightly scoped to these exact characters to preserve TC output
# while eliminating tofu boxes in campaign/crusade description UI.
DEFAULT_MISSING_FUTURA_CHARS = set(
    "並來個們倖倫備價務勝勵區卻園團夠將幾後從態憐憫戰擊擲敗敵於時榮標"
    "毀沒滅潰無爾狀獎獲當癒眾結經維緣繼續羅聖艙艦著處蟲衛裡評誌讓負責"
    "軍這連遠邊鑄開隊際離領駛驗體鬥"
)


def load_missing_futura_chars() -> set[str]:
    """Load campaign description fallback char-set from config.

    Config schema:
      {
        "campaign_chinese_fallback_chars": "...chars..."
      }
    """
    if not os.path.isfile(FALLBACK_CONFIG):
        return set(DEFAULT_MISSING_FUTURA_CHARS)

    try:
        with open(FALLBACK_CONFIG, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as e:
        print(f"WARN: failed to parse fallback config ({FALLBACK_CONFIG}): {e}", file=sys.stderr)
        return set(DEFAULT_MISSING_FUTURA_CHARS)

    chars = payload.get("campaign_chinese_fallback_chars", "") if isinstance(payload, dict) else ""
    if not isinstance(chars, str) or not chars:
        return set(DEFAULT_MISSING_FUTURA_CHARS)
    return set(chars)


def main():
    if not os.path.isfile(BACKUP_RESOURCES):
        print(f"ERROR: backup resources.assets not found: {BACKUP_RESOURCES}", file=sys.stderr)
        print("       Run tools/scripts/deploy.sh to initialise the backup.", file=sys.stderr)
        sys.exit(1)
    source = BACKUP_RESOURCES

    print(f"Source: {source}")
    print(f"Output: {DIST_FILE}")

    os.makedirs(os.path.dirname(DIST_FILE), exist_ok=True)

    env = UnityPy.load(source)
    converter = opencc.OpenCC("s2twp")
    to_sc = opencc.OpenCC("t2s")
    missing_futura_chars = load_missing_futura_chars()
    print(f"Loaded campaign fallback char-set: {len(missing_futura_chars)} chars")
    if ENABLE_SC_FALLBACK:
        print("SC fallback override: ENABLED (MOD_ENABLE_SC_FALLBACK=1) — applying targeted SC fallback")
    else:
        print("SC fallback mode: OFF (default TC-first)")

    converted = 0
    total_fallback = 0
    for obj in env.objects:
        if obj.type.name != "TextAsset":
            continue
        ta = obj.read()
        if "chinese" not in ta.m_Name.lower():
            continue

        script = ta.m_Script
        text = script.decode("utf-8") if isinstance(script, bytes) else (script or "")
        if not text:
            continue

        tc_text = converter.convert(text)

        # Targeted glyph-compat fallback: only convert runtime-proven missing
        # characters back to their SC forms for legacy futura TMP paths used by
        # campaign descriptions and unit management labels.
        # IMPORTANT: keep this scoped to campaign/units Chinese repositories to avoid
        # broad SC regression across the rest of the UI/content.
        fallback_count = 0
        apply_targeted_fallback = (
            isinstance(ta.m_Name, str)
            and ("campaign" in ta.m_Name.lower() or "units" in ta.m_Name.lower())
            and "chinese" in ta.m_Name.lower()
        )

        if tc_text and apply_targeted_fallback and ENABLE_SC_FALLBACK:
            chars = []
            for ch in tc_text:
                if ch in missing_futura_chars:
                    sc = to_sc.convert(ch)
                    repl = sc[0] if sc else ch
                    if repl != ch:
                        fallback_count += 1
                    chars.append(repl)
                else:
                    chars.append(ch)
            tc_text = "".join(chars)

        sc_bytes = len(text.encode("utf-8"))
        tc_bytes = len(tc_text.encode("utf-8"))
        ta.m_Script = tc_text
        ta.save()
        converted += 1
        total_fallback += fallback_count
        print(f"  {ta.m_Name}: {sc_bytes} → {tc_bytes} bytes  (targeted_fallback={fallback_count})")

    print(f"\nConverted {converted} TextAssets")
    if total_fallback > 0:
        print(f"  ⚠  WARNING: {total_fallback} characters reverted to SC via targeted fallback "
              f"(MOD_ENABLE_SC_FALLBACK=1). If unexpected, do not deploy.")

    with open(DIST_FILE, "wb") as f:
        f.write(env.file.save())

    print(f"Saved: {os.path.getsize(DIST_FILE):,} bytes")


if __name__ == "__main__":
    main()
