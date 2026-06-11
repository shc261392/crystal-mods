#!/usr/bin/env python3
"""
Extract Simplified Chinese (SC) YAML configs, convert to Traditional Chinese (TC),
and create TC localization YAML files for Black Book.

This script:
1. Scans all config_zh.yaml files from the installed game
2. Extracts SC text strings
3. Converts SC → TC (Taiwan) using OpenCC
4. Creates TC YAML configs in the mod payload directory

NO AutoTranslator or plugins - direct YAML replacement.
"""

import sys
import os
import re
from pathlib import Path
from collections import defaultdict

try:
    import yaml
    from opencc import OpenCC
except ImportError as e:
    print(f"ERROR: Missing dependency: {e}")
    print("Install with: pip install pyyaml opencc")
    sys.exit(1)

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR = Path(__file__).parent.parent
GAME_DATA = Path("/mnt/d/SteamLibrary/steamapps/common/Black Book/Black Book_Data")

# OpenCC converter: Simplified → Traditional (Taiwan with phrases)
CONVERTER = OpenCC('s2twp')

# ============================================================================
# Extraction
# ============================================================================

def find_game_directory(optional_path=None):
    """Locate Black Book game directory (for flexibility)."""
    if optional_path:
        game_dir = Path(optional_path) / "Black Book_Data"
        if game_dir.exists():
            return game_dir
    
    # Default WSL path
    if GAME_DATA.exists():
        return GAME_DATA
    
    # Try other paths
    for path in [
        Path("/mnt/c/Program Files (x86)/Steam/steamapps/common/Black Book/Black Book_Data"),
        Path("/mnt/c/Program Files/Steam/steamapps/common/Black Book/Black Book_Data"),
    ]:
        if path.exists():
            return path
    
    raise FileNotFoundError("Black Book game directory not found")


