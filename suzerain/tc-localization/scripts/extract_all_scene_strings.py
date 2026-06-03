# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "UnityPy>=1.20",
# ]
# ///
"""Extract ALL strings from scene bundles (TextMeshPro, Text, and MonoBehaviour fields)."""

import json
from pathlib import Path
from collections import defaultdict
import UnityPy

def is_english_like(s):
    if not isinstance(s, str) or len(s) < 2:
        return False
    latin = sum(1 for c in s if ord(c) < 128 and c.isalpha())
    cjk = sum(1 for c in s if ord(c) >= 0x4E00)
    return latin > len(s)*0.5 and cjk == 0

def extract_all_strings_from_bundle(bundle_path: Path):
    """Extract ALL text content from a scene bundle."""
    all_english = {}
    
    with open(bundle_path, 'rb') as f:
        env = UnityPy.load(f)
    
    for obj in env.objects:
        try:
            read_obj = obj.read()
            obj_type = obj.type.name
            
            # TextMeshPro
            if hasattr(read_obj, 'm_text') and read_obj.m_text:
                text = read_obj.m_text
                if is_english_like(text):
                    all_english[text] = f"TextMeshPro ({obj.name})"
            
            # Regular Text component
            if hasattr(read_obj, 'm_Text') and read_obj.m_Text:
                text = read_obj.m_Text
                if is_english_like(text):
                    all_english[text] = f"Text ({obj.name})"
            
            # LocalizeStringEvent (localization system)
            if obj_type == 'MonoBehaviour':
                # Check for localization-related fields
                if hasattr(read_obj, 'm_LocalizationParametrs'):
                    # This might contain localization keys
                    pass
                
                # Scan all string properties
                for attr_name in dir(read_obj):
                    if attr_name.startswith('_'):
                        continue
                    try:
                        attr = getattr(read_obj, attr_name, None)
                        if isinstance(attr, str) and 10 < len(attr) < 500 and is_english_like(attr):
                            if attr not in all_english:
                                all_english[attr] = f"MonoBehaviour.{attr_name} ({obj.name})"
                    except:
                        pass
        except:
            pass
    
    return all_english

# Scan all scenes
scenes = {
    "Sordland": Path("backup/20260530-full-original/scenes_scenes_assets_scenes_sordland.unity_6a29f2cab2ef8b301931a992da045ec1.bundle"),
    "Rizia": Path("backup/20260530-full-original/scenes_scenes_assets_scenes_rizia.unity_f3aa16cfb48dca20773754a9c19d5c1d.bundle"),
    "MainMenu": Path("backup/20260530-full-original/scenes_scenes_assets_scenes_mainmenu.unity_6dd6ca6b71e2733b13cf2860d4a95134.bundle"),
}

print("=== Comprehensive String Extraction (All Types) ===\n")

for scene_name, bundle_path in scenes.items():
    print(f"\n[{scene_name}]")
    strings = extract_all_strings_from_bundle(bundle_path)
    
    if strings:
        print(f"Found {len(strings)} English-like strings:")
        # Group by type
        by_type = defaultdict(list)
        for text, source in strings.items():
            src_type = source.split(' (')[0]
            by_type[src_type].append(text)
        
        for src_type, texts in sorted(by_type.items()):
            print(f"\n  {src_type} ({len(texts)}):")
            for text in sorted(texts)[:5]:
                print(f"    - {text[:80]}")
            if len(texts) > 5:
                print(f"    ... and {len(texts)-5} more")
    else:
        print("  No English-like strings found")

# Write full list
all_strings = {}
for scene_name, bundle_path in scenes.items():
    strings = extract_all_strings_from_bundle(bundle_path)
    all_strings.update(strings)

with open('docs/all-scene-strings-comprehensive.txt', 'w') as f:
    for text in sorted(all_strings.keys()):
        f.write(f"{text}\n")

print(f"\n✓ Wrote {len(all_strings)} total strings to all-scene-strings-comprehensive.txt")
