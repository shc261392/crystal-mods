<#
.SYNOPSIS
  Restores the most recent backup created by deploy.ps1 (Windows / PowerShell).
  If you installed via Vortex, purge/remove the mod instead (auto-restore).
.EXAMPLE
  pwsh uninstall.ps1
  pwsh uninstall.ps1 -Stamp 20260711-120000
#>
[CmdletBinding()]
param(
  [string]$GameDir = "",
  [string]$Stamp = ""
)
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackupDir = Join-Path $RepoRoot "backup"
$GameFolder = "Warhammer 40K Battlesector"
$DataSub = "Warhammer 40K Battlesector_Data\StreamingAssets"

if (-not $GameDir) {
  foreach ($c in @(
    "C:\Program Files (x86)\Steam\steamapps\common\$GameFolder",
    "D:\SteamLibrary\steamapps\common\$GameFolder",
    "C:\SteamLibrary\steamapps\common\$GameFolder")) {
    if (Test-Path $c) { $GameDir = $c; break }
  }
}
if (-not $GameDir -or -not (Test-Path $GameDir)) { throw "Game directory not found. Use -GameDir PATH." }

if (-not $Stamp) {
  $Stamp = (Get-ChildItem $BackupDir -Directory -ErrorAction SilentlyContinue |
            Sort-Object Name | Select-Object -Last 1).Name
}
if (-not $Stamp -or -not (Test-Path (Join-Path $BackupDir $Stamp))) { throw "No backup found in $BackupDir." }
Write-Host "Restoring backup: $Stamp" -ForegroundColor Green

# Restore every bundle that was backed up in this stamp.
$DeployFiles = @(Get-ChildItem (Join-Path $BackupDir $Stamp) -Filter *.bundle | ForEach-Object { $_.Name })

foreach ($f in $DeployFiles) {
  $bak = Join-Path $BackupDir "$Stamp\$f"
  if (-not (Test-Path $bak)) { Write-Host "No backup for $f, skipping" -ForegroundColor Yellow; continue }
  Write-Host "Restore $f" -ForegroundColor Cyan
  Copy-Item $bak (Join-Path $GameDir "$DataSub\$f") -Force
}
Write-Host "Vanilla files restored." -ForegroundColor Green
