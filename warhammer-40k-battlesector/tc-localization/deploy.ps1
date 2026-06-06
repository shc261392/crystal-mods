<#
.SYNOPSIS
    WH40K Battlesector — Traditional Chinese Localization Deployer (Windows)

.DESCRIPTION
    Deploys the TC localization mod to the game installation on Windows.
    Auto-detects Steam game directory from registry and common library paths.
    Creates a timestamped backup before deploying.

    Actions:
      1. Auto-detect game installation directory
      2. Backup existing sharedassets1.assets
      3. Deploy patched sharedassets1.assets
      4. Verify deployment integrity

.PARAMETER GameDir
    Override the auto-detected game installation directory.

.PARAMETER DryRun
    Show what would be deployed without writing anything.

.PARAMETER NoBackup
    Skip backup step (not recommended).

.EXAMPLE
    .\deploy.ps1
    .\deploy.ps1 -DryRun
    .\deploy.ps1 -GameDir "D:\SteamLibrary\steamapps\common\Warhammer 40K Battlesector"
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$GameDir    = "",
    [switch]$DryRun,
    [switch]$NoBackup
)

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$DataSubPath = "Warhammer 40K Battlesector_Data"
$GameFolderName = "Warhammer 40K Battlesector"
$Stamp = (Get-Date -Format "yyyyMMdd-HHmmss")
$BackupRoot = Join-Path $ScriptRoot "backup"
$DeployFiles = @("sharedassets1.assets")

# ─────────────────────────────────────────────────────────────────────────────
function Write-Step  { param([string]$Msg) Write-Host "▶ $Msg" -ForegroundColor Cyan }
function Write-Ok    { param([string]$Msg) Write-Host "✓ $Msg" -ForegroundColor Green }
function Write-Warn  { param([string]$Msg) Write-Host "⚠ $Msg" -ForegroundColor Yellow }
function Write-Fail  { param([string]$Msg) Write-Error "✗ $Msg" }

# ─────────────────────────────────────────────────────────────────────────────
# Steam library discovery
# ─────────────────────────────────────────────────────────────────────────────
function Get-SteamLibraryRoots {
    $roots = [System.Collections.Generic.List[string]]::new()

    # 1. Registry (Steam install path)
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

    # 2. Common default paths
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

    # 3. Parse libraryfolders.vdf from each found Steam root
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

    # 4. Scan all drive roots for SteamLibrary folders
    $drives = Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Root -match '^[A-Z]:\\$' }
    foreach ($drv in $drives) {
        foreach ($candidate in @("SteamLibrary", "Steam", "Games\Steam")) {
            $path = Join-Path $drv.Root $candidate
            if (Test-Path $path) { $roots.Add($path) | Out-Null }
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

# ─────────────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "WH40K Battlesector — Traditional Chinese Localization Deployer (Windows)" -ForegroundColor White -BackgroundColor DarkBlue
Write-Host "Repo: $ScriptRoot"
Write-Host ""

if ($DryRun) { Write-Warn "[DRY RUN — no files will be written]" }

# 1. Resolve game directory
if ([string]::IsNullOrWhiteSpace($GameDir)) {
    $GameDir = $env:WH40K_BS_GAME_DIR
}
if ([string]::IsNullOrWhiteSpace($GameDir)) {
    Write-Step "Auto-detecting game installation..."
    $GameDir = Find-GameDir
    if ([string]::IsNullOrWhiteSpace($GameDir)) {
        Write-Fail "Could not auto-detect game directory."
        Write-Host "Set WH40K_BS_GAME_DIR environment variable or use -GameDir parameter." -ForegroundColor Red
        Write-Host "Example: -GameDir 'D:\SteamLibrary\steamapps\common\Warhammer 40K Battlesector'"
        exit 1
    }
    Write-Ok "Found: $GameDir"
} else {
    Write-Step "Using game directory: $GameDir"
}

# Verify game directory exists
if (!(Test-Path $GameDir)) {
    Write-Fail "Game directory does not exist: $GameDir"
    exit 1
}

# 2. Verify data directory
$DataDir = Join-Path $GameDir $DataSubPath
if (!(Test-Path $DataDir)) {
    Write-Fail "Game data folder not found: $DataDir"
    exit 1
}
Write-Ok "Game data folder: $DataDir"

# 3. Verify source files exist
Write-Step "Checking deployment files..."
foreach ($f in $DeployFiles) {
    $src = Join-Path $ScriptRoot "dist" $f
    if (!(Test-Path $src)) {
        Write-Fail "Source file not found: $src"
        exit 1
    }
    Write-Ok "Ready: $f"
}

# 4. Create backup
if (!$NoBackup) {
    Write-Step "Creating backup..."
    if (!(Test-Path $BackupRoot)) {
        New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
    }
    foreach ($f in $DeployFiles) {
        $orig = Join-Path $DataDir $f
        if (Test-Path $orig) {
            $backup = Join-Path $BackupRoot "$($f -replace '\.assets$').$Stamp.assets.backup"
            if ($DryRun) {
                Write-Step "[DRY] Would backup: $orig -> $backup"
            } else {
                Copy-Item $orig $backup -Force
                Write-Ok "Backed up: $($f -replace '\.assets$').*"
            }
        }
    }
}

# 5. Deploy files
Write-Step "Deploying files..."
foreach ($f in $DeployFiles) {
    $src = Join-Path $ScriptRoot "dist" $f
    $dst = Join-Path $DataDir $f
    if ($DryRun) {
        Write-Step "[DRY] Would copy: $src -> $dst"
    } else {
        Copy-Item $src $dst -Force
        Write-Ok "Deployed: $f"
    }
}

# 6. Verify
if (!$DryRun) {
    Write-Step "Verifying deployment..."
    foreach ($f in $DeployFiles) {
        $dst = Join-Path $DataDir $f
        if (Test-Path $dst) {
            Write-Ok "Verified: $f"
        } else {
            Write-Fail "Deployment failed: $f not found at $dst"
            exit 1
        }
    }
}

Write-Host ""
if ($DryRun) {
    Write-Host "╭─ DRY RUN COMPLETE ───────────────────────────────────────────╮" -ForegroundColor Green
} else {
    Write-Host "╭─ DEPLOYMENT COMPLETE ────────────────────────────────────────╮" -ForegroundColor Green
}
Write-Host "│                                                                  │"
Write-Host "│ ✓ In-game: Select Chinese (Simplified) for Traditional Chinese   │"
Write-Host "│ ✓ Backup location: $BackupRoot"
Write-Host "│                                                                  │"
Write-Host "╰──────────────────────────────────────────────────────────────────╯"
Write-Host ""
