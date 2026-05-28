<#
.SYNOPSIS
    WH40K DoW:DE — Traditional Chinese Locale Mod Deployer (Windows native)

.DESCRIPTION
    Deploys the TC locale mod to the game installation on Windows.
    Auto-detects Steam game directory from registry and common library paths.
    Creates a timestamped backup before deploying.

    Actions:
      1. Auto-detect game installation directory
      2. Apply font-fix patches via Python (patching data/font/*.fnt in repo)
      3. Backup existing locale files
      4. Copy data/ and Engine.ucs to Engine\Locale\Chinese\
      5. Disable EnginLoc.sga (rename to .disabled) so game loads data/ instead

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

$DeployDirs  = @("data")
$DeployFiles = @("Engine.ucs")

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

    # 4. Scan all drive roots for SteamLibrary folders
    $drives = Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Root -match '^[A-Z]:\\$' }
    foreach ($drv in $drives) {
        foreach ($candidate in @("SteamLibrary", "Steam", "Games\Steam")) {
            $path = Join-Path $drv.Root $candidate
            if (Test-Path $path) { $roots.Add($path) }
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
Write-Host "WH40K DoW:DE — Traditional Chinese Locale Mod Deployer (Windows)" -ForegroundColor White -BackgroundColor DarkBlue
Write-Host "Repo: $ScriptRoot"
Write-Host ""

if ($DryRun) { Write-Warn "[DRY RUN — no files will be written]" }

# 1. Resolve game directory
if ([string]::IsNullOrWhiteSpace($GameDir)) {
    $GameDir = $env:DOW_GAME_DIR
}
if ([string]::IsNullOrWhiteSpace($GameDir)) {
    Write-Step "Auto-detecting game installation..."
    $GameDir = Find-GameDir
    if ([string]::IsNullOrWhiteSpace($GameDir)) {
        Write-Fail "Could not auto-detect game directory."
        Write-Host "Set DOW_GAME_DIR environment variable or use -GameDir parameter." -ForegroundColor Red
        Write-Host "Example: -GameDir 'D:\SteamLibrary\steamapps\common\Dawn of War Definitive Edition'"
        exit 1
    }
    Write-Ok "Found: $GameDir"
} else {
    if (-not (Test-Path $GameDir)) { throw "Specified GameDir does not exist: $GameDir" }
    Write-Ok "Using provided: $GameDir"
}

$LocaleTarget = Join-Path $GameDir $LocaleSubPath
if (-not (Test-Path $LocaleTarget)) {
    throw "Expected locale directory missing: $LocaleTarget"
}
Write-Host "Target: $LocaleTarget"
Write-Host ""

# 2. Apply font-fix patches
Write-Step "Applying font-fix patches (data/font/*.fnt)..."
$PythonExe = $null
$uvExe = Get-Command uv -ErrorAction SilentlyContinue
$py3Exe = Get-Command python -ErrorAction SilentlyContinue

if ($uvExe) {
    $applyArgs = @(
        "run", "python",
        (Join-Path $ScriptRoot "scripts\apply_font_fix.py"),
        "--root", $ScriptRoot,
        "--font", "noto-sans-tc",
        "--restore-from-bak",
        "--mode", "fallback-only",
        "--size", "34"
    )
    if ($DryRun) { $applyArgs += "--dry-run" }
    if (-not $DryRun) {
        & uv @applyArgs
    } else {
        & uv @applyArgs 2>$null
    }
} elseif ($py3Exe) {
    $applyArgs = @(
        (Join-Path $ScriptRoot "scripts\apply_font_fix.py"),
        "--root", $ScriptRoot,
        "--font", "noto-sans-tc",
        "--restore-from-bak",
        "--mode", "fallback-only",
        "--size", "34"
    )
    if ($DryRun) { $applyArgs += "--dry-run" }
    & python @applyArgs
} else {
    Write-Warn "Python not found. Skipping font-fix patch — deploying pre-existing .fnt files."
}

# 3. Backup existing files
if (-not $NoBackup -and -not $DryRun) {
    $BackupStampDir = Join-Path $BackupRoot $Stamp
    New-Item -ItemType Directory -Force -Path $BackupStampDir | Out-Null
    Write-Step "Backing up to $BackupStampDir ..."

    foreach ($d in $DeployDirs) {
        $src = Join-Path $LocaleTarget $d
        if (Test-Path $src) {
            Copy-Item -Recurse -Force $src (Join-Path $BackupStampDir $d)
        }
    }
    foreach ($f in $DeployFiles) {
        $src = Join-Path $LocaleTarget $f
        if (Test-Path $src) {
            Copy-Item -Force $src (Join-Path $BackupStampDir $f)
        }
    }
    foreach ($sgaName in @("EnginLoc.sga", "EnginLoc.sga.disabled")) {
        $src = Join-Path $LocaleTarget $sgaName
        if (Test-Path $src) {
            Copy-Item -Force $src (Join-Path $BackupStampDir $sgaName)
        }
    }
    Write-Ok "Backup done."
}

# 4. Deploy directories
foreach ($d in $DeployDirs) {
    $src  = Join-Path $ScriptRoot $d
    $dest = Join-Path $LocaleTarget $d
    if (-not (Test-Path $src)) { Write-Warn "Source missing, skipping: $src"; continue }

    Write-Step "Deploying $d\ → $dest\"
    if (-not $DryRun) {
        if (-not (Test-Path $dest)) { New-Item -ItemType Directory -Force -Path $dest | Out-Null }
        # Robocopy: mirror without deleting extra files, exclude .bak
        $rcArgs = @($src, $dest, "/E", "/XF", "*.bak", "/NJH", "/NJS")
        $rc = Start-Process -FilePath "robocopy" -ArgumentList $rcArgs -Wait -PassThru -NoNewWindow
        # robocopy exit codes: 0-7 are success (see docs)
        if ($rc.ExitCode -ge 8) { throw "robocopy failed with exit code $($rc.ExitCode)" }
    }
}

# 5. Deploy files
foreach ($f in $DeployFiles) {
    $src  = Join-Path $ScriptRoot $f
    $dest = Join-Path $LocaleTarget $f
    if (-not (Test-Path $src)) { Write-Warn "Source missing, skipping: $src"; continue }

    Write-Step "Deploying $f"
    if (-not $DryRun) { Copy-Item -Force $src $dest }
}

# 6. Disable EnginLoc.sga
$sgaActive   = Join-Path $LocaleTarget "EnginLoc.sga"
$sgaDisabled = Join-Path $LocaleTarget "EnginLoc.sga.disabled"

if (Test-Path $sgaActive) {
    Write-Step "Disabling EnginLoc.sga..."
    if (-not $DryRun) {
        Rename-Item -Path $sgaActive -NewName "EnginLoc.sga.disabled" -Force
        Write-Ok "Renamed EnginLoc.sga → EnginLoc.sga.disabled"
    } else {
        Write-Warn "[DRY RUN] Would rename: EnginLoc.sga → EnginLoc.sga.disabled"
    }
} elseif (Test-Path $sgaDisabled) {
    Write-Ok "EnginLoc.sga already disabled"
} else {
    Write-Warn "EnginLoc.sga not found — game may load stale packed locale"
}

# 7. Save deploy state
if (-not $DryRun) {
    New-Item -ItemType Directory -Force -Path $DeployStateDir | Out-Null
    @"
GAME_DIR=$GameDir
LOCALE_TARGET=$LocaleTarget
BACKUP_STAMP=$Stamp
BACKUP_DIR=$(Join-Path $BackupRoot $Stamp)
"@ | Set-Content $DeployStateFile -Encoding UTF8
    Write-Ok "Deploy state saved: $DeployStateFile"
}

Write-Host ""
Write-Host "Deployment complete!" -ForegroundColor Green -NoNewline
Write-Host "  Launch DoW:DE and verify Chinese text rendering."
Write-Host "  To revert: .\uninstall.ps1"
Write-Host ""
