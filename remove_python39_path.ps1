# Script to remove Python 3.9 paths from PATH environment variable
# Run as Administrator if needed

Write-Host "Removing Python 3.9 paths from PATH..." -ForegroundColor Green

# Get current user PATH
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
Write-Host "`nCurrent user PATH:" -ForegroundColor Yellow
Write-Host $userPath

# Remove Python 3.9 paths from user PATH
$userPathParts = $userPath -split ';' | Where-Object { 
    $_ -notlike "*Python39*" -and 
    $_ -notlike "*python39*" -and
    $_ -ne ""
}
$newUserPath = $userPathParts -join ';'

# Set new user PATH
[Environment]::SetEnvironmentVariable("Path", $newUserPath, "User")
Write-Host "`nUpdated user PATH:" -ForegroundColor Green
Write-Host $newUserPath

# Check system PATH (requires Administrator)
$systemPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
if ($systemPath) {
    Write-Host "`nCurrent system PATH:" -ForegroundColor Yellow
    Write-Host $systemPath
    
    $systemPathParts = $systemPath -split ';' | Where-Object { 
        $_ -notlike "*Python39*" -and 
        $_ -notlike "*python39*" -and
        $_ -ne ""
    }
    $newSystemPath = $systemPathParts -join ';'
    
    Write-Host "`nDo you want to remove Python 3.9 from SYSTEM PATH? (Y/N): " -ForegroundColor Yellow -NoNewline
    $response = Read-Host
    if ($response -eq 'Y' -or $response -eq 'y') {
        try {
            [Environment]::SetEnvironmentVariable("Path", $newSystemPath, "Machine")
            Write-Host "System PATH updated successfully." -ForegroundColor Green
        } catch {
            Write-Host "Error updating system PATH. You may need to run as Administrator." -ForegroundColor Red
            Write-Host "Error: $_" -ForegroundColor Red
        }
    }
}

Write-Host "`nDone! Please restart PowerShell for changes to take effect." -ForegroundColor Green
Write-Host "After restart, verify with: python --version" -ForegroundColor Cyan

