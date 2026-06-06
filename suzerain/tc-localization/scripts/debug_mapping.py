# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "UnityPy>=1.20",
# ]
# ///
"""Debug why translations aren't matching bundle texts."""

import json
from pathlib import Path
import UnityPy

project = Path("scene-tmp-translation")

# Load source
src = {}
for line in (project / "source.jsonl").read_text("utf-8").splitlines():
    if line.strip():
        rec = json.loads(line)
        src[rec["id"]] = rec["text"]

# Load state and build mapping
mapping = {}
for line in (project / "state.jsonl").read_text("utf-8").splitlines():
    if not line.strip():
        continue
    rec = json.loads(line)
    tgt = rec.get("manual") if rec.get("manual") is not None else rec.get("machine")
    s = src.get(rec["id"])
    if s and tgt and s != tgt:
        mapping[s] = tgt

print(f"Translation mapping: {len(mapping)} entries")

# Check if these texts exist in bundles
bundle_path = Path("/mnt/d/SteamLibrary/steamapps/common/Suzerain/Suzerain_Data/StreamingAssets/aa/StandaloneWindows64/scenes_scenes_assets_scenes_mainmenu.unity_6dd6ca6b71e2733b13cf2860d4a95134.bundle")
env = UnityPy.load(str(bundle_path))

bundle_texts = set()
TMP_TEXT_SCRIPT = 7477354737935883349
for obj in env.objects:
    if obj.type.name != "MonoBehaviour":
        continue
    try:
        tree = obj.read_typetree()
    except:
        continue
    script = tree.get("m_Script")
    if not isinstance(script, dict) or script.get("m_PathID") != TMP_TEXT_SCRIPT:
        continue
    src_text = tree.get("m_text")
    if isinstance(src_text, str):
        bundle_texts.add(src_text)

print(f"Bundle m_text entries: {len(bundle_texts)}")

# Check if mapping keys exist in bundle
matches = len(set(mapping.keys()) & bundle_texts)
print(f"Matches between mapping and bundle: {matches}")

if matches > 0:
    print(f"✓ {matches} mappings will be applied!")
    # Show samples
    matched_keys = set(mapping.keys()) & bundle_texts
    for key in list(matched_keys)[:5]:
        print(f"  {key} -> {mapping[key]}")
else:
    print("✗ ERROR: No mappings match bundle texts!")
    sample_map_key = list(mapping.keys())[0] if mapping else "NO MAPPINGS"
    print(f"\nSample mapping key: '{sample_map_key}'")
    if sample_map_key in mapping:
        print(f"Maps to: {mapping[sample_map_key]}")
        print(f"Is it in bundle_texts? {sample_map_key in bundle_texts}")
        
        # Find what texts ARE in bundle (for comparison)
        print(f"\nSample bundle texts:")
        for t in list(bundle_texts)[:10]:
            print(f"  '{t}'")
