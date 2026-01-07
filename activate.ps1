# Script to activate virtual environment in PowerShell
# Usage: .\activate.ps1

if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Green
    & "venv\Scripts\Activate.ps1"
    Write-Host "Virtual environment activated!" -ForegroundColor Green
    Write-Host "Python version:" -ForegroundColor Yellow
    python --version
    Write-Host "To deactivate, run: deactivate" -ForegroundColor Cyan
} else {
    Write-Host "Error: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please create it first with: py -3.12 -m venv venv" -ForegroundColor Yellow
}

