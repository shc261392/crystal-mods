#!/usr/bin/env python3
"""
COMPLETE Black Book TC Localization Extractor

Extracts ALL text fields from YAML configs (Name, Description, Flavour,
ShortQuestDescr, LongQuestDescr, LocationName, etc.) and converts from
Simplified Chinese (SC) to Traditional Chinese (TC).

Statistics:
  - Name: ~1,440 strings
  - Description: ~568 strings
  - Flavour: ~191 strings
  - Other: ShortQuestDescr, LongQuestDescr, LocationName, etc.
  - TOTAL: ~2,300+ localizable strings
"""

import sys
from pathlib import Path
from collections import defaultdict
import yaml

try:
    from opencc import OpenCC
except ImportError:
    print("ERROR: opencc not installed. Run: pip install opencc-python-py")
    sys.exit(1)

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR = Path(__file__).parent.parent
GAME_DATA = Path("/mnt/d/SteamLibrary/steamapps/common/Black Book/Black Book_Data")

# OpenCC converter: SC → TC (Taiwan traditional Chinese with phrases)
CONVERTER = OpenCC('s2twp')

# Text fields to extract from YAML files (comprehensive list)
TEXT_FIELDS = {
    "Name": "Item/ability/location name",
    "Description": "Item/ability description with effect details",
    "Flavour": "Flavor/lore text",
    "ShortQuestDescr": "Short quest description",
    "LongQuestDescr": "Long quest description",
    "LocationName": "Location name",
    "ShortDescription": "Short description",
    # Credits/metadata fields (if localized)
    "Developers": "Developer names",
    "Publishers": "Publisher names",
    "Thanks": "Special thanks",
    "Backers": "Backer names",
    "SuperBackers": "Super backer names",
    "Literature": "Literature credits",
    "Music": "Music credits",
}

# ============================================================================
# Extraction
# ============================================================================

def extract_text_fields(yaml_file):
    """Extract TEXT_FIELDS from a YAML file."""
    try:
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"    [!] Error reading {yaml_file.name}: {e}")
        return {}
    
    if not data:
        return {}
    
    extracted = {}
    for field in TEXT_FIELDS.keys():
        if field in data and isinstance(data[field], str) and data[field].strip():
            extracted[field] = data[field]
    
    return extracted


def scan_all_configs(game_data):
    """
    Scan all config_zh.yaml files and extract ALL text fields.
    
    Returns:
        tuple: (file_count, field_counts, all_configs)
          - file_count: total files scanned
          - field_counts: {field_name: count}
          - all_configs: {rel_path: {field: value}}
    """
    config_dir = game_data / "StreamingAssets" / "Config"
    
    if not config_dir.exists():
        raise FileNotFoundError(f"Config directory not found: {config_dir}")
    
    print(f"[*] Scanning YAML configs in: {config_dir}")
    
    all_configs = {}
    field_counts = defaultdict(int)
    file_count = 0
    
    for yaml_file in sorted(config_dir.rglob("config_zh.yaml")):
        file_count += 1
        rel_path = yaml_file.relative_to(config_dir)
        
        # Extract text fields
        fields = extract_text_fields(yaml_file)
        if fields:
            all_configs[rel_path] = fields
            for field in fields.keys():
                field_counts[field] += 1
        
        if file_count % 500 == 0:
            print(f"    ... {file_count} files processed")
    
    print(f"[✓] Scanned {file_count} config_zh.yaml files")
    print(f"\nField counts:")
    for field in sorted(TEXT_FIELDS.keys()):
        count = field_counts.get(field, 0)
        if count > 0:
            print(f"    {field:20} {count:6} strings")
    
    return file_count, dict(field_counts), all_configs


# ============================================================================
# Conversion & Output
# ============================================================================

