# ---------------------------------------------------------------------------
# Easy Reinforcement - DoW DE standalone mod - build (Windows PowerShell)
# ---------------------------------------------------------------------------
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

& make -s build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Done."