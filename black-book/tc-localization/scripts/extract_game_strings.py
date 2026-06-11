#!/usr/bin/env python3
"""
Extract string assets from Black Book using UnityPy.

This script scans Unity asset bundles and serialized files to extract
all localizable strings (UI, dialogue, item descriptions, etc.).

SMART AUTO-DETECTION: Automatically finds Black Book installation across:
- Windows (native & WSL2 mounts)
- Linux (native Steam installations)
- Multiple Steam library folders

Usage:
    python3 extract_game_strings.py [--output strings_extracted.txt] [--game-path PATH]

Requirements:
    pip install UnityPy
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path
from collections import defaultdict

try:
    from UnityPy import Environment
except ImportError:
    print("ERROR: UnityPy module not installed.")
    print("Install it with: pip install UnityPy")
    sys.exit(1)

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR = Path(__file__).parent.parent
STEAM_APP_ID = "1138660"
GAME_NAME = "Black Book"

# ============================================================================
# Steam Auto-Detection
# ============================================================================

def find_steam_config_vdf():
    """
    Locate Steam's libraryfolders.vdf to find all Steam library paths.
    Searches Windows drives (via WSL /mnt/) and native Linux.
    
    Returns:
        Path to libraryfolders.vdf or None
    """
    possible_paths = [
        # Native Linux paths
        Path.home() / ".steam" / "steam" / "steamapps" / "libraryfolders.vdf",
        Path.home() / ".steam" / "root" / "steamapps" / "libraryfolders.vdf",
        Path.home() / ".local" / "share" / "Steam" / "steamapps" / "libraryfolders.vdf",
        # Windows via WSL - all drives C through G
        Path("/mnt/c/Program Files (x86)/Steam/steamapps/libraryfolders.vdf"),
        Path("/mnt/c/Program Files/Steam/steamapps/libraryfolders.vdf"),
        Path("/mnt/c/SteamLibrary/steamapps/libraryfolders.vdf"),
        Path("/mnt/d/Program Files (x86)/Steam/steamapps/libraryfolders.vdf"),
        Path("/mnt/d/Program Files/Steam/steamapps/libraryfolders.vdf"),
        Path("/mnt/d/SteamLibrary/steamapps/libraryfolders.vdf"),
        Path("/mnt/e/Program Files (x86)/Steam/steamapps/libraryfolders.vdf"),
        Path("/mnt/e/Program Files/Steam/steamapps/libraryfolders.vdf"),
        Path("/mnt/e/SteamLibrary/steamapps/libraryfolders.vdf"),
        Path("/mnt/f/Program Files (x86)/Steam/steamapps/libraryfolders.vdf"),
        Path("/mnt/f/Program Files/Steam/steamapps/libraryfolders.vdf"),
        Path("/mnt/f/SteamLibrary/steamapps/libraryfolders.vdf"),
        Path("/mnt/g/Program Files (x86)/Steam/steamapps/libraryfolders.vdf"),
        Path("/mnt/g/Program Files/Steam/steamapps/libraryfolders.vdf"),
        Path("/mnt/g/SteamLibrary/steamapps/libraryfolders.vdf"),
    ]
    
    for path in possible_paths:
        if path.exists():
            print(f"[*] Found Steam config: {path}")
            return path
    
    return None


def parse_steam_libraries(vdf_path):
    """
    Parse Steam's libraryfolders.vdf to extract all library paths.
    Simple parsing (not a full VDF parser).
    
    Args:
        vdf_path: Path to libraryfolders.vdf
        
    Returns:
        List of library directory paths
    """
    libraries = []
    
    try:
        with open(vdf_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Simple regex to find path= entries
            import re
            matches = re.findall(r'"path"\s+"([^"]+)"', content)
            
            for match in matches:
                lib_path = Path(match)
                if lib_path.exists():
                    libraries.append(lib_path)
                    print(f"[*] Found Steam library: {lib_path}")
    except Exception as e:
        print(f"[!] Error parsing VDF: {e}")
    
    return libraries


def scan_steam_library(lib_path):
    """
    Scan a Steam library folder for Black Book installation.
    
    Args:
        lib_path: Path to Steam library
        
    Returns:
        Path to Black Book directory or None
    """
    common_path = lib_path / "steamapps" / "common" / "Black Book"
    
    if (common_path / "Black Book.exe").exists():
        print(f"[✓] Found Black Book at: {common_path}")
        return common_path
    
    # Try alternate names
    for name_variant in ["black-book", "BlackBook", "blackbook"]:
        variant_path = lib_path / "steamapps" / "common" / name_variant
        if (variant_path / "Black Book.exe").exists():
            print(f"[✓] Found Black Book at: {variant_path}")
            return variant_path
    
    return None


def find_game_directory(optional_path=None):
    """
    Locate Black Book game directory using smart auto-detection.
    
    Args:
        optional_path: User-provided path override
        
    Returns:
        Path to game directory
        
    Raises:
        FileNotFoundError: If game directory not found
    """
    # User override
    if optional_path:
        game_dir = Path(optional_path)
        if (game_dir / "Black Book.exe").exists():
            print(f"[✓] Using provided path: {game_dir}")
            return game_dir
        elif (game_dir.parent / "Black Book.exe").exists():
            game_dir = game_dir.parent
            print(f"[✓] Using provided path: {game_dir}")
            return game_dir
        else:
            raise FileNotFoundError(f"Black Book not found at: {optional_path}")
    
    print(f"[*] Searching for {GAME_NAME} installation...")
    
    # Check common direct locations first (fast path) - includes all Windows drives via WSL
    direct_paths = [
        # Linux native
        Path.home() / ".steam" / "steam" / "steamapps" / "common" / "Black Book",
        # Windows via WSL - All drives C through G
        Path("/mnt/c/Program Files (x86)/Steam/steamapps/common/Black Book"),
        Path("/mnt/c/Program Files/Steam/steamapps/common/Black Book"),
        Path("/mnt/c/SteamLibrary/steamapps/common/Black Book"),
        Path("/mnt/d/Program Files (x86)/Steam/steamapps/common/Black Book"),
        Path("/mnt/d/Program Files/Steam/steamapps/common/Black Book"),
        Path("/mnt/d/SteamLibrary/steamapps/common/Black Book"),
        Path("/mnt/e/Program Files (x86)/Steam/steamapps/common/Black Book"),
        Path("/mnt/e/Program Files/Steam/steamapps/common/Black Book"),
        Path("/mnt/e/SteamLibrary/steamapps/common/Black Book"),
        Path("/mnt/f/Program Files (x86)/Steam/steamapps/common/Black Book"),
        Path("/mnt/f/Program Files/Steam/steamapps/common/Black Book"),
        Path("/mnt/f/SteamLibrary/steamapps/common/Black Book"),
        Path("/mnt/g/Program Files (x86)/Steam/steamapps/common/Black Book"),
        Path("/mnt/g/Program Files/Steam/steamapps/common/Black Book"),
        Path("/mnt/g/SteamLibrary/steamapps/common/Black Book"),
    ]
    
    for path in direct_paths:
        if (path / "Black Book.exe").exists():
            print(f"[✓] Found Black Book at: {path}")
            return path
    
    # Scan Steam libraries via libraryfolders.vdf
    vdf_path = find_steam_config_vdf()
    if vdf_path:
        libraries = parse_steam_libraries(vdf_path)
        for lib_path in libraries:
            result = scan_steam_library(lib_path)
            if result:
                return result
    
    # Fallback: try to use `steam` CLI
    try:
        print("[*] Trying Steam CLI detection...")
        result = subprocess.run(
            ["steam", "run", "sh", "-c", f"find ~/.steam/steam/steamapps -name 'Black Book.exe' 2>/dev/null"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            found_path = Path(result.stdout.strip()).parent
            print(f"[✓] Found via Steam CLI: {found_path}")
            return found_path
    except:
        pass
    
    raise FileNotFoundError(
        f"[ERROR] {GAME_NAME} installation not found.\n"
        f"Tried: common Steam paths, libraryfolders.vdf scan, Steam CLI\n"
        f"Specify manually with: python3 extract_game_strings.py --game-path /path/to/Black\\ Book"
    )


# ============================================================================
# Asset Extraction
# ============================================================================

def extract_text_from_asset(obj, strings_dict, verbose=False):
    """
    Recursively extract text strings from Unity objects.
    """
    if not hasattr(obj, '__dict__'):
        return
    
    obj_type = obj.__class__.__name__
    
    # Extract from known text components
    if obj_type in ('Text', 'TextMeshPro', 'TextMeshProUGUI', 'TextMesh'):
        if hasattr(obj, 'm_Text') and obj.m_Text:
            key = f"text_{id(obj) % 10000}"
            strings_dict[key] = obj.m_Text
            if verbose:
                print(f"          [TEXT] {obj_type}: {obj.m_Text[:50]}")
    
    # Extract from generic text fields - try all possible attribute names
    text_attrs = ['text', 'm_text', 'Text', 'content', 'value', 'description', 
                  'm_Content', 'm_Description', 'title', 'm_Title', 'label', 'm_Label',
                  'question', 'm_Question', 'answer', 'm_Answer']
    
    for attr in text_attrs:
        if hasattr(obj, attr):
            try:
                val = getattr(obj, attr)
                if isinstance(val, str) and len(val) > 2 and len(val) < 5000:
                    # Filter out hashes and GUIDs
                    if not all(c in '0123456789abcdefABCDEF-' for c in val):
                        key = f"{obj_type.lower()}_{attr}_{id(obj) % 10000}"
                        if key not in strings_dict:
                            strings_dict[key] = val
                            if verbose:
                                print(f"          [{attr}] {obj_type}: {val[:50]}")
            except:
                pass


def scan_assets(game_dir, output_file):
    """
    Scan and extract strings from all Black Book assets.
    Primary source: data.unity3d (1.1GB asset bundle)
    """
    data_dir = game_dir / "Black Book_Data"
    
    if not data_dir.exists():
        raise FileNotFoundError(f"Game data directory not found: {data_dir}")
    
    print(f"[*] Scanning game assets in: {data_dir}")
    
    strings = defaultdict(list)
    file_count = 0
    
    # Primary: Scan data.unity3d (main asset bundle)
    main_bundle = data_dir / "data.unity3d"
    if main_bundle.exists():
        print(f"[*] Scanning main asset bundle: data.unity3d (this may take 1-2 minutes)...")
        try:
            with open(main_bundle, 'rb') as f:
                env = Environment(f)
                obj_count = 0
                for container in env.container.values():
                    for obj in container.objects.values():
                        extract_text_from_asset(obj, strings)
                        obj_count += 1
                print(f"    Processed {obj_count} objects from data.unity3d")
            file_count += 1
        except Exception as e:
            print(f"    [!] Error: {type(e).__name__}: {str(e)[:100]}")
    
    # Secondary: Scan .resource files
    print("[*] Scanning .resource files...")
    for resource_file in sorted(data_dir.glob("*.resource")):
        print(f"    {resource_file.name}...")
        try:
            with open(resource_file, 'rb') as f:
                env = Environment(f)
                obj_count = 0
                for container in env.container.values():
                    for obj in container.objects.values():
                        extract_text_from_asset(obj, strings)
                        obj_count += 1
                if obj_count > 0:
                    print(f"        Found {obj_count} objects")
                    file_count += 1
        except Exception as e:
            print(f"        [!] Error: {type(e).__name__}")
    
    # Tertiary: Scan StreamingAssets
    streaming_dir = data_dir / "StreamingAssets"
    if streaming_dir.exists():
        print("[*] Scanning StreamingAssets...")
        try:
            asset_files = list(streaming_dir.rglob("*.asset")) + list(streaming_dir.rglob("*.unity3d"))
            print(f"    Found {len(asset_files)} asset files")
            for asset_file in asset_files[:50]:  # Limit to first 50
                try:
                    with open(asset_file, 'rb') as f:
                        env = Environment(f)
                        for container in env.container.values():
                            for obj in container.objects.values():
                                extract_text_from_asset(obj, strings)
                except:
                    pass
        except Exception as e:
            print(f"    [!] Error scanning StreamingAssets: {e}")
    
    # Write output
    print(f"[*] Writing {len(strings)} unique strings...")
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Extracted Black Book Strings\n")
        f.write(f"# Extraction date: {__import__('datetime').datetime.now().isoformat()}\n")
        f.write("# Format: key=English value\n")
        f.write("# Use these as the base for SC→TC conversion\n\n")
        
        for key in sorted(strings.keys()):
            for value in sorted(set(str(v) for v in strings[key] if v)):
                value_escaped = value.replace('\n', '\\n').replace('\r', '\\r')
                f.write(f"{key}={value_escaped}\n")
    
    print(f"[✓] Extraction complete!")
    print(f"    Total unique strings: {len(strings)}")
    print(f"    Files scanned: {file_count}")
    print(f"    Output: {output_file}")
    print(f"\nNext step:")
    print(f"  1. Verify extracted strings: cat {output_file} | head -20")
    print(f"  2. Convert to TC: python3 convert_sc_to_tc.py")


def main():
    parser = argparse.ArgumentParser(
        description=f"Extract localizable strings from {GAME_NAME}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect and extract:
  python3 extract_game_strings.py
  
  # Use custom game path:
  python3 extract_game_strings.py --game-path /mnt/d/SteamLibrary/steamapps/common/Black\\ Book
  
  # Specify output file:
  python3 extract_game_strings.py --output /tmp/strings.txt
        """
    )
    parser.add_argument(
        "--game-path",
        help="Path to Black Book game directory (auto-detected if omitted)"
    )
    parser.add_argument(
        "--output",
        default=str(SCRIPT_DIR / "payload" / "Black Book_Data" / "resources" / "strings_extracted.txt"),
        help="Output file for extracted strings"
    )
    
    args = parser.parse_args()
    
    try:
        game_dir = find_game_directory(args.game_path)
        scan_assets(game_dir, Path(args.output))
    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR = Path(__file__).parent.parent
