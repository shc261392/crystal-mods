# ---------------------------------------------------------------------------
# Over 40000 - DoW DE power-cheat mod - build (Windows PowerShell)
#
# Builds the COMPLETE release zip set (both variants) with NO content args:
#   dist\over-40000-v0.1.7.zip                  (resource cheat on)
#   dist\over-40000-v0.1.7-normal-resources.zip (no resource cheat)
#
# Per AGENTS.md hard rule 15, only infrastructure path overrides are accepted;
# content args (squad-scale, resource-cheat) are forbidden for releases.
#
# Usage: .\build.ps1 [-GameDir PATH] [-ExtractRoot PATH]
# ---------------------------------------------------------------------------
param(
    [string]$GameDir = "",
    [string]$ExtractRoot = ""
)

$ErrorActionPreference = "Stop"
$Version = "0.1.7"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

if (-not $ExtractRoot) { $ExtractRoot = Join-Path (Resolve-Path "..\..").Path ".copilot_workspace\extract" }
if (-not $GameDir) { $GameDir = $env:DOW_GAME_DIR }

Write-Host "== Over 40000 - DoW DE build (Windows) =="
Write-Host "  version: $Version   release set: both variants, no content args"

$extractArgs = @("--extract-root", $ExtractRoot)
if ($GameDir) { $extractArgs += @("--game-dir", $GameDir) }

# 1. Ensure the game data is extracted (auto-detect game dir if not given).
& python scripts\ensure_extract.py @extractArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$variants = @(
    @{ Cheat = "on";  Pkg = "over-40000-v$Version" },
    @{ Cheat = "off"; Pkg = "over-40000-v${Version}-normal-resources" }
)
foreach ($v in $variants) {
    Write-Host "== variant: resource-cheat $($v.Cheat) -> $($v.Pkg) =="

    # 2. Regenerate a CLEAN mod tree for this variant.
    if (Test-Path mod) { Remove-Item -Recurse -Force mod }
    & python scripts\generate_mod.py $ExtractRoot "mod" --squad-scale 5 --resource-cheat $v.Cheat --exclude-single-model on --descale-campaign-single on
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    # 3. Package this variant's Vortex zip (only its own artifacts are touched).
    if (Test-Path "dist\$($v.Pkg)") { Remove-Item -Recurse -Force "dist\$($v.Pkg)" }
    if (Test-Path "dist\$($v.Pkg).zip") { Remove-Item -Force "dist\$($v.Pkg).zip" }
    New-Item -ItemType Directory -Force -Path "dist\$($v.Pkg)" | Out-Null
    Copy-Item -Recurse -Force "mod\W40k", "mod\WXP", "mod\DXP2", "mod\DXP3" "dist\$($v.Pkg)"
    & python scripts\package_zip.py "dist\$($v.Pkg)" "dist\$($v.Pkg).zip"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "✓ dist\$($v.Pkg).zip (deterministic packaging)"
}