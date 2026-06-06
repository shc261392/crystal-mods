<#
.SYNOPSIS
    WH40K Battlesector — Traditional Chinese Localization Uninstaller

.DESCRIPTION
    Restores the original sharedassets1.assets from the most recent backup.

.EXAMPLE
    .\uninstall.ps1
#>
[CmdletBinding(SupportsShouldProcess)]
param()

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackupRoot = Join-Path $ScriptRoot "backup"
$GameFolderName = "Warhammer 40K Battlesector"
$DataSubPath = "Warhammer 40K Battlesector_Data"

function Write-Step  { param([string]$Msg) Write-Host "▶ $Msg" -ForegroundColor Cyan }
function Write-Ok    { param([string]$Msg) Write-Host "✓ $Msg" -ForegroundColor Green }
function Write-Warn  { param([string]$Msg) Write-Host "⚠ $Msg" -ForegroundColor Yellow }
function Write-Fail  { param([string]$Msg) Write-Error "✗ $Msg" }

function Get-SteamLibraryRoots {
    $roots = [System.Collections.Generic.List[string]]::new()

    $regPaths = @(
        "HKLM:\SOFTWARE\Valve\Steam",
        "HKLM:\SOFTWARE\WOW6432Node\Valve\Steam",
        "HKCU:\SOFTWARE\Valve\Steam"
    )
    foreach ($rp in $regPaths) {
        try {
            $steamPath = (Get-ItemProperty -Path $rp -ErrorAction SilentlyContinue).InstallPath
            if ($steamPath -and (Test-Path $steamPath)) {
                $roots.Add($steamPath) | Out-Null
            }
        } catch { }
    }

    $defaults = @(
        "$env:ProgramFiles(x86)\Steam",
        "$env:ProgramFiles\Steam",
        "C:\Steam",
        "D:\Steam",
        "D:\SteamLibrary"
    )
    foreach ($d in $defaults) {
        if (Test-Path $d) { $roots.Add($d) | Out-Null }
    }

    $vdfRoots = @($roots | Where-Object { $_ })
    foreach ($steamRoot in $vdfRoots) {
        $vdf = Join-Path $steamRoot "steamapps\libraryfolders.vdf"
        if (Test-Path $vdf) {
            $content = Get-Content $vdf -Raw -ErrorAction SilentlyContinue
            if ($content) {
                $matches_ = [regex]::Matches($content, '"path"\s+"([^"]+)"')
                foreach ($m in $matches_) {
                    $p = $m.Groups[1].Value -replace '\\\\', '\'
                    if (Test-Path $p) { $roots.Add($p) | Out-Null }
                }
            }
        }
    }

    return $roots | Sort-Object -Unique
}

function Find-GameDir {
    $roots = Get-SteamLibraryRoots
    foreach ($root in $roots) {
        $candidate = Join-Path $root "steamapps\common\$GameFolderName"
        if (Test-Path $candidate) {
            return $candidate
        }
    }
    return $null
}

Write-Host ""
Write-Host "WH40K Battlesector — Traditional Chinese Localization Uninstaller" -ForegroundColor White -BackgroundColor DarkBlue
Write-Host "Repo: $ScriptRoot"
Write-Host ""

# Find backup
Write-Step "Looking for backup..."
$BackupFiles = Get-ChildItem -Path $BackupRoot -Filter "sharedassets1.*.assets.backup" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
if ($BackupFiles.Count -eq 0) {
    Write-Fail "No backup found in $BackupRoot"
    exit 1
}
$BackupFile = $BackupFiles[0].FullName
Write-Ok "Found backup: $(Split-Path -Leaf $BackupFile)"

# Find game directory
Write-Step "Auto-detecting game installation..."
$GameDir = Find-GameDir
if ([string]::IsNullOrWhiteSpace($GameDir)) {
    Write-Fail "Could not auto-detect game directory. Set WH40K_BS_GAME_DIR environment variable."
    exit 1
}
Write-Ok "Found: $GameDir"

# Verify paths
$DataDir = Join-Path $GameDir $DataSubPath
if (!(Test-Path $DataDir)) {
    Write-Fail "Game data folder not found: $DataDir"
    exit 1
}

$CurrentMod = Join-Path $DataDir "sharedassets1.assets"
if (!(Test-Path $CurrentMod)) {
    Write-Warn "No mod file found at: $CurrentMod"
    Write-Fail "Nothing to uninstall"
    exit 1
}

# Restore backup
Write-Step "Restoring original sharedassets1.assets..."
Copy-Item $BackupFile $CurrentMod -Force
Write-Ok "Restored: sharedassets1.assets"

# Verify
if (Test-Path $CurrentMod) {
    Write-Ok "Verified: Original file restored"
} else {
    Write-Fail "Restore failed: $CurrentMod"
    exit 1
}

Write-Host ""
Write-Host "╭─ UNINSTALL COMPLETE ─────────────────────────────────────────╮" -ForegroundColor Green
Write-Host "│                                                                │"
Write-Host "│ ✓ Original sharedassets1.assets restored                       │"
Write-Host "│ ✓ Backup kept at: $BackupRoot"
Write-Host "│                                                                │"
Write-Host "╰──────────────────────────────────────────────────────────────────╯"
Write-Host ""
