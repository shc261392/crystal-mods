#!/usr/bin/env python3
"""Debug script to inspect Black Book asset structure."""

import sys
from pathlib import Path
from collections import Counter

try:
    from UnityPy import Environment
except ImportError:
    print("ERROR: UnityPy not installed. Run: pip install UnityPy")
    sys.exit(1)

GAME_PATH = Path("/mnt/d/SteamLibrary/steamapps/common/Black Book")
DATA_DIR = GAME_PATH / "Black Book_Data"

def inspect_resource(resource_file):
    """Inspect object types in a resource file."""
    print(f"\n{'='*60}")
    print(f"Inspecting: {resource_file.name}")
    print('='*60)
    
    try:
        with open(resource_file, 'rb') as f:
            env = Environment(f)
            
            object_types = Counter()
            total_objects = 0
            text_objects = []
            
            for container in env.container.values():
                for obj in container.objects.values():
                    total_objects += 1
                    obj_type = obj.__class__.__name__
                    object_types[obj_type] += 1
                    
                    # Check for text-related fields
                    if hasattr(obj, '__dict__'):
                        attrs = vars(obj)
                        for key, value in attrs.items():
                            if isinstance(value, str) and len(value) > 5:
                                text_objects.append((obj_type, key, value[:80]))
            
            print(f"Total objects: {total_objects}")
            print(f"\nObject types found:")
            for obj_type, count in object_types.most_common(20):
                print(f"  {obj_type}: {count}")
            
            if text_objects:
                print(f"\nText-like content found ({len(text_objects)} samples):")
                for obj_type, key, value in text_objects[:10]:
                    print(f"  [{obj_type}] {key}: {repr(value)}")
    
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")


# Scan all .resource files
print(f"Scanning Black Book assets: {DATA_DIR}")
for resource_file in sorted(DATA_DIR.glob("*.resource")):
    inspect_resource(resource_file)

# Check for specific text asset types
print(f"\n{'='*60}")
print("Looking for text asset files in StreamingAssets...")
print('='*60)

streaming_dir = DATA_DIR / "StreamingAssets"
if streaming_dir.exists():
    text_assets = list(streaming_dir.glob("**/*.asset")) + list(streaming_dir.glob("**/*.json"))
    print(f"Found {len(text_assets)} potential assets")
    for asset in text_assets[:5]:
        print(f"  {asset.relative_to(DATA_DIR)}")
