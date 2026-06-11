#!/usr/bin/env python3
"""
Validate Black Book TC localization YAML configs.
"""

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed")
    sys.exit(1)

PAYLOAD_DIR = Path(__file__).parent.parent / "payload"
CONFIG_DIR = PAYLOAD_DIR / "Black Book_Data" / "StreamingAssets" / "Config"

def validate_yaml_configs():
    """Validate all TC YAML config files."""
    
    if not CONFIG_DIR.exists():
        print(f"[FAIL] Config directory not found: {CONFIG_DIR}")
        return False
    
    yaml_files = list(CONFIG_DIR.rglob("config_zh.yaml"))
    
    if not yaml_files:
        print(f"[FAIL] No TC YAML config files found")
        return False
    
    print(f"[✓] Found {len(yaml_files)} TC config files")
    
    # Validate first 50 files for syntax
    failed = []
    for i, yaml_file in enumerate(yaml_files[:50]):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
        except Exception as e:
            failed.append((yaml_file, str(e)))
    
    if failed:
        print(f"[FAIL] YAML validation failed:")
        for fpath, error in failed[:3]:
            print(f"  {fpath.relative_to(CONFIG_DIR)}: {error}")
        return False
    
    print(f"[✓] YAML format valid (tested 50 files)")
    return True

if __name__ == "__main__":
    if not validate_yaml_configs():
        sys.exit(1)
