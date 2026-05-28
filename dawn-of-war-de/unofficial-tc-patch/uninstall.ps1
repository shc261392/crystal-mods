<#
.SYNOPSIS
    WH40K DoW:DE — Traditional Chinese Locale Mod Uninstaller (Windows native)

.DESCRIPTION
    Reverts a previous deployment made by deploy.ps1.
    Reads the last deploy state from .copilot_workspace\last_deploy_win.env.

    Actions:
      1. Re-enable EnginLoc.sga (rename from .disabled → .sga)
      2. Remove deployed data\ directory
      3. Remove deployed Engine.ucs
      4. Restore files from the timestamped backup

.PARAMETER GameDir
    Override the stored game directory.

.PARAMETER DryRun
    Show what would be removed without writing anything.

.EXAMPLE
    .\uninstall.ps1
    .\uninstall.ps1 -DryRun
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$GameDir = "",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$LocaleSubPath = "Engine\Locale\Chinese"
$DeployStateFile = Join-Path $ScriptRoot ".copilot_workspace\last_deploy_win.env"

$DeployDirs  = @("data")
$DeployFiles = @("Engine.ucs")

function Write-Step  { param([string]$Msg) Write-Host "▶ $Msg" -ForegroundColor Cyan }
function Write-Ok    { param([string]$Msg) Write-Host "✓ $Msg" -ForegroundColor Green }
function Write-Warn  { param([string]$Msg) Write-Host "⚠ $Msg" -ForegroundColor Yellow }

Write-Host ""
Write-Host "WH40K DoW:DE — Traditional Chinese Locale Mod Uninstaller (Windows)" -ForegroundColor White -BackgroundColor DarkRed
Write-Host ""

# ── Load stored deploy state ──────────────────────────────────────────────────
$BackupDirStored = ""
$LocaleTargetStored = ""

if (Test-Path $DeployStateFile) {
    Write-Step "Loading deploy state: $DeployStateFile"
    Get-Content $DeployStateFile | ForEach-Object {
        if ($_ -match '^GAME_DIR=(.+)$')       { if ([string]::IsNullOrWhiteSpace($GameDir)) { $GameDir = $Matches[1] } }
        if ($_ -match '^LOCALE_TARGET=(.+)$')  { $LocaleTargetStored = $Matches[1] }
        if ($_ -match '^BACKUP_DIR=(.+)$')      { $BackupDirStored = $Matches[1] }
    }
} else {
    Write-Warn "No deploy state found ($DeployStateFile). Using DOW_GAME_DIR or -GameDir."
}

if ([string]::IsNullOrWhiteSpace($GameDir)) {
    $GameDir = $env:DOW_GAME_DIR
}
if ([string]::IsNullOrWhiteSpace($GameDir)) {
    throw "Could not determine game directory. Run deploy.ps1 first or pass -GameDir."
}

$LocaleTarget = if ($LocaleTargetStored) { $LocaleTargetStored } else { Join-Path $GameDir $LocaleSubPath }

if (-not (Test-Path $LocaleTarget)) {
    throw "Locale directory not found: $LocaleTarget"
}

Write-Host "Target: $LocaleTarget"
if ($DryRun) { Write-Warn "[DRY RUN — no files will be written]" }
Write-Host ""

# ── 1. Re-enable EnginLoc.sga ────────────────────────────────────────────────
$sgaDisabled = Join-Path $LocaleTarget "EnginLoc.sga.disabled"
$sgaActive   = Join-Path $LocaleTarget "EnginLoc.sga"

if (Test-Path $sgaDisabled) {
    Write-Step "Re-enabling EnginLoc.sga..."
    if (-not $DryRun) {
        Rename-Item -Path $sgaDisabled -NewName "EnginLoc.sga" -Force
        Write-Ok "Renamed EnginLoc.sga.disabled → EnginLoc.sga"
    } else {
        Write-Warn "[DRY RUN] Would rename: EnginLoc.sga.disabled → EnginLoc.sga"
    }
} elseif (Test-Path $sgaActive) {
    Write-Ok "EnginLoc.sga already active"
} else {
    Write-Warn "EnginLoc.sga not found in either state — skipping"
}

# ── 2. Remove deployed directories ───────────────────────────────────────────
foreach ($d in $DeployDirs) {
    $target = Join-Path $LocaleTarget $d
    if (Test-Path $target) {
        Write-Step "Removing deployed directory: $target"
        if (-not $DryRun) {
            Remove-Item -Recurse -Force $target
            Write-Ok "Removed $target"
        } else {
            Write-Warn "[DRY RUN] Would remove: $target"
        }
    } else {
        Write-Warn "Not found (already removed?): $target"
    }
}

# ── 3. Remove deployed files ─────────────────────────────────────────────────
foreach ($f in $DeployFiles) {
    $target = Join-Path $LocaleTarget $f
    if (Test-Path $target) {
        Write-Step "Removing deployed file: $target"
        if (-not $DryRun) {
            Remove-Item -Force $target
            Write-Ok "Removed $target"
        } else {
            Write-Warn "[DRY RUN] Would remove: $target"
        }
    } else {
        Write-Warn "Not found (already removed?): $target"
    }
}

# ── 4. Restore from backup ───────────────────────────────────────────────────
if ($BackupDirStored -and (Test-Path $BackupDirStored)) {
    Write-Step "Restoring backup from $BackupDirStored ..."
    if (-not $DryRun) {
        $rcArgs = @($BackupDirStored, $LocaleTarget, "/E", "/NJH", "/NJS")
        $rc = Start-Process -FilePath "robocopy" -ArgumentList $rcArgs -Wait -PassThru -NoNewWindow
        if ($rc.ExitCode -ge 8) { throw "robocopy restore failed (exit $($rc.ExitCode))" }
        Write-Ok "Backup restored."
    } else {
        Write-Warn "[DRY RUN] Would restore from: $BackupDirStored"
    }
} else {
    Write-Warn "No backup directory found — skipping restore"
    Write-Warn "(EnginLoc.sga re-enabled; game will load original packed locale)"
}

# ── 5. Clear stored deploy state ─────────────────────────────────────────────
if (-not $DryRun -and (Test-Path $DeployStateFile)) {
    Remove-Item $DeployStateFile -Force
    Write-Ok "Deploy state cleared"
}

Write-Host ""
Write-Host "Uninstall complete!" -ForegroundColor Green
Write-Host "  The game will now load the original EnginLoc.sga locale archive."
Write-Host "  To re-deploy: .\deploy.ps1"
Write-Host ""
