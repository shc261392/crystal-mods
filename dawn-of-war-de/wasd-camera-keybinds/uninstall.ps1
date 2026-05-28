<#
.SYNOPSIS
    Restore the most recent backup taken by deploy.ps1
#>
param([string]$GameDir = '')

$ErrorActionPreference = 'Stop'
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$GameFolderName = 'Dawn of War Definitive Edition'

function Write-Ok { param($m) Write-Host "✓ $m" -ForegroundColor Green }
function Die      { param($m) Write-Host "✗ $m" -ForegroundColor Red; exit 1 }

function Get-SteamRoots {
    $roots = New-Object System.Collections.Generic.List[string]
    foreach ($k in 'HKLM:\SOFTWARE\WOW6432Node\Valve\Steam','HKLM:\SOFTWARE\Valve\Steam','HKCU:\Software\Valve\Steam') {
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

$GameDir   = Find-Game
$TargetDir = Join-Path $GameDir 'Engine\defprofile'

$Latest = Get-ChildItem -Path (Join-Path $ScriptRoot 'backup') -Directory -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $Latest) { Die "No backups found under $ScriptRoot\backup\" }

Write-Host "▶ Restoring from $($Latest.FullName)" -ForegroundColor Cyan
Get-ChildItem -Path $Latest.FullName -Filter '*.lua' -File | ForEach-Object {
    Copy-Item $_.FullName (Join-Path $TargetDir $_.Name) -Force
    Write-Ok "Restored $($_.Name)"
}
Write-Ok "Done."
