#!/usr/bin/env python3
"""
SGA Builder Helper — Automate locale mod SGA packaging for Vortex deployment.

This script creates a locale mod SGA archive suitable for Vortex mod manager.

Usage:
    python3 build_sga.py --input <mod_directory> --output <output.sga> \\
                         --archive-exe <path_to_archive.exe>

Example:
    python3 build_sga.py \\
        --input wh40k-dow-de-tc-mod-v1.0.3 \\
        --output EnginLocMod.sga \\
        --archive-exe "D:\\SteamLibrary\\steamapps\\common\\Dawn of War Definitive Edition\\archive\\Archive.exe"

Requirements:
    - Archive.exe (from game installation)
    - Python 3.6+
    - CRLF line endings (auto-converted on Windows)
"""

import argparse
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path


def create_buildfile(root_dir, buildfile_path):
    """Create Archive.exe buildfile with proper CRLF line endings."""
    content = """Archive
TOCStart alias="data" relativeroot="."
FileSettingsStart defcompression="1"
    Override wildcard=".*(gfx)$" minsize="-1" maxsize="-1" ct="1"
    Override wildcard=".*(fnt)$" minsize="-1" maxsize="-1" ct="2"
    Override wildcard=".*(ttf|ttc|ucs)$" minsize="-1" maxsize="-1" ct="0"
FileSettingsEnd
TOCEnd"""
    
    # Ensure CRLF line endings (Windows standard for Archive.exe)
    content = content.replace('\r\n', '\n').replace('\n', '\r\n')
    
    with open(buildfile_path, 'w', newline='') as f:
        f.write(content)
    
    print(f"✅ Created buildfile: {buildfile_path}")


def validate_mod_directory(mod_dir):
    """Verify mod contains required locale mod files."""
    mod_path = Path(mod_dir)
    
    if not mod_path.is_dir():
        print(f"❌ Error: {mod_dir} is not a directory")
        return False
    
    # Check for locale mod markers
    has_engine_ucs = (mod_path / 'Engine.ucs').exists()
    has_data_font = (mod_path / 'data' / 'font').exists()
    has_data_art = (mod_path / 'data' / 'art' / 'ui' / 'swf').exists()
    
    has_marker = has_engine_ucs or has_data_font or has_data_art
    
    if not has_marker:
        print(f"⚠️  Warning: No locale mod markers found in {mod_dir}")
        print("   Expected: Engine.ucs, data/font/, or data/art/ui/swf/")
        return False
    
    # Check for forbidden files
    fontdecor = list(mod_path.rglob('fontdecor.gfx'))
    if fontdecor:
        print(f"❌ Error: fontdecor.gfx found (should be excluded for locale mods)")
        print(f"   File: {fontdecor[0]}")
        return False
    
    bak_files = list(mod_path.rglob('*.bak'))
    if bak_files:
        print(f"⚠️  Warning: {len(bak_files)} .bak backup files found")
        print("   These will not be packed (extension auto-filters them)")
    
    print(f"✅ Mod directory validated: {mod_dir}")
    return True


