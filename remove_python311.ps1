# Script to remove Python 3.11 paths from PATH and folder
# Run as Administrator if needed

Write-Host "Removing Python 3.11..." -ForegroundColor Green

# Get current user PATH
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
Write-Host "`nCurrent user PATH:" -ForegroundColor Yellow

# Remove Python 3.11 paths from user PATH
$userPathParts = $userPath -split ';' | Where-Object { 
    $_ -notlike "*Python311*" -and 
    $_ -notlike "*python311*" -and
    $_ -ne ""
}
$newUserPath = $userPathParts -join ';'

# Set new user PATH
[Environment]::SetEnvironmentVariable("Path", $newUserPath, "User")
Write-Host "Python 3.11 paths removed from user PATH" -ForegroundColor Green

# Check system PATH
$systemPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
if ($systemPath) {
    $systemPathParts = $systemPath -split ';' | Where-Object { 
        $_ -notlike "*Python311*" -and 
        $_ -notlike "*python311*" -and
        $_ -ne ""
    }
    $newSystemPath = $systemPathParts -join ';'
    
    try {
        [Environment]::SetEnvironmentVariable("Path", $newSystemPath, "Machine")
        Write-Host "Python 3.11 paths removed from system PATH" -ForegroundColor Green
    } catch {
        Write-Host "Could not update system PATH. You may need Administrator rights." -ForegroundColor Yellow
    }
}

# Try to remove Python 3.11 folder
$python311Path = "$env:LOCALAPPDATA\Programs\Python\Python311"
if (Test-Path $python311Path) {
    Write-Host "`nFound Python 3.11 folder at: $python311Path" -ForegroundColor Yellow
    Write-Host "Attempting to remove..." -ForegroundColor Yellow
    
    try {
        Remove-Item -Path $python311Path -Recurse -Force -ErrorAction Stop
        Write-Host "Python 3.11 folder removed successfully!" -ForegroundColor Green
    } catch {
        Write-Host "Could not remove folder automatically. Error: $_" -ForegroundColor Yellow
        Write-Host "You may need to:" -ForegroundColor Yellow
        Write-Host "1. Run PowerShell as Administrator" -ForegroundColor Yellow
        Write-Host "2. Or manually delete: $python311Path" -ForegroundColor Yellow
    }
} else {
    Write-Host "`nPython 3.11 folder not found at: $python311Path" -ForegroundColor Green
}

Write-Host "`nDone! Please restart PowerShell for changes to take effect." -ForegroundColor Green
Write-Host "After restart, verify with: py -0p" -ForegroundColor Cyan

