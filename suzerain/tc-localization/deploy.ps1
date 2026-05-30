<#
.SYNOPSIS
    Suzerain zh-TW localisation deployer (Windows).

.DESCRIPTION
    Replaces the EntityTextAssets bundle in the game's Addressables folder with
    the patched (translated) bundle from .\build\. Backs up the original bundle
    to .\backup\<stamp>\ before overwriting so uninstall.ps1 can restore it.

    Build the patched bundle first (on a dev machine):  make build
    The .bundle is platform-agnostic, so you can build on WSL2 and deploy here.

.PARAMETER GameDir
    Override auto-detected Suzerain install.

.PARAMETER Bundle
    Patched bundle to deploy (default: .\build\<bundle>).

.PARAMETER DryRun
    Show actions without writing.

.PARAMETER NoBackup
    Skip backup (not recommended).

.EXAMPLE
    .\deploy.ps1
    .\deploy.ps1 -GameDir "D:\SteamLibrary\steamapps\common\Suzerain"
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$GameDir = '',
    [string]$Bundle  = '',
    [switch]$DryRun,
    [switch]$NoBackup
)

$ErrorActionPreference = 'Stop'
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$GameFolderName = 'Suzerain'
$AaRel = 'Suzerain_Data\StreamingAssets\aa\StandaloneWindows64'
$BundleName = 'defaultlocalgroup_assets_assets_database_entitytextassets.asset_7658ed792f0c4924d06b11829a6c36d1.bundle'
$SceneGlob = 'scenes_scenes_assets_scenes_*.bundle'

function Write-Step { param($m) Write-Host "> $m"  -ForegroundColor Cyan }
function Write-Ok   { param($m) Write-Host "OK $m" -ForegroundColor Green }
function Write-Warn { param($m) Write-Host "!! $m" -ForegroundColor Yellow }
function Die        { param($m) Write-Host "XX $m" -ForegroundColor Red; exit 1 }

if (-not $Bundle) { $Bundle = Join-Path $ScriptRoot "build\$BundleName" }

# -- Steam library discovery --------------------------------------------------
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
    Die "Could not auto-detect '$GameFolderName'. Use -GameDir."
}

$GameDir = Find-Game
Write-Ok "Game: $GameDir"

$TargetDir    = Join-Path $GameDir $AaRel
$TargetBundle = Join-Path $TargetDir $BundleName
if (-not (Test-Path $TargetDir))    { Die "Addressables dir missing: $TargetDir" }
if (-not (Test-Path $TargetBundle)) { Die "Original bundle not found: $TargetBundle" }
$SceneBundles = @(Get-ChildItem -Path (Join-Path $ScriptRoot "build") -Filter $SceneGlob -File -ErrorAction SilentlyContinue)

if (-not (Test-Path $Bundle)) {
    Die "Patched bundle missing: $Bundle`nBuild it on a dev machine with 'make build', then copy build\$BundleName here."
}
if ($SceneBundles.Count -eq 0) {
    Die "Patched scene bundles missing under $(Join-Path $ScriptRoot 'build'). Run 'make build' first."
}

# -- Backup -------------------------------------------------------------------
if (-not $NoBackup) {
    $Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $BackupDir = Join-Path $ScriptRoot "backup\$Stamp"
    if ($DryRun) {
        Write-Step "[dry-run] would backup original -> $BackupDir\$BundleName"
        foreach ($scene in Get-ChildItem -Path $TargetDir -Filter $SceneGlob -File -ErrorAction SilentlyContinue) {
            Write-Step "[dry-run] would backup original -> $(Join-Path $BackupDir $scene.Name)"
        }
    } else {
        New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
        Copy-Item $TargetBundle (Join-Path $BackupDir $BundleName)
        foreach ($scene in Get-ChildItem -Path $TargetDir -Filter $SceneGlob -File -ErrorAction SilentlyContinue) {
            Copy-Item $scene.FullName (Join-Path $BackupDir $scene.Name)
        }
        Set-Content -Path (Join-Path $BackupDir 'origin-dir.txt') -Value $TargetDir
        Write-Ok "Backup -> $BackupDir\$BundleName"
    }
}

# -- Deploy -------------------------------------------------------------------
if ($DryRun) {
    Write-Step "[dry-run] cp $Bundle -> $TargetBundle"
    foreach ($scene in $SceneBundles) {
        Write-Step "[dry-run] cp $($scene.FullName) -> $(Join-Path $TargetDir $scene.Name)"
    }
} else {
    Copy-Item $Bundle $TargetBundle -Force
    foreach ($scene in $SceneBundles) {
        Copy-Item $scene.FullName (Join-Path $TargetDir $scene.Name) -Force
    }
    Write-Ok "Deployed patched bundle -> $TargetBundle"
    Write-Ok "Deployed patched scene bundles -> $(Join-Path $TargetDir $SceneGlob)"
}

Write-Ok "Done. Launch Suzerain and verify the Traditional Chinese text."
Write-Warn "If text appears blank/garbled or reverts to English, the Addressables"
Write-Warn "catalogue may verify bundle CRC. Run uninstall.ps1 to restore, and report it."
