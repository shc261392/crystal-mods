# Black Book — Traditional Chinese Localization Mod
# Deploy script for Windows (PowerShell)
#
# Purpose:
#   1. Auto-detects Black Book in Steam library
#   2. Validates game structure
#   3. Backs up original game assets
#   4. Deploys TC localization asset files to Black Book_Data/resources/
#   5. Deploys Noto Sans TC font asset
#
# Usage:
#   .\deploy.ps1 [-NoBackup] [-Force]
#
# Requires: PowerShell 5.0+

#Requires -Version 5.0

param(
  [switch]$NoBackup,
  [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ============================================================================
# Configuration
# ============================================================================

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ModDir = $ScriptDir
$PayloadDir = Join-Path $ModDir 'payload'
$SteamAppId = '1138660'
$GameDir = $null
$BackupDir = Join-Path $ModDir 'backup'
$CreateBackup = -not $NoBackup

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
# Steam Registry & Path Detection
# ============================================================================

function Find-SteamInstallPath {
  Write-Log 'Locating Steam installation...'
  
  # Common Steam registry paths
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
  
  Write-Error-Custom 'Steam installation not found in registry'
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
  
  # Try Steam registry first
  $steamInstall = Find-SteamInstallPath
  
  # Check main Steam directory
  $gamePath = Find-GameInSteam $steamInstall
  if ($gamePath) {
    Write-Log "Found game at: $gamePath"
    return $gamePath
  }
  
  # Check Steam library folders (libraryfolders.vdf)
  $libFoldersPath = Join-Path $steamInstall 'steamapps' 'libraryfolders.vdf'
  if (Test-Path $libFoldersPath) {
    $content = Get-Content $libFoldersPath -Raw
    # Simple regex to find library paths (basic parsing of VDF format)
    $matches = [regex]::Matches($content, '"path"\s+"([^"]+)"')
    
    foreach ($match in $matches) {
      $libPath = $match.Groups[1].Value
      $gamePath = Find-GameInSteam $libPath
      if ($gamePath) {
        Write-Log "Found game at: $gamePath"
        return $gamePath
      }
    }
  }
  
  Write-Error-Custom 'Black Book not found in Steam library'
}

# ============================================================================
# Validation
# ============================================================================

function Test-GameStructure {
  param([string]$GamePath)
  
  Write-Log 'Validating game structure...'
  
  $exe = Join-Path $GamePath 'Black Book.exe'
  $dataDir = Join-Path $GamePath 'Black Book_Data'
  
  if (-not (Test-Path $exe)) {
    Write-Error-Custom "Game executable not found: $exe"
  }
  
  if (-not (Test-Path $dataDir)) {
    Write-Error-Custom "Game data directory not found: $dataDir"
  }
  
  Write-Log '✓ Game structure valid'
}

function Test-PayloadStructure {
  Write-Log 'Validating mod payload...'
  
  $payloadPath = Join-Path $PayloadDir 'AutoTranslator' 'Translation' 'zh-TW'
  
  if (-not (Test-Path $payloadPath)) {
    Write-Error-Custom "Payload missing: $payloadPath"
  }
  
  Write-Log '✓ Payload structure valid'
}

# ============================================================================
# Backup
# ============================================================================

function Backup-Game {
  param([string]$GamePath)
  
  if (-not $CreateBackup) {
    Write-Log 'Skipping backup (--NoBackup)'
    return
  }
  
  $backupTs = Get-Date -Format 'yyyyMMdd_HHmmss'
  $backupPath = Join-Path $BackupDir "game_backup_$backupTs"
  
  Write-Log "Backing up game assets to: $backupPath"
  New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
  
  $resourcesPath = Join-Path $GamePath 'Black Book_Data' 'resources'
  if (Test-Path $resourcesPath) {
    Copy-Item $resourcesPath (Join-Path $backupPath 'resources_original') -Recurse -Force | Out-Null
  }
  
  Write-Log '✓ Backup complete'
}

# ============================================================================
# Deploy
# ============================================================================

function Deploy-Payload {
  param([string]$GamePath)
  
  Write-Log 'Deploying localization payload...'
  
  # Deploy asset files
  $payloadBlackBookData = Join-Path $PayloadDir 'Black Book_Data'
  if (Test-Path $payloadBlackBookData) {
    $destDir = Join-Path $GamePath 'Black Book_Data'
    New-Item -ItemType Directory -Path $destDir -Force | Out-Null
    Copy-Item (Join-Path $payloadBlackBookData '*') $destDir -Recurse -Force | Out-Null
    Write-Log '  ✓ Black Book_Data/resources deployed'
  }
  
  # Deploy Fonts
  $fontsSrc = Join-Path $PayloadDir 'Fonts'
  if ((Test-Path $fontsSrc) -and @(Get-ChildItem $fontsSrc -ErrorAction SilentlyContinue).Count -gt 0) {
    $fontsDest = Join-Path $GamePath 'Fonts'
    New-Item -ItemType Directory -Path $fontsDest -Force | Out-Null
    Copy-Item (Join-Path $fontsSrc '*') $fontsDest -Recurse -Force | Out-Null
    Write-Log '  ✓ Fonts deployed'
  }
  
  Write-Log '✓ Deployment complete'
}

# ============================================================================
# Post-Deploy
# ============================================================================

function Invoke-PostDeploy {
  param([string]$GamePath)
  
  Write-Log 'Running post-deployment checks...'
  
  $deployedPath = Join-Path $GamePath 'Black Book_Data' 'resources'
  if (Test-Path $deployedPath) {
    $fileCount = @(Get-ChildItem $deployedPath -Recurse -File).Count
    Write-Log "  ✓ $fileCount files deployed to Black Book_Data/resources/"
  }
  
  Write-Log '✓ Post-deployment complete'
  Write-Host ''
  Write-Host '==========================================' -ForegroundColor Green
  Write-Host 'Deployment successful!' -ForegroundColor Green
  Write-Host '==========================================' -ForegroundColor Green
  Write-Host ''
  Write-Host 'Next steps:'
  Write-Host '  1. Launch Black Book from Steam'
  Write-Host '  2. Verify text appears in Traditional Chinese'
  Write-Host '  3. Check for any rendering issues'
  Write-Host ''
  Write-Host 'To uninstall, run: .\uninstall.ps1'
  Write-Host ''
}

# ============================================================================
# Main
# ============================================================================

Write-Log 'Black Book — Traditional Chinese Localization Installer'
Write-Host ''

# Locate game
$GameDir = Locate-Game

# Validate
Test-GameStructure $GameDir
Test-PayloadStructure

# Backup
Backup-Game $GameDir

# Deploy
Deploy-Payload $GameDir

# Post-deploy
Invoke-PostDeploy $GameDir
