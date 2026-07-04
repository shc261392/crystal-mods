<#
.SYNOPSIS
    Repack data/ directory into EnginLocMod.sga using Archive.exe

.DESCRIPTION
    This PowerShell script must be run from Windows (not WSL2) to use Archive.exe.
    It creates a buildfile and repacks the data/ directory into EnginLocMod.sga.

.PARAMETER GameDir
    Path to Dawn of War Definitive Edition installation (where Archive.exe is located)

.PARAMETER SkipBackup
    Skip backing up existing EnginLocMod.sga

.EXAMPLE
    .\scripts\repack_sga_windows.ps1
    .\scripts\repack_sga_windows.ps1 -GameDir "D:\SteamLibrary\steamapps\common\Dawn of War Definitive Edition"
#>
param(
    [string]$GameDir = "D:\SteamLibrary\steamapps\common\Dawn of War Definitive Edition",
    [switch]$SkipBackup
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

Write-Host ""
Write-Host "WH40K DoW:DE — SGA Repacking (Windows native)" -ForegroundColor Cyan
Write-Host ""

# Verify prerequisites
$ArchiveExe = Join-Path $GameDir "Archive.exe"
if (-not (Test-Path $ArchiveExe)) {
    Write-Error "Archive.exe not found: $ArchiveExe"
    Write-Host "Please specify correct -GameDir parameter" -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ Found Archive.exe: $ArchiveExe" -ForegroundColor Green

$DataDir = Join-Path $RepoRoot "data"
if (-not (Test-Path $DataDir)) {
    Write-Error "data/ directory not found: $DataDir"
    Write-Host "Run font patching scripts first to create data/ directory" -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ Found data/ directory" -ForegroundColor Green

# Backup existing SGA
if (-not $SkipBackup) {
    $ExistingSga = Join-Path $RepoRoot "EnginLocMod.sga"
    if (Test-Path $ExistingSga) {
        $Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $BackupPath = "$ExistingSga.backup.$Timestamp"
        Move-Item $ExistingSga $BackupPath -Force
        Write-Host "✓ Backed up existing SGA to: $BackupPath" -ForegroundColor Green
    }
}

# Create buildfile
Write-Host ""
Write-Host "▶ Creating SGA buildfile..." -ForegroundColor Cyan

$BuildfilePath = Join-Path $RepoRoot ".copilot_workspace\EnginLocBuild.txt"
$BuildfileDir = Split-Path -Parent $BuildfilePath
if (-not (Test-Path $BuildfileDir)) {
    New-Item -ItemType Directory -Path $BuildfileDir -Force | Out-Null
}

$BuildfileContent = @"
Archive
TOCStart alias="data" relativeroot="."
FileSettingsStart defcompression="1"
    Override wildcard=".*(gfx)$" minsize="-1" maxsize="-1" ct="1"
    Override wildcard=".*(fnt)$" minsize="-1" maxsize="-1" ct="2"
    Override wildcard=".*(ttf|ttc)$" minsize="-1" maxsize="-1" ct="0"
    Override wildcard=".*(fda|rat)$" minsize="-1" maxsize="-1" ct="2"
FileSettingsEnd
TOCEnd
"@

# Write with CRLF line endings (required by Archive.exe)
$BuildfileContent -split "`n" | ForEach-Object { "$_`r`n" } | Set-Content -Path $BuildfilePath -NoNewline
Write-Host "✓ Buildfile created: $BuildfilePath" -ForegroundColor Green

# Repack SGA
Write-Host ""
Write-Host "▶ Repacking SGA (this takes ~60 seconds)..." -ForegroundColor Cyan
Write-Host ""

$OutputSga = Join-Path $RepoRoot "EnginLocMod.sga"

$ArchiveArgs = @(
    "-build", $BuildfilePath,
    "-sourcedir", $DataDir,
    "-archive", $OutputSga,
    "-verbose"
)

Write-Host "Command: Archive.exe $($ArchiveArgs -join ' ')" -ForegroundColor DarkGray
Write-Host ""

& $ArchiveExe @ArchiveArgs

if ($LASTEXITCODE -ne 0) {
    Write-Error "Archive.exe failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

if (-not (Test-Path $OutputSga)) {
    Write-Error "EnginLocMod.sga was not created"
    exit 1
}

$SgaSize = (Get-Item $OutputSga).Length / 1MB
Write-Host ""
Write-Host "✓ EnginLocMod.sga built successfully!" -ForegroundColor Green
Write-Host "  Size: $([math]::Round($SgaSize, 1)) MB" -ForegroundColor White
Write-Host "  Path: $OutputSga" -ForegroundColor White

# Verify by extracting one file
Write-Host ""
Write-Host "▶ Verifying SGA contents..." -ForegroundColor Cyan

$VerifyDir = Join-Path $RepoRoot ".copilot_workspace\verify_repack"
if (Test-Path $VerifyDir) {
    Remove-Item $VerifyDir -Recurse -Force
}
New-Item -ItemType Directory -Path $VerifyDir -Force | Out-Null

$ExtractArgs = @(
    "-extract", $OutputSga,
    "-outpath", $VerifyDir
)

& $ArchiveExe @ExtractArgs | Out-Null

$VerifyFont = Join-Path $VerifyDir "data\font\notosans_m_16_xc.fnt"
if (Test-Path $VerifyFont) {
    $SizeDefaultLine = Get-Content $VerifyFont | Select-String "^\s*sizeDefault"
    Write-Host "✓ Extracted sample font:" -ForegroundColor Green
    Write-Host "  $SizeDefaultLine" -ForegroundColor White
    
    if ($SizeDefaultLine -match "= (\d+);") {
        $ActualSize = $matches[1]
        Write-Host ""
        Write-Host "Font size in SGA: $ActualSize" -ForegroundColor Cyan
    }
} else {
    Write-Warning "Could not verify font size (extraction failed)"
}

Write-Host ""
Write-Host "✓ SGA repack complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Run: make package (to create distribution zip)"
Write-Host "  2. Test the package in-game"
Write-Host "  3. For size 48 variant: patch with SIZE=48 and rerun this script"
Write-Host ""
