# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "UnityPy>=1.20",
# ]
# ///
"""Verify TMP patches were applied to bundles."""

import json
from pathlib import Path
import UnityPy

bundle_path = Path("build.minimal/scenes_scenes_assets_scenes_mainmenu.unity_6dd6ca6b71e2733b13cf2860d4a95134.bundle")

with open(bundle_path, 'rb') as f:
    env = UnityPy.load(f)

tmp_count = 0
tmp_texts = []

for obj in env.objects:
    try:
        read_obj = obj.read()
        if hasattr(read_obj, 'm_text') and read_obj.m_text:
            text = read_obj.m_text
            tmp_count += 1
            if any(ord(c) > 127 for c in text):  # Contains non-ASCII
                tmp_texts.append((text[:60], "TRANSLATED"))
            elif len(text) > 3:
                tmp_texts.append((text[:60], "ENGLISH"))
    except:
        pass

print(f"Total m_text fields found: {tmp_count}")
print(f"\nSample texts (first 20):")
for text, lang in tmp_texts[:20]:
    print(f"  [{lang}] {text}")

if not any(lang == "TRANSLATED" for _, lang in tmp_texts):
    print("\n⚠ WARNING: No translated text found! TMP patcher may have failed.")
else:
    trans_count = sum(1 for _, lang in tmp_texts if lang == 'TRANSLATED')
    print(f"\n✓ Found {trans_count} translated strings out of {tmp_count}")
