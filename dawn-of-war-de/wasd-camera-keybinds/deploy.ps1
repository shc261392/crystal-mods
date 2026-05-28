<#
.SYNOPSIS
    DoW:DE WSAD Camera Keybind deployer (Windows)

.DESCRIPTION
    Installs one of three presets to <game>\Engine\defprofile\:
      vanilla            → keydefaults.lua  (stock DoW:DE Classic)
      wasd-camera        → keydefaults.lua  (replace Classic)
      wasd-camera-ingame → keydefaults_modern.lua  (replace Modern slot)

    Backs up existing files to .\backup\<stamp>\ before overwriting.

.PARAMETER Preset
    vanilla | wasd-camera | wasd-camera-ingame   (default: wasd-camera)

.PARAMETER GameDir
    Override auto-detected game install.

.PARAMETER DryRun
    Show actions without writing.

.PARAMETER NoBackup
    Skip backup (not recommended).

.EXAMPLE
    .\deploy.ps1
    .\deploy.ps1 -Preset wasd-camera-ingame
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [ValidateSet('vanilla','wasd-camera','wasd-camera-ingame')]
    [string]$Preset  = 'wasd-camera',
    [string]$GameDir = '',
    [switch]$DryRun,
    [switch]$NoBackup
)

$ErrorActionPreference = 'Stop'
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$GameFolderName = 'Dawn of War Definitive Edition'

function Write-Step { param($m) Write-Host "▶ $m" -ForegroundColor Cyan }
function Write-Ok   { param($m) Write-Host "✓ $m" -ForegroundColor Green }
function Write-Warn { param($m) Write-Host "⚠ $m" -ForegroundColor Yellow }
function Die        { param($m) Write-Host "✗ $m" -ForegroundColor Red; exit 1 }

# ── Steam library discovery ──────────────────────────────────────────────────
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

$PresetDir = Join-Path $ScriptRoot "presets\$Preset"
if (-not (Test-Path $PresetDir)) { Die "Preset not found: $Preset ($PresetDir)" }

$GameDir   = Find-Game
$TargetDir = Join-Path $GameDir 'Engine\defprofile'
if (-not (Test-Path $TargetDir)) { Die "Target dir missing: $TargetDir" }
Write-Ok "Game: $GameDir"

$SrcFiles = Get-ChildItem -Path (Join-Path $PresetDir 'Engine\defprofile') -Filter '*.lua' -File
if ($SrcFiles.Count -eq 0) { Die "No .lua files under $PresetDir\Engine\defprofile" }
Write-Step "Preset: $Preset ($($SrcFiles.Count) file(s))"
$SrcFiles | ForEach-Object { Write-Host "    - $($_.Name)" }

if (-not $NoBackup) {
    $Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $BackupDir = Join-Path $ScriptRoot "backup\$Stamp"
    if ($DryRun) {
        Write-Step "[dry-run] would backup to $BackupDir"
    } else {
        New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
        foreach ($f in $SrcFiles) {
            $existing = Join-Path $TargetDir $f.Name
            if (Test-Path $existing) { Copy-Item $existing $BackupDir }
        }
        Write-Ok "Backup → $BackupDir"
    }
}

foreach ($f in $SrcFiles) {
    $dest = Join-Path $TargetDir $f.Name
    if ($DryRun) {
        Write-Step "[dry-run] cp $($f.FullName) → $dest"
    } else {
        Copy-Item $f.FullName $dest -Force
        Write-Ok "Deployed $($f.Name)"
    }
}

Write-Ok "Done. Launch the game and verify the WSAD bindings."
if ($Preset -eq 'wasd-camera-ingame') {
    Write-Step "In-game: Options → Hotkeys → Preset → 'Modern Hotkeys' to activate."
}
