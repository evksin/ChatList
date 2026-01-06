# Script to clean up Python 3.11 registration
# Run as Administrator

Write-Host "Cleaning up Python 3.11 registration..." -ForegroundColor Green

# Remove from user PATH (already done, but double-check)
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$userPathParts = $userPath -split ';' | Where-Object { 
    $_ -notlike "*Python311*" -and 
    $_ -notlike "*python311*" -and
    $_ -ne ""
}
$newUserPath = $userPathParts -join ';'
[Environment]::SetEnvironmentVariable("Path", $newUserPath, "User")
Write-Host "User PATH cleaned" -ForegroundColor Green

# Try to remove from registry (requires Admin)
try {
    $regPath = "HKLM:\SOFTWARE\Python\PythonCore\3.11"
    if (Test-Path $regPath) {
        Write-Host "Found Python 3.11 in registry. Attempting to remove..." -ForegroundColor Yellow
        Remove-Item -Path $regPath -Recurse -Force -ErrorAction Stop
        Write-Host "Python 3.11 registry entry removed" -ForegroundColor Green
    } else {
        Write-Host "Python 3.11 not found in registry" -ForegroundColor Green
    }
} catch {
    Write-Host "Could not remove from registry. You may need Administrator rights." -ForegroundColor Yellow
    Write-Host "Error: $_" -ForegroundColor Yellow
}

# Check for Python 3.11 in AppData
$possiblePaths = @(
    "$env:LOCALAPPDATA\Programs\Python\Python311",
    "$env:APPDATA\Python\Python311",
    "C:\Program Files\Python311",
    "C:\Program Files (x86)\Python311"
)

foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        Write-Host "`nFound Python 3.11 at: $path" -ForegroundColor Yellow
        Write-Host "You can manually delete this folder if needed." -ForegroundColor Yellow
    }
}

Write-Host "`nDone! Python 3.11 should be removed from py launcher after system restart." -ForegroundColor Green
Write-Host "To verify, restart PowerShell and run: py -0p" -ForegroundColor Cyan

