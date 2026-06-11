#!/usr/bin/env python3
"""
Convert Simplified Chinese (SC) to Traditional Chinese (TC)
using OpenCC library with Taiwan phrase substitution.

Usage:
    python3 convert_sc_to_tc.py [source_file] [output_file]

Requirements:
    pip install opencc
"""

import sys
import os
import argparse
from pathlib import Path

try:
    from opencc import OpenCC
except ImportError:
    print("ERROR: opencc module not installed.")
    print("Install it with: pip install opencc")
    sys.exit(1)

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR = Path(__file__).parent.parent
SOURCE_FILE = SCRIPT_DIR / "reference" / "SC_SOURCE.txt"
OUTPUT_FILE = SCRIPT_DIR / "payload" / "AutoTranslator" / "Translation" / "zh-TW" / "Text" / "_Translations.txt"

# OpenCC configurations: Taiwan Traditional Chinese with phrase substitution
OPENCC_CONFIG = "s2twp.json"  # Simplified → Traditional (Taiwan, with phrases)


# ============================================================================
# Conversion
# ============================================================================

def convert_file(source_path: Path, output_path: Path) -> None:
    """
    Convert SC to TC using OpenCC.
    
    Args:
        source_path: Path to source SC translation file
        output_path: Path to output TC translation file
        
    Raises:
        FileNotFoundError: If source file doesn't exist
    """
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")
    
    print(f"[*] Loading OpenCC config: {OPENCC_CONFIG}")
    converter = OpenCC(OPENCC_CONFIG)
    
    print(f"[*] Reading source file: {source_path}")
    with open(source_path, 'r', encoding='utf-8') as f:
        source_text = f.read()
    
    line_count = source_text.count('\n') + 1
    print(f"[*] Source file: {line_count} lines")
    
    print(f"[*] Converting SC → TC (Taiwan)...")
    tc_text = converter.convert(source_text)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"[*] Writing output file: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(tc_text)
    
    print(f"[✓] Conversion complete: {output_path}")
    print(f"    Lines: {line_count}")
    print(f"    Size: {len(tc_text)} bytes")


def main():
    parser = argparse.ArgumentParser(
        description="Convert SC to TC using OpenCC"
    )
    parser.add_argument(
        "source",
        nargs="?",
        default=str(SOURCE_FILE),
        help=f"Source SC file (default: {SOURCE_FILE})"
    )
    parser.add_argument(
        "output",
        nargs="?",
        default=str(OUTPUT_FILE),
        help=f"Output TC file (default: {OUTPUT_FILE})"
    )
    
    args = parser.parse_args()
    
    source_path = Path(args.source)
    output_path = Path(args.output)
    
    try:
        convert_file(source_path, output_path)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
