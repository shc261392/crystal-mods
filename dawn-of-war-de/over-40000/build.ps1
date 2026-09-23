# ---------------------------------------------------------------------------
# Over 40000 - DoW DE power-cheat mod - build (Windows PowerShell)
#
# Auto-detects the Dawn of War Definitive Edition install (or use -GameDir),
# extracts the game data if needed, regenerates mod/ and builds the
# Vortex-installable zip into dist/.
#
# Usage: .\build.ps1 [-GameDir PATH] [-ExtractRoot PATH] [-SquadScale N] [-ResourceCheat on|off]
# ---------------------------------------------------------------------------
param(
    [string]$GameDir = "",
    [string]$ExtractRoot = "",
    [int]$SquadScale = 5,
    [string]$ResourceCheat = "on"
)

$ErrorActionPreference = "Stop"
$Version = "0.1.7"
if ($ResourceCheat -eq "off") { $PKG_NAME = "over-40000-v${Version}-normal-resources" }
else { $PKG_NAME = "over-40000-v$Version" }
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

if (-not $ExtractRoot) { $ExtractRoot = Join-Path (Resolve-Path "..").Path ".copilot_workspace\extract" }
if (-not $GameDir) { $GameDir = $env:DOW_GAME_DIR }

Write-Host "== Over 40000 - DoW DE build (Windows) =="
Write-Host "  version: $Version   squad-scale: $SquadScale   resource-cheat: $ResourceCheat"

$extractArgs = @("--extract-root", $ExtractRoot)
if ($GameDir) { $extractArgs += @("--game-dir", $GameDir) }

# 1. Ensure the game data is extracted (auto-detect game dir if not given).
& python scripts\ensure_extract.py @extractArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# 2. Regenerate the mod tree.
& python scripts\generate_mod.py $ExtractRoot "mod" --squad-scale $SquadScale --resource-cheat $ResourceCheat --exclude-single-model on --descale-campaign-single on
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# 3. Package the Vortex zip.
if (Test-Path dist) { Remove-Item -Recurse -Force dist }
New-Item -ItemType Directory -Force -Path "dist\$PKG_NAME" | Out-Null
Copy-Item -Recurse -Force "mod\W40k", "mod\WXP", "mod\DXP2", "mod\DXP3" "dist\$PKG_NAME"
Compress-Archive -Path "dist\$PKG_NAME\*" -DestinationPath "dist\$PKG_NAME.zip" -Force
Write-Host "✓ dist\$PKG_NAME.zip"
