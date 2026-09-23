# ---------------------------------------------------------------------------
# fps-boost - apply CPU-core aggression to a running Space Marine 2 (Windows)
#
# Pins the game to the physical cores (disabling SMT usage for it) and raises
# its priority. This is the AMD analogue of the OC3D finding that disabling
# Intel E-cores improved Space Marine 2 CPU throughput. Keeps public
# matchmaking (it is OS-level, invisible to the game / EAC).
#
# Usage (admin PowerShell):
#   .\scripts\apply-affinity.ps1 [-Name "Warhammer 40000 Space Marine 2 - Retail"]
#                                [-Mask 0x5555]
#
# Mask: bit i = allow CPU i. On a Ryzen 5800X with SMT siblings numbered as
# adjacent pairs (0,1),(2,3),... the physical cores are 0,2,4,...,14 = 0x5555.
# Verify your mapping in Task Manager -> Performance -> CPU (logical
# processors) before assuming; pass -Mask to override.
# ---------------------------------------------------------------------------
[CmdletBinding()]
param(
    [string]$Name = "Warhammer 40000 Space Marine 2 - Retail",
    [int64]$Mask = 0x5555
)

$proc = Get-Process -Name $Name -ErrorAction SilentlyContinue
if (-not $proc) {
    Write-Host "Game not running ('$Name'). Start the game, wait for the main menu, then re-run this." -ForegroundColor Yellow
    exit 1
}

$old = $proc.ProcessorAffinity
try {
    $proc.ProcessorAffinity = $Mask
    $proc.PriorityClass = 'High'
    Write-Host "Applied CPU affinity mask 0x$('{0:X}' -f $Mask) (physical cores) + High priority to PID $($proc.Id)."
    Write-Host "Previous mask: 0x$('{0:X}' -f $old)"
} catch {
    Write-Host "Failed to set affinity (need Administrator PowerShell?): $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}