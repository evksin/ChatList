# Script to build executable file
# Make sure all dependencies are installed: pip install -r requirements.txt

Write-Host "Starting build process..." -ForegroundColor Green

# Install dependencies
Write-Host "`nChecking dependencies..." -ForegroundColor Yellow
$env:HTTP_PROXY=''; $env:HTTPS_PROXY=''; $env:NO_PROXY='*'
pip install -r requirements.txt

# Clean previous builds
Write-Host "`nCleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
    Write-Host "Removed build folder" -ForegroundColor Yellow
}

if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist"
    Write-Host "Removed dist folder" -ForegroundColor Yellow
}

# Remove old .spec file (optional, for clean build)
if (Test-Path "PyQtApp.spec") {
    Remove-Item -Force "PyQtApp.spec"
    Write-Host "Removed old .spec file" -ForegroundColor Yellow
}

# Build executable file
# --onefile - creates single executable file
# --windowed - hides console window (for GUI applications)
# --name - output file name
# --hidden-import - explicitly specify hidden imports
Write-Host "`nStarting build..." -ForegroundColor Green
pyinstaller --onefile --windowed --name "ChatList" --hidden-import=markdown --hidden-import=dotenv main.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nBuild completed successfully!" -ForegroundColor Green
    Write-Host "Executable file is located in: dist\ChatList.exe" -ForegroundColor Cyan
} else {
    Write-Host "`nBuild error!" -ForegroundColor Red
}