GAME_DEFAULT_PATHS = [
    Path.cwd() / "Black Book.exe",  # Current directory
    Path("/mnt/c/Program Files (x86)/Steam/steamapps/common/Black Book/Black Book.exe"),
    Path("/mnt/d/SteamLibrary/steamapps/common/Black Book/Black Book.exe"),
]

# Assets to scan
ASSET_TARGETS = [
    "resources.resource",
    "sharedassets*.resource",
    "StreamingAssets/*",
]


# ============================================================================
# Extraction Logic
# ============================================================================

def find_game_directory(optional_path=None):
    """
    Locate Black Book game directory.
    
    Args:
        optional_path: User-provided path override
        
    Returns:
        Path to game directory
        
    Raises:
        FileNotFoundError: If game directory not found
    """
    if optional_path:
        game_dir = Path(optional_path).parent
        if game_dir.exists():
            return game_dir
        raise FileNotFoundError(f"Path not found: {optional_path}")
    
    for path in GAME_DEFAULT_PATHS:
        if path.exists():
            return path.parent
    
    raise FileNotFoundError("Black Book game directory not found. Specify with --game-path.")


def extract_text_from_asset(obj, strings_dict):
    """
    Recursively extract text strings from Unity objects.
    
    Args:
        obj: Unity object (TextMeshPro, Text, etc.)
        strings_dict: Dictionary to accumulate extracted strings
    """
    # Skip non-serializable types
    if not hasattr(obj, '__dict__'):
        return
    
    obj_type = obj.__class__.__name__
    
    # Extract from known text components
    if obj_type in ('Text', 'TextMeshPro', 'TextMeshProUGUI'):
        if hasattr(obj, 'm_Text') and obj.m_Text:
            scope = 'ui_text'
            key = f"text_{id(obj) % 10000}"
            strings_dict[f"{scope}_{key}"] = obj.m_Text
    
    # Extract from generic localizable components
    if hasattr(obj, 'text') and isinstance(getattr(obj, 'text', None), str):
        scope = f"generic_{obj_type}"
        key = f"text_{id(obj) % 10000}"
        text_val = obj.text
        if text_val and len(text_val) > 0:
            strings_dict[f"{scope}_{key}"] = text_val


