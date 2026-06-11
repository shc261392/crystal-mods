#!/usr/bin/env python3
"""
Extract SC strings from AutoTranslator translations.

Black Book uses AutoTranslator plugin with SC source. We extract the SC translations
(left side of "SC=EN" format) to create a source for TC conversion.

This avoids the complex UnityPy parsing and uses the existing game translations.
"""

import sys
import argparse
from pathlib import Path
from collections import defaultdict

def extract_sc_from_autotranslator(game_dir):
    """
    Extract SC (Simplified Chinese) strings from AutoTranslator translation files.
    """
    autotranslator_dir = game_dir / "AutoTranslator" / "Translation" / "en" / "Text"
    
    if not autotranslator_dir.exists():
        raise FileNotFoundError(f"AutoTranslator directory not found at: {autotranslator_dir}")
    
    print(f"[*] Scanning AutoTranslator translations: {autotranslator_dir}")
    
    strings = defaultdict(int)
    sc_strings = []
    
    # Find all translation files
    translation_files = list(autotranslator_dir.glob("*.txt"))
    print(f"[*] Found {len(translation_files)} translation files")
    
    for trans_file in sorted(translation_files):
        print(f"    Reading: {trans_file.name}...", end="", flush=True)
        
        try:
            with open(trans_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.rstrip('\n\r')
                    
                    if not line or line.startswith('#'):
                        continue
                    
                    # Format: SC=EN
                    if '=' in line:
                        parts = line.split('=', 1)
                        if len(parts) == 2:
                            sc, en = parts
                            sc = sc.strip()
                            en = en.strip()
                            
                            # Only keep SC strings that are valid Chinese
                            if sc and len(sc) > 1 and len(sc) < 5000:
                                # Check if contains CJK characters
                                has_cjk = any('\u4e00' <= c <= '\u9fff' for c in sc)
                                if has_cjk:
                                    if sc not in strings:
                                        strings[sc] = 0
                                        sc_strings.append(sc)
                                    strings[sc] += 1
            
            print(f" ({len(translation_files)} lines)")
        except Exception as e:
            print(f" [ERROR] {e}")
    
    print(f"\n[✓] Extraction complete!")
    print(f"    Total SC strings found: {len(strings)}")
    print(f"    Unique strings: {len(sc_strings)}")
    
    return sc_strings, strings


def main():
    parser = argparse.ArgumentParser(
        description="Extract SC strings from Black Book's AutoTranslator translations"
    )
    parser.add_argument(
        "--game-path",
        help="Path to Black Book game directory (auto-detected if omitted)"
    )
    parser.add_argument(
        "--output",
        default="reference/SC_SOURCE.txt",
        help="Output file for extracted SC strings"
    )
    
    args = parser.parse_args()
    
    try:
        # Find game directory
        if args.game_path:
            game_dir = Path(args.game_path)
        else:
            # Try common paths
            common_paths = [
                Path("/mnt/d/SteamLibrary/steamapps/common/Black Book"),
                Path("/mnt/c/Program Files (x86)/Steam/steamapps/common/Black Book"),
                Path("/mnt/c/SteamLibrary/steamapps/common/Black Book"),
                Path.home() / ".steam" / "steam" / "steamapps" / "common" / "Black Book",
            ]
            
            game_dir = None
            for path in common_paths:
                if (path / "Black Book.exe").exists():
                    game_dir = path
                    break
            
            if not game_dir:
                raise FileNotFoundError("Black Book not found. Specify with --game-path")
        
        print(f"[*] Found Black Book at: {game_dir}\n")
        
        # Extract SC strings
        sc_strings, string_counts = extract_sc_from_autotranslator(game_dir)
        
        # Write output
        output_file = Path(args.output)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"[*] Writing to: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Simplified Chinese source strings extracted from Black Book\n")
            f.write("# Format: key=SC_value\n")
            f.write("# These will be converted to Traditional Chinese (TC) using OpenCC\n\n")
            
            for idx, sc in enumerate(sc_strings, 1):
                f.write(f"text_{idx}={sc}\n")
        
        print(f"[✓] Output written: {output_file}")
        print(f"    Total lines: {len(sc_strings)}")
        
    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
