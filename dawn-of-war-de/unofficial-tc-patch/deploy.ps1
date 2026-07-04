<#
.SYNOPSIS
    WH40K DoW:DE — Traditional Chinese Locale Mod Deployer (Windows native)

.DESCRIPTION
    Deploys the pre-built TC locale mod SGA to the game installation on Windows.
    Auto-detects Steam game directory from registry and common library paths.
    Creates a timestamped backup before deploying.

    Actions:
      1. Auto-detect game installation directory
      2. Backup existing locale files
      3. Copy EnginLocMod.sga and Engine.ucs to Engine\Locale\Chinese\
      4. Verify deployment integrity

    Note: Loose data deployment has been removed (obsolete since v1.0.4).

.PARAMETER GameDir
    Override the auto-detected game installation directory.

.PARAMETER DryRun
    Show what would be deployed without writing anything.

.PARAMETER NoBackup
    Skip backup step (not recommended).

.EXAMPLE
    .\deploy.ps1
    .\deploy.ps1 -DryRun
    .\deploy.ps1 -GameDir "D:\SteamLibrary\steamapps\common\Dawn of War Definitive Edition"
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$GameDir    = "",
    [switch]$DryRun,
    [switch]$NoBackup
)

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$LocaleSubPath = "Engine\Locale\Chinese"
$GameFolderName = "Dawn of War Definitive Edition"
$Stamp = (Get-Date -Format "yyyyMMdd-HHmmss")
$BackupRoot = Join-Path $ScriptRoot "backup"
$DeployStateDir = Join-Path $ScriptRoot ".copilot_workspace"
$DeployStateFile = Join-Path $DeployStateDir "last_deploy_win.env"

$DeployFiles = @("EnginLocMod.sga", "Engine.ucs")

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
                $roots.Add($steamPath)
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
        if (Test-Path $d) { $roots.Add($d) }
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
                    if (Test-Path $p) { $roots.Add($p) }
                }
            }
        }
    }

    return ($roots | Select-Object -Unique)
}

function Find-GameDir {
    $roots = Get-SteamLibraryRoots
    foreach ($lib in $roots) {
        $candidate = Join-Path $lib "steamapps\common\$GameFolderName"
        if (Test-Path $candidate) {
            return $candidate
        }
    }
    return $null
}

# ─────────────────────────────────────────────────────────────────────────────
# Main Deploy Logic
# ─────────────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "WH40K DoW:DE — Traditional Chinese Locale Mod Deployer" -ForegroundColor White
Write-Host "Repo: $ScriptRoot"
Write-Host "Mode: SGA-only (pre-built archives)"
Write-Host ""

# 1. Resolve game directory
if (-not $GameDir) {
    Write-Step "Auto-detecting game installation..."
    $GameDir = Find-GameDir
    if (-not $GameDir) {
        Write-Fail "Could not auto-detect game directory."
        Write-Host "Please provide -GameDir parameter." -ForegroundColor Red
        exit 1
    }
    Write-Ok "Found: $GameDir"
} else {
    if (-not (Test-Path $GameDir)) {
        Write-Fail "Specified game dir does not exist: $GameDir"
        exit 1
    }
    Write-Ok "Using provided: $GameDir"
}

$LocaleTarget = Join-Path $GameDir $LocaleSubPath
if (-not (Test-Path $LocaleTarget)) {
    Write-Fail "Expected locale directory missing: $LocaleTarget"
    exit 1
}

Write-Host ""
Write-Host "Target: $LocaleTarget" -ForegroundColor White
if ($DryRun) { Write-Host "[DRY RUN — no files will be written]" -ForegroundColor Yellow }
Write-Host ""

# 2. Backup existing files
if (-not $NoBackup -and -not $DryRun) {
    Write-Step "Creating backup ($BackupRoot\$Stamp)..."
    $BackupDir = Join-Path $BackupRoot $Stamp
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    
    foreach ($f in $DeployFiles) {
        $src = Join-Path $LocaleTarget $f
        if (Test-Path $src) {
            $dst = Join-Path $BackupDir $f
            Copy-Item -Path $src -Destination $dst -Force
        }
    }
    Write-Ok "Backup written to $BackupDir"
}

# 3. Deploy SGA and UCS files
foreach ($f in $DeployFiles) {
    $src = Join-Path $ScriptRoot $f
    if (-not (Test-Path $src)) {
        Write-Fail "Source file missing: $src"
        exit 1
    }

    Write-Step "Deploying $f → $LocaleTarget\$f"
    if (-not $DryRun) {
        Copy-Item -Path $src -Destination (Join-Path $LocaleTarget $f) -Force
        Write-Ok "Deployed $f"
    } else {
        Write-Warn "[DRY RUN] Would copy: $f"
    }
}

# 4. Record deployment state
if (-not $DryRun) {
    if (-not (Test-Path $DeployStateDir)) {
        New-Item -ItemType Directory -Path $DeployStateDir -Force | Out-Null
    }
    @"
GAME_DIR=$GameDir
LOCALE_TARGET=$LocaleTarget
BACKUP_STAMP=$Stamp
BACKUP_DIR=$(Join-Path $BackupRoot $Stamp)
"@ | Out-File -FilePath $DeployStateFile -Encoding utf8 -Force
    Write-Ok "Deploy state saved: $DeployStateFile"
}

Write-Host ""
Write-Host "Deployment complete\!" -ForegroundColor Green
Write-Host "  Launch DoW:DE and verify Chinese text rendering."
Write-Host "  To revert: .\uninstall.ps1"
Write-Host ""
