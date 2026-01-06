# Script to set Python 3.12 as default version
# Run as Administrator

Write-Host "Setting Python 3.12 as default version..." -ForegroundColor Green

# Path to Python 3.12
$python312Path = "C:\Users\777\AppData\Local\Programs\Python\Python312"
$python312ScriptsPath = "$python312Path\Scripts"

# Get current PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

# Check if Python 3.12 is already in PATH
if ($currentPath -notlike "*$python312Path*") {
    Write-Host "Adding Python 3.12 to user PATH..." -ForegroundColor Yellow
    
    # Add Python 3.12 to the beginning of PATH
    $newPath = "$python312Path;$python312ScriptsPath;$currentPath"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    
    Write-Host "Python 3.12 added to PATH" -ForegroundColor Green
} else {
    Write-Host "Python 3.12 is already in PATH" -ForegroundColor Cyan
}

# Remove Python 3.9 from user PATH (if exists)
$python39Path = "C:\Program Files\Python39"
if ($currentPath -like "*$python39Path*") {
    Write-Host "Removing Python 3.9 from user PATH..." -ForegroundColor Yellow
    
    # Remove Python 3.9 paths
    $pathParts = $currentPath -split ';' | Where-Object { $_ -notlike "*$python39Path*" }
    $newPath = $pathParts -join ';'
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    
    Write-Host "Python 3.9 removed from user PATH" -ForegroundColor Green
}

# Check system PATH (requires admin rights)
$systemPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
if ($systemPath -like "*$python39Path*") {
    Write-Host ""
    Write-Host "WARNING: Python 3.9 found in system PATH!" -ForegroundColor Yellow
    Write-Host "Admin rights required to remove it." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Remove from system PATH? (Y/N): " -ForegroundColor Yellow -NoNewline
    
    $response = Read-Host
    if ($response -eq 'Y' -or $response -eq 'y') {
        $systemPathParts = $systemPath -split ';' | Where-Object { $_ -notlike "*$python39Path*" }
        $newSystemPath = $systemPathParts -join ';'
        [Environment]::SetEnvironmentVariable("Path", $newSystemPath, "Machine")
        Write-Host "Python 3.9 removed from system PATH" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANT: Restart PowerShell or Command Prompt for changes to take effect." -ForegroundColor Yellow
Write-Host "After restart, check: python --version" -ForegroundColor Cyan
