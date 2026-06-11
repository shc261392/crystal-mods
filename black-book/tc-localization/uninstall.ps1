# Black Book — Traditional Chinese Localization Mod
# Uninstall script for Windows (PowerShell)
#
# Purpose:
#   Removes deployed TC localization asset files and optionally restores from backup
#
# Usage:
#   .\uninstall.ps1 [-NoRestore] [-Force]
#
# Requires: PowerShell 5.0+

#Requires -Version 5.0

param(
  [switch]$NoRestore,
  [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ============================================================================
# Configuration
# ============================================================================

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ModDir = $ScriptDir
$SteamAppId = '1138660'
$GameDir = $null
$BackupDir = Join-Path $ModDir 'backup'
$RestoreBackup = -not $NoRestore

# ============================================================================
# Utility Functions
# ============================================================================

function Write-Log {
  param([string]$Message)
  $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
  Write-Host "[$timestamp] $Message"
}

function Write-Error-Custom {
  param([string]$Message)
  Write-Host "[ERROR] $Message" -ForegroundColor Red
  exit 1
}

function Write-Warn {
  param([string]$Message)
  Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

# ============================================================================
# Steam Detection
# ============================================================================

function Find-SteamInstallPath {
  Write-Log 'Locating Steam installation...'
  
  $steamPaths = @(
    'HKCU:\Software\Valve\Steam',
    'HKLM:\Software\Valve\Steam',
    'HKLM:\Software\Wow6432Node\Valve\Steam'
  )
  
  foreach ($regPath in $steamPaths) {
    try {
      if (Test-Path $regPath) {
        $installPath = (Get-ItemProperty $regPath -ErrorAction SilentlyContinue).InstallPath
        if ($installPath -and (Test-Path $installPath)) {
          return $installPath
        }
      }
    }
    catch {}
  }
  
  Write-Error-Custom 'Steam installation not found'
}

function Find-GameInSteam {
  param([string]$SteamRoot)
  
  $possiblePaths = @(
    (Join-Path $SteamRoot 'steamapps' 'common' 'Black Book'),
    (Join-Path $SteamRoot 'steamapps' 'common' 'black-book')
  )
  
  foreach ($path in $possiblePaths) {
    if (Test-Path (Join-Path $path 'Black Book.exe')) {
      return $path
    }
  }
  
  return $null
}

function Locate-Game {
  Write-Log 'Locating Black Book...'
  
  $steamInstall = Find-SteamInstallPath
  
  $gamePath = Find-GameInSteam $steamInstall
  if ($gamePath) {
    Write-Log "Found game at: $gamePath"
    return $gamePath
  }
  
  Write-Error-Custom 'Black Book not found in Steam library'
}

# ============================================================================
# Uninstall
# ============================================================================

function Remove-DeployedFiles {
  param([string]$GamePath)
  
  Write-Log 'Removing deployed localization files...'
  
  $resourcesPath = Join-Path $GamePath 'Black Book_Data' 'resources'
  if (Test-Path $resourcesPath) {
    # Only remove TC asset files
    Get-ChildItem $resourcesPath -Filter '*zh-TW*' -File | Remove-Item -Force
    Get-ChildItem $resourcesPath -Filter '*TC*' -File | Remove-Item -Force
    Write-Log '  ✓ Removed TC localization assets'
  }
  
  # Remove fonts if deployed
  $fontsPath = Join-Path $GamePath 'Fonts'
  if (Test-Path $fontsPath) {
    $fontFile = Join-Path $fontsPath 'NotoSansTC.asset'
    if (Test-Path $fontFile) {
      Remove-Item $fontFile -Force | Out-Null
      Write-Log '  ✓ Removed NotoSansTC font asset'
    }
  }
  
  Write-Log '✓ Deployed files removed'
}

function Restore-FromBackup {
  param([string]$GamePath)
  
  if (-not $RestoreBackup) {
    Write-Log 'Skipping backup restoration (-NoRestore)'
    return
  }
  
  if (-not (Test-Path $BackupDir) -or @(Get-ChildItem $BackupDir -ErrorAction SilentlyContinue).Count -eq 0) {
    Write-Log 'No backup found; skipping restoration'
    return
  }
  
  $latestBackup = Get-ChildItem $BackupDir -Filter 'game_backup_*' -Directory | 
                  Sort-Object -Property Name -Descending | 
                  Select-Object -First 1
  
  if (-not $latestBackup) {
    Write-Log 'No valid backup found; skipping restoration'
    return
  }
  
  Write-Log "Restoring from backup: $($latestBackup.FullName)"
  
  $resourcesBak = Join-Path $latestBackup 'resources_original'
  if (Test-Path $resourcesBak) {
    $resourcesDest = Join-Path $GamePath 'Black Book_Data' 'resources'
    if (Test-Path $resourcesDest) {
      Remove-Item $resourcesDest -Recurse -Force | Out-Null
    }
    Copy-Item $resourcesBak $resourcesDest -Recurse -Force | Out-Null
    Write-Log '  ✓ Resources restored'
  }
  
  Write-Log '✓ Restoration complete'
}

# ============================================================================
# Main
# ============================================================================

Write-Log 'Black Book — Traditional Chinese Localization Uninstaller'
Write-Host ''

# Locate game
$GameDir = Locate-Game

# Uninstall
Remove-DeployedFiles $GameDir
Restore-FromBackup $GameDir

Write-Host ''
Write-Host '==========================================' -ForegroundColor Green
Write-Host 'Uninstall complete!' -ForegroundColor Green
Write-Host '==========================================' -ForegroundColor Green
Write-Host ''
Write-Host 'Black Book has been restored to its original state.'
Write-Host ''
