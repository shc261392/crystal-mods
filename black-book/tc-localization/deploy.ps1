<#
.SYNOPSIS
  Black Book — Traditional Chinese Localization Mod installer (Windows).

.DESCRIPTION
  Copies the mod's TC config_zh.yaml files over the game's Simplified Chinese
  originals. Restoration does NOT need a backup: source\sc\ holds the game's
  own Simplified Chinese files byte-for-byte, and uninstall.ps1 copies them
  back.

.EXAMPLE
  .\deploy.ps1
.EXAMPLE
  .\deploy.ps1 -GamePath 'D:\SteamLibrary\steamapps\common\Black Book'
.EXAMPLE
  .\deploy.ps1 -DryRun
#>
[CmdletBinding()]
param(
  [string]$GamePath = $env:GAME_PATH,
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$PayloadDir = Join-Path $ScriptDir 'payload\Black Book_Data\StreamingAssets\Config'

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

Write-Log 'Black Book — Traditional Chinese Localization installer'
if ($DryRun) { Write-Log '(dry run: nothing will be written)' }

if (-not (Test-Path $PayloadDir)) {
  throw "Payload not found: $PayloadDir - run 'make build' first."
}

$game = Get-BlackBookPath -Explicit $GamePath
Write-Log "Game directory: $game"

$configDir = Join-Path $game 'Black Book_Data\StreamingAssets\Config'
if (-not (Test-Path $configDir)) {
  throw "Game config directory not found: $configDir"
}

$files = Get-ChildItem -LiteralPath $PayloadDir -Recurse -Filter 'config_zh.yaml'
if ($files.Count -eq 0) { throw 'Payload contains no config_zh.yaml files' }
Write-Log "Payload: $($files.Count) Traditional Chinese config file(s)"

Write-Log 'Installing...'
foreach ($file in $files) {
  $relative = $file.FullName.Substring($PayloadDir.Length).TrimStart('\', '/')
  $destination = Join-Path $configDir $relative
  $parent = Split-Path -Parent $destination
  if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
  Invoke-Copy -Source $file.FullName -Destination $destination
}
Write-Log "  [ok] wrote $($files.Count) file(s) into StreamingAssets\Config"

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
Write-Host 'Installation complete'
Write-Host '=========================================='
Write-Host ''
Write-Host 'Launch Black Book from Steam and check:'
Write-Host '  - item names / descriptions in the inventory'
Write-Host '  - ability names'
Write-Host '  - chapter titles in the menu'
Write-Host '  - the credits screen (Settings -> Credits)'
Write-Host ''
Write-Host 'Text that comes from Unity assets rather than config files is NOT'
Write-Host 'covered by this mod. See the "Coverage" section of README.md.'
Write-Host ''
Write-Host 'To uninstall:  .\uninstall.ps1'