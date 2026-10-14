<#
.SYNOPSIS
  Black Book — Traditional Chinese Localization Mod uninstaller (Windows).

.DESCRIPTION
  Restores the game's own Simplified Chinese config_zh.yaml files. No backup is
  required: source\sc\ contains them byte-for-byte, which is also the input the
  build converts from.

.EXAMPLE
  .\uninstall.ps1
.EXAMPLE
  .\uninstall.ps1 -GamePath 'D:\SteamLibrary\steamapps\common\Black Book'
#>
[CmdletBinding()]
param(
  [string]$GamePath = $env:GAME_PATH,
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$SourceDir  = Join-Path $ScriptDir 'source\sc\StreamingAssets\Config'

$SteamRoots = @(
  "$env:ProgramFiles(x86)\Steam",
  "$env:ProgramFiles\Steam",
  'C:\Program Files (x86)\Steam',
  'D:\SteamLibrary',
  'E:\SteamLibrary',
  'G:\SteamLibrary'
) | Where-Object { $_ -and (Test-Path $_) }

function Write-Log([string]$Message) {
  Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
}

function Get-BlackBookPath {
  param([string]$Explicit)

  if ($Explicit) {
    if (-not (Test-Path (Join-Path $Explicit 'Black Book_Data'))) {
      throw "Not a Black Book folder: $Explicit"
    }
    return $Explicit
  }

  foreach ($root in $SteamRoots) {
    foreach ($candidate in @(
        (Join-Path $root 'steamapps\common\Black Book'),
        (Join-Path $root 'steamapps\common\black-book'))) {
      if (Test-Path (Join-Path $candidate 'Black Book.exe')) { return $candidate }
    }
  }
  throw 'Black Book not found. Pass -GamePath or set the GAME_PATH environment variable.'
}

function Invoke-Copy {
  param([string]$Source, [string]$Destination)
  if ($DryRun) { Write-Host "      DRY-RUN: $Source -> $Destination" }
  else { Copy-Item -LiteralPath $Source -Destination $Destination -Force }
}

Write-Log 'Black Book — Traditional Chinese Localization uninstaller'
if ($DryRun) { Write-Log '(dry run: nothing will be written)' }

if (-not (Test-Path $SourceDir)) {
  throw "Restoration source not found: $SourceDir. Run 'git checkout source/sc' to restore it, or verify the game files through Steam (Properties -> Installed Files -> Verify integrity of game files)."
}

$game = Get-BlackBookPath -Explicit $GamePath
Write-Log "Game directory: $game"

$configDir = Join-Path $game 'Black Book_Data\StreamingAssets\Config'
if (-not (Test-Path $configDir)) {
  throw "Game config directory not found: $configDir"
}

$files = Get-ChildItem -LiteralPath $SourceDir -Recurse -Filter 'config_zh.yaml'
if ($files.Count -eq 0) { throw "Restoration source is empty: $SourceDir" }
Write-Log "Restoring $($files.Count) Simplified Chinese config file(s)..."

foreach ($file in $files) {
  $relative = $file.FullName.Substring($SourceDir.Length).TrimStart('\', '/')
  $destination = Join-Path $configDir $relative
  $parent = Split-Path -Parent $destination
  if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
  Invoke-Copy -Source $file.FullName -Destination $destination
}
Write-Log '  [ok] StreamingAssets\Config restored to the original Simplified Chinese'

# Remove the empty scratch folder an older version of this mod created.
$stray = Join-Path $game 'Black Book_Data\resources'
if (Test-Path -LiteralPath $stray) {
  if (-not (Get-ChildItem -LiteralPath $stray -Force)) {
    if ($DryRun) { Write-Host "      DRY-RUN: remove $stray" }
    else { Remove-Item -LiteralPath $stray -Force; Write-Log '  [ok] removed stray empty resources\ folder' }
  }
}

Write-Host ''
Write-Host '=========================================='
Write-Host 'Uninstall complete'
Write-Host '=========================================='
Write-Host ''
Write-Host "The game's own Simplified Chinese localisation is back in place."
Write-Host ''
Write-Host 'If anything still looks wrong, verify the install through Steam:'
Write-Host '  right-click Black Book -> Properties -> Installed Files ->'
Write-Host '  Verify integrity of game files'