param(
    [string]$VenvDir = ".venv-relic"
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

Write-Host "[1/3] Creating virtual environment at $VenvDir ..."
python -m venv $VenvDir

$pythonExe = Join-Path $root "$VenvDir\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    throw "Python venv creation failed. Could not find: $pythonExe"
}

Write-Host "[2/3] Upgrading pip ..."
Invoke-NativeChecked -FilePath $pythonExe -Arguments @("-m", "pip", "install", "--upgrade", "pip")

Write-Host "[2.5/3] Installing setuptools compatibility shim (pkg_resources) ..."
Invoke-NativeChecked -FilePath $pythonExe -Arguments @("-m", "pip", "install", "setuptools<81")

Write-Host "[3/3] Installing MAK Relic SGA tools ..."
Invoke-NativeChecked -FilePath $pythonExe -Arguments @("-m", "pip", "install", "relic-tool-sga", "relic-tool-sga-v2")

Write-Host "Done. Test command:"
Write-Host "  $VenvDir\Scripts\relic.exe --help"
