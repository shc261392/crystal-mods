#Requires -Version 5
<#
.SYNOPSIS
  The Great Crusade — restore the vanilla bundle backed up by deploy.ps1.
.EXAMPLE
  ./uninstall.ps1
#>
param(
  [string]$GameDir = $(if ($env:BS_GAME_DIR) { $env:BS_GAME_DIR } else { "D:\SteamLibrary\steamapps\common\Warhammer 40000 Battlesector" })
)
$ErrorActionPreference = 'Stop'
$rel = "Warhammer 40K Battlesector_Data\StreamingAssets\startup_assets_all.bundle"
$target = Join-Path $GameDir $rel
$bak = "$target.the-great-crusade.bak"

if (Test-Path $bak) {
  Move-Item -LiteralPath $bak -Destination $target -Force
  Write-Host "restored original bundle from backup"
}
else {
  Write-Error "no backup found ($bak); nothing to restore"
  exit 1
}
