param(
    [string]$VenvDir = ".venv-relic",
    [string]$Manifest = "",
    [string]$OutSga = ""
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

if ([string]::IsNullOrWhiteSpace($Manifest)) {
    $m = Get-ChildItem -Path $root -File -Include *.arciv,*.json | Select-Object -First 1
    if (-not $m) {
        throw "No .arciv/.json manifest found in $root. Make sure unpack step created one, or pass -Manifest explicitly."
    }
    $Manifest = $m.FullName
} elseif (-not (Test-Path $Manifest)) {
    $Manifest = Join-Path $root $Manifest
    if (-not (Test-Path $Manifest)) {
        throw "Manifest not found: $Manifest"
    }
}

if ([string]::IsNullOrWhiteSpace($OutSga)) {
    if (Test-Path (Join-Path $root "EnginLoc.sga")) {
        $OutSga = Join-Path $root "EnginLoc.new.sga"
    } elseif (Test-Path (Join-Path $root "EngineLoc.sga")) {
        $OutSga = Join-Path $root "EngineLoc.new.sga"
    } else {
        $OutSga = Join-Path $root "Locale.new.sga"
    }
}

Write-Host "Packing manifest: $Manifest"
Write-Host "Output SGA: $OutSga"

Invoke-NativeChecked -FilePath $relicExe -Arguments @("sga", "v2", "pack", $Manifest, $OutSga)

Write-Host "Pack complete. Keep your original SGA as backup; test with the new archive first."
