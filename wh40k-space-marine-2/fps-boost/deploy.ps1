# ---------------------------------------------------------------------------
# fps-boost - Space Marine 2 potato-mode config (Windows 11)
#
# Non-mod configuration that keeps public matchmaking. Applies:
#   1. Windows power plan -> Ultimate Performance (best effort).
#   2. Prints the in-game + CPU-core config guide and the affinity helper.
#
# No game files are modified. Nothing is installed into the game folder.
#
# Usage: .\deploy.ps1 [-GamePath <dir>]
# Env:   SM2_GAME_PATH
# ---------------------------------------------------------------------------
[CmdletBinding()]
param([string]$GamePath)

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

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
}
if ($GamePath) { Write-Host "Game install:  $GamePath" }

# ── power plan -> Ultimate Performance (best effort) ──────────────────────
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
if ($isAdmin) {
    powercfg /setactive e9a42b02-d5df-448d-aa00-03f14749eb61 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host 'Windows power plan -> Ultimate Performance.'
    } else {
        Write-Warning 'Could not activate Ultimate Performance (create it once: powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61).'
    }
} else {
    Write-Host 'Power plan not changed (run as Administrator to apply Ultimate Performance).'
}

Write-Host @"

===============================================================
 fps-boost - potato-mode config (keeps public matchmaking)
===============================================================
IN-GAME (Options -> Graphics):
  Upscaling          = DLSS Quality
  Frame Generation   = FSR 3 ON      <- the 120 lever on a CPU-pinned rig
  FPS cap            = 120
  Dynamic Resolution = ON, target 120
  Details/Effects/Fog Volume = Low, Swarm/Physics/Cloth = Low
  NVIDIA Reflex      = On

CPU CORE AGGRESSION (OS-level, EAC-safe):
  While the game runs -> ADMIN PowerShell:
      .\scripts\apply-affinity.ps1   (pins to physical cores, High priority)

OPTIONAL - Lossless Scaling (you own it): LSFG 3.0 frame-gen on top,
  instead of the game's FSR3 FG (not both).

Expected on 5800X + 3090: ~90-120 displayed FPS in full swarms.
Docs: docs\settings-preset.md, docs\engine-analysis.md
===============================================================
"@