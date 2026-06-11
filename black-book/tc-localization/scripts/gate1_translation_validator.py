#!/usr/bin/env python3
"""
Gate 1: Translation File Structure Validator

Checks:
  - Translation file exists
  - File is not empty
  - File is valid UTF-8
  - Each line follows key=value format
  - No duplicate keys
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.parent
TRANSLATION_FILE = SCRIPT_DIR / "payload" / "AutoTranslator" / "Translation" / "zh-TW" / "Text" / "_Translations.txt"


def validate_translation_file() -> bool:
    """
    Validate translation file structure.
    
    Returns:
        True if valid, False otherwise
    """
    if not TRANSLATION_FILE.exists():
        print(f"[FAIL] Translation file not found: {TRANSLATION_FILE}")
        return False
    
    file_size = TRANSLATION_FILE.stat().st_size
    if file_size == 0:
        print(f"[FAIL] Translation file is empty: {TRANSLATION_FILE}")
        return False
    
    print(f"[*] Translation file size: {file_size} bytes")
    
    try:
        with open(TRANSLATION_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError as e:
        print(f"[FAIL] File is not valid UTF-8: {e}")
        return False
    
    print(f"[*] Total lines: {len(lines)}")
    
    # Check format and for duplicates
    seen_keys = set()
    invalid_lines = []
    
    for i, line in enumerate(lines, 1):
        line = line.rstrip('\n')
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue
        
        # Check for key=value format
        if '=' not in line:
            invalid_lines.append((i, line, "No '=' separator"))
            continue
        
        key, _, value = line.partition('=')
        
        if not key:
            invalid_lines.append((i, line, "Empty key"))
            continue
        
        if key in seen_keys:
            invalid_lines.append((i, line, f"Duplicate key: {key}"))
        
        seen_keys.add(key)
    
    if invalid_lines:
        print(f"[FAIL] Found {len(invalid_lines)} formatting issues:")
        for line_no, content, reason in invalid_lines[:10]:  # Show first 10
            print(f"      Line {line_no}: {reason}")
            if len(content) > 80:
                print(f"        {content[:80]}...")
            else:
                print(f"        {content}")
        return False
    
    print(f"[✓] Translation file structure valid")
    print(f"    Keys: {len(seen_keys)}")
    return True


if __name__ == "__main__":
    if not validate_translation_file():
        sys.exit(1)
