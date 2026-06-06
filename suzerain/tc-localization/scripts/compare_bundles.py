# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "UnityPy>=1.20",
# ]
# ///
"""Compare translated strings between two bundles."""

import sys
from pathlib import Path
import UnityPy
from collections import Counter

def get_chinese_texts(bundle_path):
    """Extract all Chinese strings from a bundle."""
    texts = []
    with open(bundle_path, 'rb') as f:
        env = UnityPy.load(f)
    
    for obj in env.objects:
        try:
            read_obj = obj.read()
            if hasattr(read_obj, 'm_text') and read_obj.m_text:
                text = read_obj.m_text
                if any(ord(c) > 127 for c in text):
                    texts.append(text)
        except:
            pass
    
    return texts

if __name__ == "__main__":
    backup_path = Path("backup/20260603-214207-rizia-tmp-deploy/scenes_scenes_assets_scenes_rizia.unity_f3aa16cfb48dca20773754a9c19d5c1d.bundle")
    build_path = Path("build.minimal/scenes_scenes_assets_scenes_rizia.unity_f3aa16cfb48dca20773754a9c19d5c1d.bundle")
    
    print("Extracting Chinese texts from both bundles...")
    backup_texts = get_chinese_texts(backup_path)
    build_texts = get_chinese_texts(build_path)
    
    print(f"\nBackup rizia: {len(backup_texts)} Chinese strings")
    print(f"Build minimal: {len(build_texts)} Chinese strings")
    print()
    
    backup_set = set(backup_texts)
    build_set = set(build_texts)
    
    print(f"Only in backup: {len(backup_set - build_set)}")
    if backup_set - build_set:
        for t in list(backup_set - build_set)[:5]:
            print(f"  - {t[:60]}")
    
    print(f"\nOnly in build.minimal: {len(build_set - backup_set)}")
    if build_set - backup_set:
        for t in list(build_set - backup_set)[:5]:
            print(f"  + {t[:60]}")
    
    print(f"\nCommon: {len(backup_set & build_set)}")
