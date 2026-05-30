<#
.SYNOPSIS
    Suzerain zh-TW localisation uninstaller (Windows).

.DESCRIPTION
    Restores the original EntityTextAssets bundle from the most recent backup
    created by deploy.ps1. Use -Backup to restore a specific stamped backup.

.PARAMETER GameDir
    Override auto-detected Suzerain install.

.PARAMETER Backup
    Restore a specific backup\<STAMP> (default: most recent).

.PARAMETER DryRun
    Show actions without writing.

.EXAMPLE
    .\uninstall.ps1
    .\uninstall.ps1 -Backup 20260529-143000
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$GameDir = '',
    [string]$Backup  = '',
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$GameFolderName = 'Suzerain'
$AaRel = 'Suzerain_Data\StreamingAssets\aa\StandaloneWindows64'
$BundleName = 'defaultlocalgroup_assets_assets_database_entitytextassets.asset_7658ed792f0c4924d06b11829a6c36d1.bundle'
$SceneGlob = 'scenes_scenes_assets_scenes_*.bundle'

function Write-Step { param($m) Write-Host "> $m"  -ForegroundColor Cyan }
function Write-Ok   { param($m) Write-Host "OK $m" -ForegroundColor Green }
function Die        { param($m) Write-Host "XX $m" -ForegroundColor Red; exit 1 }

# -- Locate backup ------------------------------------------------------------
$BackupRoot = Join-Path $ScriptRoot 'backup'
if (-not (Test-Path $BackupRoot)) { Die "No backups found under $BackupRoot. Nothing to restore." }

if ($Backup) {
    $BackupDir = Join-Path $BackupRoot $Backup
} else {
    $BackupDir = Get-ChildItem -Path $BackupRoot -Directory | Sort-Object Name | Select-Object -Last 1 |
        ForEach-Object { $_.FullName }
}
if (-not $BackupDir -or -not (Test-Path $BackupDir)) { Die "Backup dir not found: $BackupDir" }
$BackupBundle = Join-Path $BackupDir $BundleName
if (-not (Test-Path $BackupBundle)) { Die "Backup bundle missing: $BackupBundle" }
Write-Ok "Backup: $BackupDir"

# -- Determine target (prefer recorded origin, else discover) -----------------
function Get-SteamRoots {
    $roots = New-Object System.Collections.Generic.List[string]
    $regKeys = @(
        'HKLM:\SOFTWARE\WOW6432Node\Valve\Steam',
        'HKLM:\SOFTWARE\Valve\Steam',
        'HKCU:\Software\Valve\Steam'
    )
    foreach ($k in $regKeys) {
        $p = (Get-ItemProperty -Path $k -ErrorAction SilentlyContinue).InstallPath
        if ($p -and (Test-Path $p)) { $roots.Add($p) }
    }
    foreach ($d in 'C','D','E','F','G') {
        foreach ($p in @("${d}:\Program Files (x86)\Steam","${d}:\Steam","${d}:\SteamLibrary")) {
            if (Test-Path $p) { $roots.Add($p) }
        }
    }
    $roots | Select-Object -Unique
}

function Find-Game {
    if ($GameDir) { return $GameDir }
    foreach ($root in Get-SteamRoots) {
        $vdf = Join-Path $root 'steamapps\libraryfolders.vdf'
        $libs = @($root)
        if (Test-Path $vdf) {
            $libs += (Get-Content $vdf -Raw |
                Select-String -Pattern '"path"\s+"([^"]+)"' -AllMatches |
                ForEach-Object { $_.Matches } | ForEach-Object { $_.Groups[1].Value -replace '\\\\','\' })
        }
        foreach ($lib in $libs | Select-Object -Unique) {
            $candidate = Join-Path $lib "steamapps\common\$GameFolderName"
            if (Test-Path $candidate) { return $candidate }
        }
    }
    return ''
}

$OriginDirFile = Join-Path $BackupDir 'origin-dir.txt'
if (-not $GameDir -and (Test-Path $OriginDirFile)) {
    $TargetDir = (Get-Content $OriginDirFile -Raw).Trim()
} else {
    $gd = Find-Game
    if (-not $gd) { Die "Could not determine game dir. Use -GameDir." }
    $TargetDir = Join-Path $gd $AaRel
}
if (-not (Test-Path $TargetDir)) { Die "Target dir missing: $TargetDir" }
$TargetBundle = Join-Path $TargetDir $BundleName

# -- Restore ------------------------------------------------------------------
if ($DryRun) {
    Write-Step "[dry-run] cp $BackupBundle -> $TargetBundle"
    foreach ($scene in Get-ChildItem -Path $BackupDir -Filter $SceneGlob -File -ErrorAction SilentlyContinue) {
        Write-Step "[dry-run] cp $($scene.FullName) -> $(Join-Path $TargetDir $scene.Name)"
    }
} else {
    Copy-Item $BackupBundle $TargetBundle -Force
    foreach ($scene in Get-ChildItem -Path $BackupDir -Filter $SceneGlob -File -ErrorAction SilentlyContinue) {
        Copy-Item $scene.FullName (Join-Path $TargetDir $scene.Name) -Force
    }
    Write-Ok "Restored original bundle -> $TargetBundle"
    Write-Ok "Restored original scene bundles -> $(Join-Path $TargetDir $SceneGlob)"
}

Write-Ok "Done. Suzerain is back to its original (English) text."
