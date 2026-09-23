# ---------------------------------------------------------------------------
# potato-marines - Space Marine 2 aggressive FPS mod - uninstall (Windows 11)
#
# Removes potato-marines.pak from the game's mods folder and restores the
# previous pak_config.yaml (if one was backed up). Idempotent.
#
# Usage: .\uninstall.ps1 [-GamePath <dir>]
# Env:   SM2_GAME_PATH
# ---------------------------------------------------------------------------
[CmdletBinding()]
param([string]$GamePath)

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackupRoot = Join-Path $ScriptDir 'backup'
$PakName = 'potato-marines.pak'

function Resolve-SteamInstall {
    $roots = @(
        (Get-ItemProperty 'HKLM:\SOFTWARE\WOW6432Node\Valve\Steam' -ErrorAction SilentlyContinue).InstallPath,
        (Get-ItemProperty 'HKLM:\SOFTWARE\Valve\Steam' -ErrorAction SilentlyContinue).InstallPath,
        "$env:ProgramFiles(x86)\Steam",
        "$env:ProgramFiles\Steam"
    ) | Where-Object { $_ }
    foreach ($root in $roots | Select-Object -Unique) {
        $vdf = Join-Path $root 'steamapps\libraryfolders.vdf'
        if (Test-Path $vdf) {
            foreach ($line in Get-Content $vdf) {
                if ($line -match '"path"\s+"(.+)"') {
                    $lib = $Matches[1] -replace '\\\\', '\'
                    $cand = Join-Path $lib 'steamapps\common\Space Marine 2'
                    if (Test-Path (Join-Path $cand 'client_pc')) { return $cand }
                }
            }
        }
        $cand = Join-Path $root 'steamapps\common\Space Marine 2'
        if (Test-Path (Join-Path $cand 'client_pc')) { return $cand }
    }
    return $null
}

if ($GamePath) {
    if (-not (Test-Path (Join-Path $GamePath 'client_pc'))) { Write-Error "game dir not found: $GamePath" }
} elseif ($env:SM2_GAME_PATH) {
    $GamePath = $env:SM2_GAME_PATH
    if (-not (Test-Path (Join-Path $GamePath 'client_pc'))) { Write-Error "SM2_GAME_PATH invalid: $GamePath" }
} else {
    $GamePath = Resolve-SteamInstall
    if (-not $GamePath) { Write-Error "could not auto-detect Space Marine 2. Pass -GamePath <dir>." }
}
$ModsDir = Join-Path $GamePath 'client_pc\root\mods'

if (Test-Path (Join-Path $ModsDir $PakName)) {
    Remove-Item -LiteralPath (Join-Path $ModsDir $PakName) -Force
    Write-Host "removed $ModsDir\$PakName"
} else {
    Write-Warning "$PakName not installed (nothing to remove)."
}

$latest = Get-ChildItem $BackupRoot -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '^\d{8}-\d{6}$' } |
    Sort-Object Name -Descending | Select-Object -First 1
if ($latest -and (Test-Path (Join-Path $latest.FullName 'pak_config.yaml.prev'))) {
    Copy-Item -LiteralPath (Join-Path $latest.FullName 'pak_config.yaml.prev') -Destination (Join-Path $ModsDir 'pak_config.yaml') -Force
    Write-Host "restored $ModsDir\pak_config.yaml from backup $($latest.Name)"
} elseif (Test-Path (Join-Path $ModsDir 'pak_config.yaml')) {
    if (Select-String -Path (Join-Path $ModsDir 'pak_config.yaml') -Pattern $PakName -Quiet) {
        Remove-Item -LiteralPath (Join-Path $ModsDir 'pak_config.yaml') -Force
        Write-Host "removed our $ModsDir\pak_config.yaml"
    }
}

# game.cfg engine config
$Cfg = Join-Path $GamePath 'client_pc\root\config\pc\game.cfg'
if ($latest -and (Test-Path (Join-Path $latest.FullName 'game.cfg.prev'))) {
    Copy-Item -LiteralPath (Join-Path $latest.FullName 'game.cfg.prev') -Destination $Cfg -Force
    Write-Host "restored $Cfg from backup $($latest.Name)"
} elseif (Test-Path $Cfg) {
    Remove-Item -LiteralPath $Cfg -Force
    Write-Host "removed our $Cfg"
}

Write-Host 'Done. Restart the game; private-lobby mode / watermark cleared.'