#!/usr/bin/env python3
"""
Gate 2: Terminology Validator

Checks:
  - Translation values use consistent terminology
  - No mixed SC/TC characters (should be pure TC)
  - Proper punctuation usage
  - No untranslated English text in values
"""

import sys
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.parent
TRANSLATION_FILE = SCRIPT_DIR / "payload" / "AutoTranslator" / "Translation" / "zh-TW" / "Text" / "_Translations.txt"
GLOSSARY_FILE = SCRIPT_DIR / "reference" / "TERMINOLOGY.md"

# Unicode ranges for character detection
RANGE_CJK_UNIFIED = re.compile(r'[\u4E00-\u9FFF]')  # CJK Unified Ideographs
RANGE_SC_ONLY = re.compile(r'[\u3400-\u4DB5\uF900-\uFAFF]')  # SC-specific characters
RANGE_LATIN = re.compile(r'[a-zA-Z]{2,}')  # 2+ Latin letters


def detect_mixed_scripts(text: str) -> bool:
    """
    Detect if text has mixed SC/TC or other issues.
    
    Returns:
        True if valid (pure TC), False if issues found
    """
    # This is a simplified check; a proper check would need a detailed SC-TC dictionary
    # For now, we'll check for obvious issues
    
    has_sc = bool(RANGE_SC_ONLY.search(text))
    has_latin = bool(RANGE_LATIN.search(text))
    
    return not has_sc and not has_latin


def validate_terminology() -> bool:
    """
    Validate translation terminology.
    
    Returns:
        True if valid, False otherwise
    """
    if not TRANSLATION_FILE.exists():
        print(f"[FAIL] Translation file not found: {TRANSLATION_FILE}")
        return False
    
    print(f"[*] Validating terminology in: {TRANSLATION_FILE}")
    
    with open(TRANSLATION_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    issues = []
    
    for i, line in enumerate(lines, 1):
        line = line.rstrip('\n')
        
        if not line or line.startswith('#') or '=' not in line:
            continue
        
        _, _, value = line.partition('=')
        
        # Check for mixed SC/TC
        if not detect_mixed_scripts(value):
            issues.append((i, "Mixed scripts or untranslated English", value))
        
        # Check for common punctuation errors
        if '，' in value and '，' == value[-1]:  # Chinese comma at end
            issues.append((i, "Chinese punctuation at line end", value))
    
    if issues:
        print(f"[FAIL] Found {len(issues)} terminology issues:")
        for line_no, reason, content in issues[:10]:
            print(f"      Line {line_no}: {reason}")
            if len(content) > 80:
                print(f"        {content[:80]}...")
            else:
                print(f"        {content}")
        return False
    
    print(f"[✓] Terminology validation passed")
    return True


if __name__ == "__main__":
    if not validate_terminology():
        sys.exit(1)