def create_tc_configs(game_data, all_configs):
    """
    Create TC config files with ALL text fields converted.
    Preserves YAML structure from original SC files.
    """
    payload_config_dir = SCRIPT_DIR / "payload" / "Black Book_Data" / "StreamingAssets" / "Config"
    payload_config_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n[*] Creating TC config files with converted text...")
    
    tc_file_count = 0
    tc_string_count = 0
    
    for rel_path, sc_fields in all_configs.items():
        # Read original SC file to preserve full structure
        original_file = game_data / "StreamingAssets" / "Config" / rel_path
        try:
            with open(original_file, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)
        except Exception as e:
            print(f"    [!] Error reading original {rel_path}: {e}")
            continue
        
        # Convert text fields SC → TC
        for field, sc_value in sc_fields.items():
            try:
                tc_value = CONVERTER.convert(sc_value)
                yaml_data[field] = tc_value
                tc_string_count += 1
            except Exception as e:
                print(f"    [!] Conversion error for {rel_path}.{field}: {e}")
        
        # Write TC config file
        output_path = payload_config_dir / rel_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(yaml_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            tc_file_count += 1
            
            if tc_file_count % 500 == 0:
                print(f"    ... {tc_file_count} files created")
        except Exception as e:
            print(f"    [!] Error writing {rel_path}: {e}")
    
    print(f"\n[✓] Created {tc_file_count} TC config files")
    print(f"[✓] Converted {tc_string_count} text strings (SC → TC)")
    print(f"    Output: {payload_config_dir}")
    
    return tc_file_count, tc_string_count


# ============================================================================
# Reporting
# ============================================================================

def generate_translations_list(all_configs):
    """Generate human-readable translations list."""
    output_file = SCRIPT_DIR / "payload" / "TRANSLATIONS_LIST.txt"
    
    # Organize by field type and category
    by_field = defaultdict(list)
    for rel_path, fields in all_configs.items():
        category = rel_path.parts[0]  # Top-level directory (Abilities, Locations, etc.)
        for field, sc_value in fields.items():
            tc_value = CONVERTER.convert(sc_value)
            by_field[field].append({
                'category': category,
                'sc': sc_value,
                'tc': tc_value,
            })
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("BLACK BOOK TC LOCALIZATION — COMPLETE TRANSLATIONS LIST\n")
        f.write("=" * 80 + "\n")
        f.write(f"\nGenerated from {len(all_configs)} config files\n")
        f.write(f"Total strings converted: {sum(len(items) for items in by_field.values())}\n\n")
        
        for field in sorted(TEXT_FIELDS.keys()):
            items = by_field.get(field, [])
            if not items:
                continue
            
            f.write(f"\n[{field.upper()}] — {len(items)} strings\n")
            f.write("-" * 80 + "\n")
            
            # Sort by SC text
            for item in sorted(items, key=lambda x: x['sc']):
                f.write(f"  SC: {item['sc']:50} → {item['tc']}\n")
    
    print(f"\n[✓] Translations list: {output_file}")
    print(f"    Human-readable reference of all conversions")


# ============================================================================
# Main
# ============================================================================

def main():
    print("=" * 80)
    print("BLACK BOOK — COMPREHENSIVE TC LOCALIZATION EXTRACTOR")
    print("=" * 80)
    print()
    
    # Verify game directory
    if not GAME_DATA.exists():
        print(f"[ERROR] Game directory not found: {GAME_DATA}")
        print("        Install Black Book to Steam first")
        sys.exit(1)
    
    # Extract all text fields
    file_count, field_counts, all_configs = scan_all_configs(GAME_DATA)
    
    if not all_configs:
        print("[ERROR] No text fields extracted!")
        sys.exit(1)
    
    # Create TC configs
    tc_files, tc_strings = create_tc_configs(GAME_DATA, all_configs)
    
    # Generate reference list
    generate_translations_list(all_configs)
    
    print("\n" + "=" * 80)
    print("EXTRACTION COMPLETE")
    print("=" * 80)
    print(f"Extracted text fields: {sum(field_counts.values())}")
    print(f"Created TC configs: {tc_files}")
    print(f"Converted strings: {tc_strings}")
    print("\nFiles ready for deployment:")
    print(f"  - payload/Black Book_Data/StreamingAssets/Config/ (TC YAML files)")
    print(f"  - payload/TRANSLATIONS_LIST.txt (human-readable reference)")
    print()


if __name__ == "__main__":
    main()
