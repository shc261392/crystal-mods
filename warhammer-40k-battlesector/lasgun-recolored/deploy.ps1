<#
.SYNOPSIS
  Deploys Lasgun Recolored payload bundles into the game's StreamingAssets,
  backing up the originals first. (Windows / PowerShell)

.NOTES
  Run `python build.py ...` first to produce .\payload.

.EXAMPLE
  pwsh deploy.ps1
  pwsh deploy.ps1 -GameDir "D:\SteamLibrary\steamapps\common\Warhammer 40000 Battlesector"
#>
[CmdletBinding()]
param(
  [string]$GameDir = "",
  [switch]$DryRun,
  [switch]$NoBackup
)
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BackupDir = Join-Path $RepoRoot "backup"
$GameFolder = "Warhammer 40K Battlesector"
$DataSub = "Warhammer 40K Battlesector_Data\StreamingAssets"
$PayloadRoot = Join-Path $RepoRoot "payload\Warhammer 40K Battlesector_Data\StreamingAssets"
# Deploy whatever bundles the build produced (colour/FX only, or +stats).
$DeployFiles = @()
if (Test-Path $PayloadRoot) {
  $DeployFiles = @(Get-ChildItem $PayloadRoot -Filter *.bundle | ForEach-Object { $_.Name })
}

if (-not $GameDir) {
  $candidates = @(
    "C:\Program Files (x86)\Steam\steamapps\common\$GameFolder",
    "D:\SteamLibrary\steamapps\common\$GameFolder",
    "C:\SteamLibrary\steamapps\common\$GameFolder"
  )
  foreach ($c in $candidates) { if (Test-Path $c) { $GameDir = $c; break } }
}
if (-not $GameDir -or -not (Test-Path $GameDir)) { throw "Game directory not found. Use -GameDir PATH." }
Write-Host "Game directory: $GameDir" -ForegroundColor Green

$TargetDir = Join-Path $GameDir $DataSub
if (-not (Test-Path $TargetDir)) { throw "StreamingAssets not found at: $TargetDir" }

foreach ($f in $DeployFiles) {
  if (-not (Test-Path (Join-Path $PayloadRoot $f))) {
    throw "Missing payload file: $f (run build.py first)"
  }
}
if ($DeployFiles.Count -eq 0) { throw "No payload bundles found (run build.py first)." }

if (-not $NoBackup) { New-Item -ItemType Directory -Force -Path (Join-Path $BackupDir $Stamp) | Out-Null }
foreach ($f in $DeployFiles) {
  $src = Join-Path $PayloadRoot $f
  $dst = Join-Path $TargetDir $f
  if (-not $NoBackup -and (Test-Path $dst)) {
    Write-Host "Backup $f -> backup\$Stamp\" -ForegroundColor Cyan
    if (-not $DryRun) { Copy-Item $dst (Join-Path $BackupDir "$Stamp\$f") -Force }
  }
  Write-Host "Deploy $f -> $TargetDir" -ForegroundColor Cyan
  if (-not $DryRun) { Copy-Item $src $dst -Force }
}
Write-Host "Done.$(if($DryRun){' (dry-run)'})" -ForegroundColor Green
if (-not $NoBackup) { Write-Host "Originals backed up to: $BackupDir\$Stamp" -ForegroundColor Green }
