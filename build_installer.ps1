# Script to build installer using Inno Setup
# Requires Inno Setup to be installed: https://jrsoftware.org/isinfo.php

Write-Host "Building ChatList installer..." -ForegroundColor Green

# Get version from version.py
Write-Host "`nReading version..." -ForegroundColor Yellow
$version = python -c "from version import __version__; print(__version__)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Could not read version from version.py" -ForegroundColor Red
    exit 1
}
$version = $version.Trim()
Write-Host "Version: $version" -ForegroundColor Cyan

# Check if executable exists
$exeName = "ChatList-v$version"
$exePath = "dist\$exeName.exe"
if (-not (Test-Path $exePath)) {
    Write-Host "`nError: Executable not found: $exePath" -ForegroundColor Red
    Write-Host "Please build the executable first using: .\build.ps1" -ForegroundColor Yellow
    exit 1
}

# Check if Inno Setup is installed
$innoSetupPath = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $innoSetupPath)) {
    $innoSetupPath = "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
}
if (-not (Test-Path $innoSetupPath)) {
    Write-Host "`nError: Inno Setup not found!" -ForegroundColor Red
    Write-Host "Please install Inno Setup from: https://jrsoftware.org/isinfo.php" -ForegroundColor Yellow
    Write-Host "Expected path: $innoSetupPath" -ForegroundColor Yellow
    exit 1
}

Write-Host "`nFound Inno Setup: $innoSetupPath" -ForegroundColor Green

# Update setup.iss with current version
Write-Host "`nUpdating setup.iss with version $version..." -ForegroundColor Yellow
$setupIss = Get-Content "setup.iss" -Raw -Encoding UTF8

# Replace version in setup.iss
$setupIss = $setupIss -replace '#define MyAppVersion ".*"', "#define MyAppVersion `"$version`""
$setupIss = $setupIss -replace '#define MyAppExeName ".*"', "#define MyAppExeName `"$exeName.exe`""

# Create temporary setup file
$tempSetupIss = "setup_temp.iss"
$setupIss | Set-Content $tempSetupIss -Encoding UTF8

# Create installer directory
if (-not (Test-Path "installer")) {
    New-Item -ItemType Directory -Path "installer" | Out-Null
}

# Build installer
Write-Host "`nBuilding installer..." -ForegroundColor Green
& $innoSetupPath $tempSetupIss

# Cleanup
if (Test-Path $tempSetupIss) {
    Remove-Item $tempSetupIss
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nInstaller built successfully!" -ForegroundColor Green
    Write-Host "Installer location: installer\ChatList-Setup-v$version.exe" -ForegroundColor Cyan
} else {
    Write-Host "`nBuild error!" -ForegroundColor Red
    exit 1
}

