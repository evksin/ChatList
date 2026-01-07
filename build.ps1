# Script to build executable file
# Make sure all dependencies are installed: pip install -r requirements.txt

Write-Host "Starting build process..." -ForegroundColor Green

# Get version from version.py
Write-Host "`nReading version..." -ForegroundColor Yellow
$version = python -c "from version import __version__; print(__version__)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Could not read version from version.py" -ForegroundColor Red
    exit 1
}
$version = $version.Trim()
Write-Host "Version: $version" -ForegroundColor Cyan

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

# Remove old .spec files (optional, for clean build)
Get-ChildItem -Path . -Filter "*.spec" | ForEach-Object {
    Remove-Item -Force $_.FullName
    Write-Host "Removed old .spec file: $($_.Name)" -ForegroundColor Yellow
}

# Build executable file
# --onefile - creates single executable file
# --windowed - hides console window (for GUI applications)
# --name - output file name (includes version)
# --icon - path to icon file
# --hidden-import - explicitly specify hidden imports
Write-Host "`nStarting build..." -ForegroundColor Green
$exeName = "ChatList-v$version"
pyinstaller --onefile --windowed --name $exeName --icon=app.ico --hidden-import=markdown --hidden-import=dotenv --hidden-import=version main.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nBuild completed successfully!" -ForegroundColor Green
    Write-Host "Executable file is located in: dist\$exeName.exe" -ForegroundColor Cyan
} else {
    Write-Host "`nBuild error!" -ForegroundColor Red
}