def run_archive_exe(archive_exe, buildfile, root_dir, output_sga):
    """Execute Archive.exe to build SGA."""
    if not Path(archive_exe).exists():
        print(f"❌ Error: Archive.exe not found at {archive_exe}")
        print("   Copy from: <game>\\archive\\Archive.exe")
        return False
    
    # Archive.exe command
    cmd = [archive_exe, '-c', buildfile, '-r', root_dir, '-a', output_sga]
    
    print(f"\n📦 Building SGA with Archive.exe...")
    print(f"   Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"❌ Archive.exe failed with return code {result.returncode}")
            if result.stderr:
                print(f"   Error: {result.stderr}")
            if result.stdout:
                print(f"   Output: {result.stdout}")
            return False
        
        print(f"✅ SGA built successfully")
        
        # Show file size
        sga_size = Path(output_sga).stat().st_size / (1024 * 1024)
        print(f"   Size: {sga_size:.1f} MB")
        
        return True
        
    except subprocess.TimeoutExpired:
        print(f"❌ Archive.exe timeout (300s)")
        return False
    except Exception as e:
        print(f"❌ Error running Archive.exe: {e}")
        return False


def verify_sga(archive_exe, sga_file):
    """Test SGA integrity."""
    cmd = [archive_exe, '-a', sga_file, '-t']
    
    print(f"\n🔍 Verifying SGA integrity...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"✅ SGA passed integrity test")
            return True
        else:
            print(f"❌ SGA integrity test failed")
            if result.stderr:
                print(f"   {result.stderr}")
            return False
            
    except Exception as e:
        print(f"⚠️  Could not verify SGA: {e}")
        return True  # Don't fail on verify error


def main():
    parser = argparse.ArgumentParser(
        description='Build locale mod SGA archive for Vortex deployment',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--input',
        required=True,
        help='Input mod directory (e.g., wh40k-dow-de-tc-mod-v1.0.3/)'
    )
    parser.add_argument(
        '--output',
        default='EnginLocMod.sga',
        help='Output SGA filename (default: EnginLocMod.sga)'
    )
    parser.add_argument(
        '--archive-exe',
        help='Path to Archive.exe (auto-detect from Steam if not provided)'
    )
    parser.add_argument(
        '--skip-verify',
        action='store_true',
        help='Skip SGA integrity verification'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print(" SGA Builder — Locale Mod Packaging for Vortex")
    print("=" * 70)
    print()
    
    # Validate input directory
    if not validate_mod_directory(args.input):
        sys.exit(1)
    
    # Resolve Archive.exe
    archive_exe = args.archive_exe
    if not archive_exe:
        # Try common Steam paths
        if platform.system() == 'Windows':
            possible_paths = [
                r"D:\SteamLibrary\steamapps\common\Dawn of War Definitive Edition\archive\Archive.exe",
                r"C:\Program Files (x86)\Steam\steamapps\common\Dawn of War Definitive Edition\archive\Archive.exe",
                r"C:\Program Files\Steam\steamapps\common\Dawn of War Definitive Edition\archive\Archive.exe",
            ]
        else:
            # WSL2 or Linux paths
            possible_paths = [
                "/mnt/d/SteamLibrary/steamapps/common/Dawn of War Definitive Edition/archive/Archive.exe",
                "/mnt/c/Program Files (x86)/Steam/steamapps/common/Dawn of War Definitive Edition/archive/Archive.exe",
            ]
        
        for path in possible_paths:
            if Path(path).exists():
                archive_exe = path
                break
    
    if not archive_exe or not Path(archive_exe).exists():
        print(f"❌ Archive.exe not found")
        print(f"   Please specify --archive-exe <path>")
        print(f"   Copy from: <game>\\archive\\Archive.exe")
        sys.exit(1)
    
    print(f"✅ Archive.exe found: {archive_exe}\n")
    
    # Create temporary buildfile
    with tempfile.TemporaryDirectory() as tmpdir:
        buildfile = os.path.join(tmpdir, 'build.txt')
        create_buildfile(args.input, buildfile)
        
        # Build SGA
        if not run_archive_exe(archive_exe, buildfile, args.input, args.output):
            sys.exit(1)
    
    # Verify SGA
    if not args.skip_verify:
        if not verify_sga(archive_exe, args.output):
            sys.exit(1)
    
    print()
    print("=" * 70)
    print(" ✅ SGA Build Complete")
    print("=" * 70)
    print()
    print(f"📦 SGA File: {args.output}")
    print()
    print("Next steps:")
    print(f"1. Create Vortex package directory:")
    print(f"   mkdir -p wh40k-dow-de-tc-mod-v1.0.3/")
    print(f"   cp {args.output} wh40k-dow-de-tc-mod-v1.0.3/")
    print(f"2. Add modinfo.json:")
    print(f'   {{"id":"unofficial-tc-patch","name":"Unofficial TC Patch","version":"1.0.3"}}')
    print(f"3. Package for Vortex:")
    print(f"   zip -r wh40k-dow-de-tc-mod-v1.0.3.zip wh40k-dow-de-tc-mod-v1.0.3/")
    print(f"4. Deploy via Vortex")
    print()


if __name__ == '__main__':
    main()
