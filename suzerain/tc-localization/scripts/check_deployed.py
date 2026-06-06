# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "UnityPy>=1.20",
# ]
# ///
"""Check what's in the deployed bundle."""

import UnityPy
from pathlib import Path

bundle_path = Path("/mnt/d/SteamLibrary/steamapps/common/Suzerain/Suzerain_Data/StreamingAssets/aa/StandaloneWindows64/scenes_scenes_assets_scenes_mainmenu.unity_6dd6ca6b71e2733b13cf2860d4a95134.bundle")

print(f"Analyzing: {bundle_path}")
print(f"File size: {bundle_path.stat().st_size} bytes")

with open(bundle_path, 'rb') as f:
    env = UnityPy.load(f)

chinese_count = 0
english_count = 0
samples = []

for obj in env.objects:
    try:
        read_obj = obj.read()
        if hasattr(read_obj, 'm_text') and read_obj.m_text:
            text = read_obj.m_text
            if any(ord(c) > 127 for c in text):
                chinese_count += 1
                if len(samples) < 10:
                    samples.append((text[:50], "CHINESE"))
            else:
                english_count += 1
                if len(samples) < 10:
                    samples.append((text[:50], "ENGLISH"))
    except:
        pass

print(f"\nText summary:")
print(f"  Chinese: {chinese_count}")
print(f"  English: {english_count}")
print(f"\nSamples:")
for text, lang in samples:
    print(f"  [{lang}] {text}")

if chinese_count == 0:
    print("\n❌ CRITICAL: Deployed bundle has ZERO Chinese text!")
    print("Bundle is either original unmodified or patches failed to serialize.")
elif english_count == 0:
    print("\n✓ Deployed bundle is FULLY CHINESE!")
else:
    print(f"\n⚠ Mixed: {chinese_count} Chinese + {english_count} English")