def scan_assets(game_dir, output_file):
    """
    Scan and extract strings from all Black Book assets.
    
    Args:
        game_dir: Path to Black Book game directory
        output_file: Output file path for extracted strings
    """
    data_dir = game_dir / "Black Book_Data"
    
    if not data_dir.exists():
        raise FileNotFoundError(f"Game data directory not found: {data_dir}")
    
    print(f"[*] Scanning game assets in: {data_dir}")
    
    strings = defaultdict(list)
    file_count = 0
    
    # Scan resource files
    for resource_file in data_dir.glob("*.resource"):
        print(f"[*] Scanning: {resource_file.name}")
        
        try:
            with open(resource_file, 'rb') as f:
                env = Environment.load_file(resource_file)
                for container in env.container.values():
                    for obj in container.objects.values():
                        extract_text_from_asset(obj, strings)
                file_count += 1
        except Exception as e:
            print(f"    [!] Error scanning {resource_file.name}: {e}")
    
    # Scan streaming assets
    streaming_dir = data_dir / "StreamingAssets"
    if streaming_dir.exists():
        print(f"[*] Scanning StreamingAssets...")
        try:
            for asset_file in streaming_dir.rglob("*.asset"):
                print(f"    Checking: {asset_file.name}")
                try:
                    env = Environment.load_file(asset_file)
                    for container in env.container.values():
                        for obj in container.objects.values():
                            extract_text_from_asset(obj, strings)
                except:
                    pass  # Skip files that can't be parsed
        except Exception as e:
            print(f"    [!] Error scanning StreamingAssets: {e}")
    
    # Write extracted strings
    print(f"[*] Writing {len(strings)} unique strings to: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Extracted Black Book Strings\n")
        f.write(f"# Extracted from {file_count} resource files\n")
        f.write("# Format: key=value\n\n")
        
        for key in sorted(strings.keys()):
            for value in sorted(set(strings[key])):
                # Escape newlines
                value_escaped = value.replace('\n', '\\n').replace('\r', '\\r')
                f.write(f"{key}={value_escaped}\n")
    
    print(f"[✓] Extraction complete")
    print(f"    Total unique strings: {len(strings)}")
    print(f"    Output: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract localizable strings from Black Book using UnityPy"
    )
    parser.add_argument(
        "--game-path",
        help="Path to Black Book executable (auto-detected if omitted)"
    )
    parser.add_argument(
        "--output",
        default=str(SCRIPT_DIR / "payload" / "Black Book_Data" / "resources" / "strings_extracted.txt"),
        help="Output file for extracted strings"
    )
    
    args = parser.parse_args()
    
    try:
        game_dir = find_game_directory(args.game_path)
        print(f"[*] Found game directory: {game_dir}")
        scan_assets(game_dir, Path(args.output))
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
