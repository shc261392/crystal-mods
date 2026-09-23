# ---------------------------------------------------------------------------
# potato-marines - Space Marine 2 aggressive FPS mod - deploy (Windows 11)
#
# Builds dist\potato-marines.pak (if missing) and installs it into the game's
# official mods folder (client_pc\root\mods\), writing pak_config.yaml.
#
# NOTE: any mod disables public matchmaking (private lobbies only, separate
# progression, "MODS DETECTED" watermark). This mod is accepted as such.
#
# Usage: .\deploy.ps1 [-GamePath <dir>]
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
Write-Host "Game install:  $GamePath"

$ModsDir = Join-Path $GamePath 'client_pc\root\mods'
if (-not (Test-Path $ModsDir)) { Write-Error "mods dir not found: $ModsDir" }
Write-Host "Mods dir:      $ModsDir"
$CfgDir = Join-Path $GamePath 'client_pc\root\config\pc'
$Cfg = Join-Path $CfgDir 'game.cfg'

# ── build pak if missing ──────────────────────────────────────────────────
$Pak = Join-Path $ScriptDir ("dist\{0}" -f $PakName)
if (-not (Test-Path $Pak)) {
    Write-Host "$PakName missing - building..."
    Push-Location $ScriptDir
    python3 scripts\build_pak.py
    Pop-Location
    if (-not (Test-Path $Pak)) { Write-Error "build failed: dist\$PakName not produced" }
}

# ── backup existing game-side artifacts (non-destructive) ─────────────────
$Ts = Get-Date -Format 'yyyyMMdd-HHmmss'
$BackupDir = Join-Path $BackupRoot $Ts
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
$Manifest = Join-Path $BackupDir 'MANIFEST.txt'
@("# potato-marines deploy backup $Ts", "# source: $ModsDir") | Set-Content -Path $Manifest
if (Test-Path (Join-Path $ModsDir $PakName)) {
    Copy-Item -LiteralPath (Join-Path $ModsDir $PakName) -Destination (Join-Path $BackupDir "$PakName.prev")
    Add-Content -Path $Manifest -Value $PakName
}
if (Test-Path (Join-Path $ModsDir 'pak_config.yaml')) {
    Copy-Item -LiteralPath (Join-Path $ModsDir 'pak_config.yaml') -Destination (Join-Path $BackupDir 'pak_config.yaml.prev')
    Add-Content -Path $Manifest -Value 'pak_config.yaml'
}
if (Test-Path $Cfg) {
    Copy-Item -LiteralPath $Cfg -Destination (Join-Path $BackupDir 'game.cfg.prev')
    Add-Content -Path $Manifest -Value 'game.cfg'
}

# ── install ───────────────────────────────────────────────────────────────
Copy-Item -LiteralPath $Pak -Destination (Join-Path $ModsDir $PakName) -Force
Write-Host "installed $ModsDir\$PakName"

$Config = Join-Path $ModsDir 'pak_config.yaml'
if (-not (Test-Path $Config)) {
    Set-Content -Path $Config -Value "- pak: $PakName"
} elseif (-not (Select-String -Path $Config -Pattern $PakName -Quiet)) {
    Add-Content -Path $Config -Value "- pak: $PakName"
}
Write-Host "pak_config.yaml ready: $Config"

# ── install engine config (game.cfg) ──────────────────────────────────────
New-Item -ItemType Directory -Force -Path $CfgDir | Out-Null
Copy-Item -LiteralPath (Join-Path $ScriptDir 'data\game.cfg') -Destination $Cfg -Force
Write-Host "installed engine config: $Cfg"

Write-Host @"

===============================================================
 potato-marines installed - aggressive FPS (poor-PC) config
===============================================================
PAK (verified loading): swarm 0.7->0.2, gibs 23/43->6/12, ragdolls
  5/15->0/2, corpses 40->8, gore 65->12.

ENGINE CONFIG (game.cfg - experimental): disables SSAO/SSR/RTAO/DOF/
  water-sim/covering/capsule+screen-space shadows/dissolve/distortion,
  floors FogVolume+Lightshaft+Shadow+Effects+Details quality, caps
  engine workers to 8, enables anim/morpheme batching.

> VERIFY: if game.cfg is parsed, the scene looks flat (no AO), no
> depth-of-field, harsher shadows. If the game looks UNCHANGED, the
> game.cfg format wasn't read (delete it and tell us).
> Revert anytime: Remove-Item $Cfg ; .\uninstall.ps1

IN-GAME also set: SSAO=OFF, SSR=OFF, Motion Blur=OFF (the menu allows
OFF for SSAO/SSR), Quality Preset=Low, Dynamic Resolution ON target
120, Frame Generation FSR3 ON.

> Mod active: private lobbies only, separate progression, watermark.
===============================================================
"@