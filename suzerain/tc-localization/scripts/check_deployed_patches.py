# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "UnityPy>=1.20",
# ]
# ///
"""Check if deployed bundle still has patches."""

import UnityPy
from pathlib import Path

game_aa = Path("/mnt/d/SteamLibrary/steamapps/common/Suzerain/Suzerain_Data/StreamingAssets/aa/StandaloneWindows64")
bundle_path = game_aa / "scenes_scenes_assets_scenes_mainmenu.unity_6dd6ca6b71e2733b13cf2860d4a95134.bundle"

print(f"Reading: {bundle_path}")
print(f"File size: {bundle_path.stat().st_size} bytes")
print()

with open(bundle_path, 'rb') as f:
    env = UnityPy.load(f)

translated = 0
english = 0
samples = []

for obj in env.objects:
    try:
        read_obj = obj.read()
        if hasattr(read_obj, 'm_text') and read_obj.m_text:
            text = read_obj.m_text
            if any(ord(c) > 127 for c in text):  # Contains non-ASCII (Chinese)
                translated += 1
                if len(samples) < 5:
                    samples.append((text[:50], "CHINESE"))
            else:
                english += 1
                if len(samples) < 5 and english <= 5:
                    samples.append((text[:50], "ENGLISH"))
    except:
        pass

print(f"Chinese: {translated} | English: {english}")
print(f"\nSamples:")
for text, lang in samples:
    print(f"  [{lang}] {text}")

if translated == 0:
    print("\n❌ PROBLEM: Deployed bundle has NO Chinese text!")
    print("   Patches were lost or reverted.")
else:
    print(f"\n✓ Deployed bundle has {translated} Chinese strings")
