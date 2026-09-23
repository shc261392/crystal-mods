# ---------------------------------------------------------------------------
# fps-boost - Space Marine 2 potato-mode config - uninstall (Windows 11)
#
# Reverts the OS-level changes deploy.ps1 applied (best effort):
#   - Windows power plan -> Balanced (High performance).
# No game files are touched.
# ---------------------------------------------------------------------------
[CmdletBinding()]
param()

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
if ($isAdmin) {
    powercfg /setactive 381b4222-f694-41f0-9685-ff5bb260df2e | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host 'Windows power plan -> Balanced (reverted).'
    } else {
        Write-Warning 'Could not revert power plan (run as Administrator).'
    }
} else {
    Write-Host 'Power plan not changed (run as Administrator to revert).'
}
Write-Host 'fps-boost deployed no game files, so nothing else to undo.'
Write-Host 'In-game rows: revert in Options -> Graphics if desired.'