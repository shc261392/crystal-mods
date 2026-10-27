#!/usr/bin/env pwsh
# Warpstorm — Windows entry point for the release build.
#
# There is ONE release recipe (AGENTS.md rule 15): package.sh, run by `make build`.
# This wrapper only runs that same script through bash (WSL or Git Bash), so a
# Windows build produces the identical dist\warpstorm-v<ver>.zip.
$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path

$bash = Get-Command bash -ErrorAction SilentlyContinue
if (-not $bash) {
  throw "bash not found. Install WSL or Git for Windows, then run: make build"
}
Push-Location $Here
try {
  & $bash.Source ./package.sh
  if ($LASTEXITCODE -ne 0) { throw "package.sh failed ($LASTEXITCODE)" }
}
finally {
  Pop-Location
}
