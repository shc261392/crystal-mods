#Requires -Version 5
<#
.SYNOPSIS
  The Great Crusade — manual deploy (Windows). Prefer installing via Vortex.
.DESCRIPTION
  Extracts the chosen variant ZIP's bundle into the game folder, backing up the
  original once.
.EXAMPLE
  ./deploy.ps1 -Zip dist/the-great-crusade-exp-x4-levels-15-v0.1.0.zip
#>
param(
  [Parameter(Mandatory = $true)][string]$Zip,
  [string]$GameDir = $(if ($env:BS_GAME_DIR) { $env:BS_GAME_DIR } else { "D:\SteamLibrary\steamapps\common\Warhammer 40000 Battlesector" })
)
$ErrorActionPreference = 'Stop'
$rel = "Warhammer 40K Battlesector_Data\StreamingAssets\startup_assets_all.bundle"

if (-not (Test-Path $Zip)) { Write-Error "zip not found: $Zip"; exit 2 }
if (-not (Test-Path $GameDir)) { Write-Error "game folder not found: $GameDir"; exit 2 }

$target = Join-Path $GameDir $rel
$bak = "$target.the-great-crusade.bak"
if ((Test-Path $target) -and -not (Test-Path $bak)) {
  Copy-Item -LiteralPath $target -Destination $bak -Force
  Write-Host "backed up original -> $(Split-Path $bak -Leaf)"
}

$tmp = New-Item -ItemType Directory -Path ([System.IO.Path]::GetTempPath()) -Name ([System.Guid]::NewGuid())
try {
  Expand-Archive -LiteralPath $Zip -DestinationPath $tmp -Force
  Copy-Item -LiteralPath (Join-Path $tmp $rel) -Destination $target -Force
  Write-Host "deployed $(Split-Path $Zip -Leaf) -> $target"
}
finally {
  Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
