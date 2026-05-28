param(
    [string]$VenvDir = ".venv-relic",
    [string]$SgaName = "",
    [switch]$NoBackup
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

function Invoke-NativeChecked {
    param([string]$FilePath, [string[]]$Arguments)

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed ($LASTEXITCODE): $FilePath $($Arguments -join ' ')"
    }
}

$relicExe = Join-Path $root "$VenvDir\Scripts\relic.exe"
if (-not (Test-Path $relicExe)) {
    throw "Cannot find $relicExe. Run .\setup_relic_tool.ps1 first."
}

if ([string]::IsNullOrWhiteSpace($SgaName)) {
    $candidates = @("EnginLoc.sga", "EngineLoc.sga")
    $found = @($candidates | Where-Object { Test-Path (Join-Path $root $_) })

    if ($found.Count -gt 0) {
        $sgaPath = Join-Path $root $found[0]
    } else {
        $fallback = Get-ChildItem -Path $root -Filter "*.sga" -File | Select-Object -First 1
        if (-not $fallback) {
            throw "No .sga file found in $root"
        }
        $sgaPath = $fallback.FullName
    }
} else {
    $sgaPath = Join-Path $root $SgaName
    if (-not (Test-Path $sgaPath)) {
        throw "Specified SGA not found: $sgaPath"
    }
}

Write-Host "Using SGA: $sgaPath"

if (-not $NoBackup) {
    $backupDir = Join-Path $root "backup"
    New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupPath = Join-Path $backupDir ("{0}.{1}.bak" -f [System.IO.Path]::GetFileName($sgaPath), $stamp)
    Copy-Item -Path $sgaPath -Destination $backupPath -Force
    Write-Host "Backup created: $backupPath"
}

Write-Host "Unpacking SGA to locale folder (expecting data/ output)..."
Invoke-NativeChecked -FilePath $relicExe -Arguments @("sga", "unpack", $sgaPath, $root)

Write-Host "Unpack complete. If successful, you should now have a data folder in: $root"
