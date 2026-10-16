#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Package the Black Book BepInEx 5 (Mono, x64) framework mod as a
  Vortex-installable zip.

.DESCRIPTION
  Windows PowerShell equivalent of package.sh. Both scripts implement the SAME
  recipe: download the pinned upstream archive, verify its SHA-256, stage it
  with modinfo.json, and write a flat, deterministic zip to ..\dist\.

  Black Book is a Unity 2018.4 Mono title, so it needs BepInEx 5 (x64), NOT
  BepInEx 6 IL2CPP. Do not change the pin without also updating modinfo.json and
  tc-localization\build_plugin.sh, which verify the same archive.

  The framework binaries are NOT committed — only this script is.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Dist = Join-Path $Here '..\dist'
$Version = (Get-Content (Join-Path $Here 'modinfo.json') -Raw | ConvertFrom-Json).version
$Out = Join-Path $Dist "bepinex-framework-v$Version.zip"

# Pinned upstream artifact (BepInEx 5.4.23.5, win-x64).
$BepInExVersion = '5.4.23.5'
$OfficialUrl = "https://github.com/BepInEx/BepInEx/releases/download/v$BepInExVersion/BepInEx_win_x64_$BepInExVersion.zip"
$OfficialSha256 = '82f9878551030f54657792c0740d9d51a09500eeae1fba21106b0c441e6732c4'

# Fast path: reuse a previously downloaded upstream archive. Verified below either way.
$Cached = Join-Path $Dist "BepInEx_win_x64_$BepInExVersion.zip"

$Stage = Join-Path ([System.IO.Path]::GetTempPath()) ("bb-bepinex-" + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $Stage | Out-Null
try {
  if (Test-Path $Cached) {
    Write-Host "[1/3] reusing cached upstream archive: $(Split-Path -Leaf $Cached)"
    $SrcZip = $Cached
  } else {
    Write-Host "[1/3] downloading official BepInEx $BepInExVersion (win-x64)..."
    $SrcZip = Join-Path $Stage 'bepinex-official.zip'
    Invoke-WebRequest -Uri $OfficialUrl -OutFile $SrcZip -UseBasicParsing
  }

  Write-Host '      verifying SHA-256...'
  $actual = (Get-FileHash -Algorithm SHA256 -Path $SrcZip).Hash.ToLowerInvariant()
  if ($actual -ne $OfficialSha256) {
    throw "SHA-256 mismatch - aborting (expected $OfficialSha256, got $actual)"
  }

  # Cache the verified archive so later runs take the reuse path above.
  if ($SrcZip -ne $Cached) {
    New-Item -ItemType Directory -Path $Dist -Force | Out-Null
    Copy-Item $SrcZip $Cached -Force
  }

  Write-Host '[2/3] stage framework + modinfo'
  $Pkg = Join-Path $Stage 'pkg'
  New-Item -ItemType Directory -Path $Pkg | Out-Null
  Expand-Archive -Path $SrcZip -DestinationPath $Pkg -Force
  Copy-Item (Join-Path $Here 'modinfo.json') (Join-Path $Pkg 'modinfo.json') -Force

  Write-Host "[3/3] zip -> dist\$(Split-Path -Leaf $Out)"
  New-Item -ItemType Directory -Path $Dist -Force | Out-Null
  if (Test-Path $Out) { Remove-Item $Out -Force }

  Add-Type -AssemblyName System.IO.Compression
  Add-Type -AssemblyName System.IO.Compression.FileSystem

  # Deterministic archive (AGENTS.md rule 15): fixed 1980-01-01 local-midnight
  # timestamps, files only (no directory entries), added in byte-sorted order.
  $fixed = [System.DateTimeOffset]::Parse('1980-01-01T00:00:00')
  $pkgFull = (Resolve-Path $Pkg).Path
  $files = Get-ChildItem -Path $Pkg -Recurse -File -Force |
    ForEach-Object { $_.FullName.Substring($pkgFull.Length + 1).Replace('\', '/') } |
    Sort-Object

  $fs = [System.IO.File]::Open($Out, [System.IO.FileMode]::Create)
  try {
    $zip = New-Object System.IO.Compression.ZipArchive($fs, [System.IO.Compression.ZipArchiveMode]::Create, $false)
    try {
      foreach ($rel in $files) {
        $entry = $zip.CreateEntry($rel, [System.IO.Compression.CompressionLevel]::Optimal)
        $entry.LastWriteTime = $fixed
        $src = Join-Path $pkgFull ($rel.Replace('/', '\'))
        $in = [System.IO.File]::OpenRead($src)
        try {
          $out = $entry.Open()
          try { $in.CopyTo($out) } finally { $out.Dispose() }
        } finally { $in.Dispose() }
      }
    } finally { $zip.Dispose() }
  } finally { $fs.Dispose() }

  Write-Host "packaged -> $Out ($((Get-Item $Out).Length) bytes)"
} finally {
  Remove-Item $Stage -Recurse -Force -ErrorAction SilentlyContinue
}
