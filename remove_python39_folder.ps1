# Script to remove Python 3.9 folder
# Run as Administrator

$python39Path = "C:\Program Files\Python39"

if (Test-Path $python39Path) {
    Write-Host "Found Python 3.9 folder at: $python39Path" -ForegroundColor Yellow
    Write-Host "Attempting to remove..." -ForegroundColor Yellow
    
    try {
        Remove-Item -Path $python39Path -Recurse -Force -ErrorAction Stop
        Write-Host "Python 3.9 folder removed successfully!" -ForegroundColor Green
    } catch {
        Write-Host "Error removing folder. You may need to:" -ForegroundColor Red
        Write-Host "1. Run PowerShell as Administrator" -ForegroundColor Yellow
        Write-Host "2. Or manually delete the folder: $python39Path" -ForegroundColor Yellow
        Write-Host "Error: $_" -ForegroundColor Red
    }
} else {
    Write-Host "Python 3.9 folder not found at: $python39Path" -ForegroundColor Green
}

