# ---------------------------------------------------------------------------
# skip-all-intro - DoW DE skip-all-intro movies mod - build (Windows PowerShell)
#
# Generates the 0-byte replacement movies into mod/ and packages a
# Vortex-installable zip into dist/.
#
# Usage: .\build.ps1 [-Version 0.1.0]
# ---------------------------------------------------------------------------
param(
    [string]$Version = "0.1.0"
)

$ErrorActionPreference = "Stop"
$PKG_NAME = "skip-all-intro-v$Version"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

Write-Host "== skip-all-intro - DoW DE build (Windows) =="
Write-Host "  version: $Version"

# 1. Generate the replacement movies into mod/.
if (Test-Path mod) { Remove-Item -Recurse -Force mod }
& python scripts\generate_movies.py "mod"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# 2. Package the Vortex zip.
if (Test-Path dist) { Remove-Item -Recurse -Force dist }
New-Item -ItemType Directory -Force -Path "dist\$PKG_NAME" | Out-Null
Copy-Item -Recurse -Force "mod\Engine", "mod\DXP2", "mod\DXP3" "dist\$PKG_NAME"
Compress-Archive -Path "dist\$PKG_NAME\*" -DestinationPath "dist\$PKG_NAME.zip" -Force
Write-Host "✓ dist\$PKG_NAME.zip"
