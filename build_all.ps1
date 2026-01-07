# Script to build executable and installer in one go
# This script automates the complete build process

param(
    [switch]$SkipInstaller = $false,
    [switch]$SkipBuild = $false
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ChatList - Complete Build Process" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get version from version.py
Write-Host "Reading version..." -ForegroundColor Yellow
$version = python -c "from version import __version__; print(__version__)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Could not read version from version.py" -ForegroundColor Red
    exit 1
}
$version = $version.Trim()
Write-Host "Version: $version" -ForegroundColor Green
Write-Host ""

# Step 1: Build executable
if (-not $SkipBuild) {
    Write-Host "Step 1: Building executable..." -ForegroundColor Cyan
    Write-Host "----------------------------------------" -ForegroundColor Cyan
    & .\build.ps1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`nError: Build failed!" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
} else {
    Write-Host "Step 1: Skipped (executable build)" -ForegroundColor Yellow
    Write-Host ""
}

# Step 2: Build installer
if (-not $SkipInstaller) {
    Write-Host "Step 2: Building installer..." -ForegroundColor Cyan
    Write-Host "----------------------------------------" -ForegroundColor Cyan
    & .\build_installer.ps1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`nError: Installer build failed!" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
} else {
    Write-Host "Step 2: Skipped (installer build)" -ForegroundColor Yellow
    Write-Host ""
}

# Summary
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Build Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Executable: dist\ChatList-v$version.exe" -ForegroundColor Cyan
if (-not $SkipInstaller) {
    Write-Host "Installer:  installer\ChatList-Setup-v$version.exe" -ForegroundColor Cyan
}
Write-Host ""