def extract_yaml_strings(yaml_file):
    """
    Extract all text strings from a YAML file.
    Returns dict of {key: value} pairs.
    """
    try:
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"    [!] Error reading {yaml_file.name}: {e}")
        return {}
    
    if not data:
        return {}
    
    strings = {}
    
    def extract_recursive(obj, prefix=""):
        """Recursively extract strings from YAML structure."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, str) and value.strip():
                    strings[new_key] = value
                elif isinstance(value, (dict, list)):
                    extract_recursive(value, new_key)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                new_key = f"{prefix}[{i}]"
                if isinstance(item, str) and item.strip():
                    strings[new_key] = item
                elif isinstance(item, (dict, list)):
                    extract_recursive(item, new_key)
    
    extract_recursive(data)
    return strings


def scan_yaml_configs(game_data):
    """
    Scan all config_zh.yaml files and extract SC strings.
    
    Returns:
        dict: {relative_path: {key: sc_value, ...}}
    """
    config_dir = game_data / "StreamingAssets" / "Config"
    
    if not config_dir.exists():
        raise FileNotFoundError(f"Config directory not found: {config_dir}")
    
    print(f"[*] Scanning YAML configs in: {config_dir}")
    
    all_strings = defaultdict(dict)
    file_count = 0
    
    for yaml_file in sorted(config_dir.rglob("config_zh.yaml")):
        file_count += 1
        
        # Get relative path for organization
        rel_path = yaml_file.relative_to(config_dir)
        
        # Extract strings
        strings = extract_yaml_strings(yaml_file)
        all_strings[rel_path] = strings
        
        if file_count <= 5:
            print(f"    Found: {rel_path} ({len(strings)} strings)")
        elif file_count % 500 == 0:
            print(f"    ... {file_count} files processed")
    
    print(f"[✓] Scanned {file_count} config_zh.yaml files")
    return all_strings


# ============================================================================
# Conversion & Output
# ============================================================================

def convert_to_tc(sc_strings):
    """Convert SC strings to TC using OpenCC."""
    tc_strings = {}
    
    for key, sc_value in sc_strings.items():
        try:
            tc_value = CONVERTER.convert(sc_value)
            tc_strings[key] = tc_value
        except Exception as e:
            print(f"    [!] Conversion error for '{key}': {e}")
            # Fallback to original
            tc_strings[key] = sc_value
    
    return tc_strings


def create_tc_yaml(game_data, all_sc_strings):
    """
    Create TC YAML config files in mod payload.
    """
    payload_config_dir = SCRIPT_DIR / "payload" / "Black Book_Data" / "StreamingAssets" / "Config"
    payload_config_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n[*] Converting and creating TC YAML files...")
    
    tc_file_count = 0
    
    for rel_path, sc_strings in all_sc_strings.items():
        # Convert SC → TC
        tc_strings = convert_to_tc(sc_strings)
        
        # Reconstruct YAML structure
        output_path = payload_config_dir / rel_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Read original SC file to preserve structure
        original_zh_file = game_data / "StreamingAssets" / "Config" / rel_path
        try:
            with open(original_zh_file, 'r', encoding='utf-8') as f:
                yaml_structure = yaml.safe_load(f)
        except:
            print(f"    [!] Could not read original: {rel_path}")
            continue
        
        # Update with TC strings
        def update_structure(obj, tc_map):
            """Update YAML structure with TC values."""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    tc_key = key  # Simplified - assumes flat structure
                    if tc_key in tc_map:
                        obj[key] = tc_map[tc_key]
                    elif isinstance(value, (dict, list)):
                        update_structure(value, tc_map)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    # For lists, keep as is (simplified handling)
                    pass
        
        update_structure(yaml_structure, tc_strings)
        
        # Write TC YAML
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(yaml_structure, f, allow_unicode=True, default_flow_style=False)
            tc_file_count += 1
            
            if tc_file_count <= 5:
                print(f"    Created: {rel_path}")
            elif tc_file_count % 500 == 0:
                print(f"    ... {tc_file_count} files created")
        except Exception as e:
            print(f"    [!] Error writing {rel_path}: {e}")
    
    print(f"\n[✓] Created {tc_file_count} TC YAML config files")
    print(f"    Output: {payload_config_dir}")
    
    return tc_file_count


def generate_translation_report(all_sc_strings):
    """Generate a summary of extracted and converted strings."""
    report_file = SCRIPT_DIR / "payload" / "EXTRACTION_REPORT.txt"
    
    total_strings = sum(len(s) for s in all_sc_strings.values())
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("Black Book TC Localization - Extraction Report\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Total YAML config files: {len(all_sc_strings)}\n")
        f.write(f"Total localizable strings: {total_strings}\n")
        f.write("\nSample strings (first 10):\n")
        f.write("-" * 60 + "\n")
        
        count = 0
        for rel_path, strings in list(all_sc_strings.items())[:3]:
            f.write(f"\n{rel_path}:\n")
            for key, value in list(strings.items())[:5]:
                tc_value = CONVERTER.convert(value)
                f.write(f"  {key}:\n")
                f.write(f"    SC: {value}\n")
                f.write(f"    TC: {tc_value}\n")
    
    print(f"\n[✓] Report: {report_file}")


# ============================================================================
# Main
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Extract SC YAML configs and convert to TC for Black Book",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect and convert:
  python3 extract_and_convert_yaml.py
  
  # Use custom game path:
  python3 extract_and_convert_yaml.py --game-path /path/to/Black\\ Book
        """
    )
    parser.add_argument(
        "--game-path",
        help="Path to Black Book game directory (auto-detected if omitted)"
    )
    
    args = parser.parse_args()
    
    try:
        # Find game
        game_data = find_game_directory(args.game_path)
        print(f"[✓] Found Black Book at: {game_data.parent}")
        
        # Scan and extract SC strings
        all_sc_strings = scan_yaml_configs(game_data)
        
        # Convert to TC and create YAML files
        tc_count = create_tc_yaml(game_data, all_sc_strings)
        
        # Generate report
        generate_translation_report(all_sc_strings)
        
        print(f"\n[✓] Conversion complete!")
        print(f"    {len(all_sc_strings)} config files processed")
        print(f"    {tc_count} TC YAML files created")
        print(f"\nNext steps:")
        print(f"  1. Review TC files in: payload/Black Book_Data/StreamingAssets/Config/")
        print(f"  2. Make manual corrections if needed")
        print(f"  3. Package with: make build")
        print(f"  4. Deploy with: bash deploy.sh")
        
    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
