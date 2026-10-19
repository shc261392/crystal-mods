# PowerShell Rebuild Command for Windows
# Run this in Windows PowerShell (not WSL) to rebuild the SGA with the fontdecor.gfx fix

# Quick one-liner (if already in the repo directory):
cd D:\Users\shado\crystal-mods\dawn-of-war-de\unofficial-tc-patch  # Adjust path
.\scripts\repack_sga_windows.ps1

# OR use the automated script:
cd D:\Users\shado\crystal-mods\dawn-of-war-de\unofficial-tc-patch
.\scripts\rebuild_sga_with_font_sizes.sh --size 36

# OR manual rebuild with Archive.exe:
cd D:\Users\shado\crystal-mods\dawn-of-war-de\unofficial-tc-patch

# Set game directory
$GAME_DIR = "D:\SteamLibrary\steamapps\common\Dawn of War Definitive Edition"
$ARCHIVE_EXE = "$GAME_DIR\Archive.exe"

# Build the SGA
& $ARCHIVE_EXE -c ".copilot_workspace\EnginLocBuild.txt" `
  -r "data" `
  -a "EnginLocMod.sga" `
  -v

# Expected result:
# EnginLocMod.sga created (~198MB with vanilla fontdecor.gfx)
