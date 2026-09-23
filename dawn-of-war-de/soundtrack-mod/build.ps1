<#
.SYNOPSIS
  Build the Faction Soundtrack mod into a Vortex-installable ZIP in dist/.

.DESCRIPTION
  For each faction, place source audio (mp3/wav/flac/ogg) in:  music/<race>/
  Factions with no source audio get a distinct TEST TONE so the mechanism can
  be validated in-game before real music is curated.

  Requires: ffmpeg, and (built-in) Compress-Archive.
  Cross-platform companion: build.sh
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$Here    = Split-Path -Parent $MyInvocation.MyCommand.Path
$ModName = 'FactionSoundtrack'

$Stage    = Join-Path $Here '.copilot_workspace/stage'
$Dist     = Join-Path $Here 'dist'
$Src      = Join-Path $Here 'src'
$MusicSrc = Join-Path $Here 'music'
$Ar       = 44100
$Version  = '0.2'

# Faction token : test-tone frequency (Hz)
$Factions = [ordered]@{
  'Space'      = 523   # Space Marines
  'Chaos'      = 415   # Chaos Space Marines
  'Ork'        = 196   # Orks
  'Eldar'      = 659   # Eldar
  'Guard'      = 294   # Imperial Guard
  'Necron'     = 233   # Necrons
  'Tau'        = 784   # Tau Empire
  'Sisters'    = 880   # Sisters of Battle
  'Dark_Eldar' = 466   # Dark Eldar
}

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { throw 'ffmpeg not found' }

Write-Host '==> Cleaning staging'
if (Test-Path $Stage) { Remove-Item -Recurse -Force $Stage }
# Distribution layout (matches the official Mod Assistant structure):
#   <ModName>/<ModName>.module ; <ModName>/pipeline.ini ; <ModName>/Mod/Data/...
$ModRoot  = Join-Path $Stage $ModName
$Data     = Join-Path $ModRoot 'Mod/Data'
$MusicOut = Join-Path $Data 'Sound/Music'
New-Item -ItemType Directory -Force -Path $MusicOut | Out-Null
New-Item -ItemType Directory -Force -Path $Dist | Out-Null

Copy-Item (Join-Path $Src "$ModName.module") (Join-Path $ModRoot "$ModName.module")
Copy-Item (Join-Path $Src 'pipeline.ini') (Join-Path $ModRoot 'pipeline.ini')

foreach ($token in $Factions.Keys) {
  $freq = $Factions[$token]
  $lc   = $token.ToLower()
  $tracks = @()

  $srcdir = Join-Path $MusicSrc $lc
  if (Test-Path $srcdir) {
    $i = 0
    Get-ChildItem -File $srcdir | Where-Object { $_.Extension -match '\.(mp3|wav|flac|ogg|m4a|aac)$' } | ForEach-Object {
      $i++
      $name = ('mod_{0}_{1:d2}' -f $lc, $i)
      Write-Host "==> [$token] converting $($_.Name) -> $name.wav"
      & ffmpeg -y -loglevel error -i $_.FullName -ar $Ar -ac 2 -sample_fmt s16 (Join-Path $MusicOut "$name.wav")
      $tracks += $name
    }
  }

  if ($tracks.Count -eq 0) {
    $name = "mod_${lc}_testtone"
    Write-Host "==> [$token] no source audio; generating test tone ${freq}Hz -> $name.wav"
    & ffmpeg -y -loglevel error -f lavfi -i "sine=frequency=${freq}:duration=12" `
      -af 'tremolo=f=4:d=0.6,volume=0.5' -ar $Ar -ac 2 -sample_fmt s16 (Join-Path $MusicOut "$name.wav")
    $tracks += $name
  }

  $pl = Join-Path $Data "SoundPlaylistFE_${token}.lua"
  $lines = @()
  $lines += "-- Faction Soundtrack: front-end (menu) playlist for ${token}"
  $lines += 'playlist ='
  $lines += '{'
  $lines += "`ttracks ="
  $lines += "`t{"
  foreach ($t in $tracks) { $lines += "`t`t`"$t`"," }
  $lines += "`t},"
  $lines += ''
  $lines += "`tsilence_min = 4.0,"
  $lines += "`tsilence_max = 12.0,"
  $lines += ''
  $lines += "`torder = false,"
  $lines += '}'
  Set-Content -Path $pl -Value $lines -Encoding ASCII
}

Write-Host '==> Packaging ZIP'
$Out = Join-Path $Dist "faction-soundtrack-v$Version.zip"
if (Test-Path $Out) { Remove-Item $Out }
Compress-Archive -Path $ModRoot -DestinationPath $Out

Write-Host ''
Write-Host "Built: $Out"
