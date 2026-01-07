# Script to create GitHub Release automatically
# Requires GitHub CLI (gh) to be installed: winget install GitHub.cli

param(
    [switch]$DryRun = $false
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ChatList - Create GitHub Release" -ForegroundColor Cyan
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

# Check if GitHub CLI is installed
$ghInstalled = Get-Command gh -ErrorAction SilentlyContinue
if (-not $ghInstalled) {
    Write-Host "Error: GitHub CLI (gh) is not installed!" -ForegroundColor Red
    Write-Host "Install it with: winget install GitHub.cli" -ForegroundColor Yellow
    Write-Host "Or download from: https://cli.github.com/" -ForegroundColor Yellow
    exit 1
}

# Check if user is authenticated
Write-Host "Checking GitHub authentication..." -ForegroundColor Yellow
$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Not authenticated with GitHub!" -ForegroundColor Red
    Write-Host "Run: gh auth login" -ForegroundColor Yellow
    exit 1
}
Write-Host "Authenticated" -ForegroundColor Green
Write-Host ""

# Check if files exist
$installerPath = "installer\ChatList-Setup-v$version.exe"
$exePath = "dist\ChatList-v$version.exe"

if (-not (Test-Path $installerPath)) {
    Write-Host "Error: Installer not found: $installerPath" -ForegroundColor Red
    Write-Host "Please build the installer first using: .\build_installer.ps1" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path $exePath)) {
    Write-Host "Warning: Executable not found: $exePath" -ForegroundColor Yellow
    Write-Host "Only installer will be uploaded" -ForegroundColor Yellow
    $exePath = $null
}

# Check if release notes template exists
$releaseNotesPath = "RELEASE_NOTES_TEMPLATE.md"
if (-not (Test-Path $releaseNotesPath)) {
    Write-Host "Warning: Release notes template not found: $releaseNotesPath" -ForegroundColor Yellow
    $releaseNotes = "Release version $version"
} else {
    $releaseNotes = Get-Content $releaseNotesPath -Raw -Encoding UTF8
    # Replace version placeholder if exists
    $releaseNotes = $releaseNotes -replace 'v1\.0\.0', "v$version"
}

# Check if tag already exists
Write-Host "Checking if tag v$version exists..." -ForegroundColor Yellow
$tagExists = git tag -l "v$version"
if ($tagExists) {
    Write-Host "Tag v$version already exists" -ForegroundColor Yellow
    $createTag = $false
} else {
    Write-Host "Tag v$version does not exist, will be created" -ForegroundColor Cyan
    $createTag = $true
}

# Check if release already exists
$releaseExists = gh release view "v$version" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Warning: Release v$version already exists!" -ForegroundColor Yellow
    $overwrite = Read-Host "Do you want to delete and recreate it? (y/N)"
    if ($overwrite -eq 'y' -or $overwrite -eq 'Y') {
        Write-Host "Deleting existing release..." -ForegroundColor Yellow
        if (-not $DryRun) {
            gh release delete "v$version" --yes
        }
    } else {
        Write-Host "Aborted" -ForegroundColor Yellow
        exit 0
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Release Information" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Version: v$version" -ForegroundColor Green
Write-Host "Installer: $installerPath" -ForegroundColor Cyan
if ($exePath) {
    Write-Host "Executable: $exePath" -ForegroundColor Cyan
}
Write-Host "Create tag: $createTag" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "DRY RUN MODE - No changes will be made" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Would execute:" -ForegroundColor Yellow
    if ($createTag) {
        Write-Host "  git tag -a v$version -m `"Release version $version`"" -ForegroundColor Gray
        Write-Host "  git push origin v$version" -ForegroundColor Gray
    }
    Write-Host "  gh release create v$version ..." -ForegroundColor Gray
    exit 0
}

# Create tag if needed
if ($createTag) {
    Write-Host "Creating tag v$version..." -ForegroundColor Yellow
    git tag -a "v$version" -m "Release version $version"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to create tag" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Pushing tag to GitHub..." -ForegroundColor Yellow
    git push origin "v$version"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to push tag" -ForegroundColor Red
        exit 1
    }
    Write-Host "Tag created and pushed" -ForegroundColor Green
    Write-Host ""
}

# Create release
Write-Host "Creating GitHub release..." -ForegroundColor Yellow
$files = @($installerPath)
if ($exePath) {
    $files += $exePath
}

$filesArg = $files -join "`" `""
$command = "gh release create `"v$version`" `"$filesArg`" --title `"ChatList v$version`" --notes `"$releaseNotes`""

Write-Host "Executing: $command" -ForegroundColor Gray
Invoke-Expression $command

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  Release Created Successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Release URL:" -ForegroundColor Cyan
    Write-Host "  https://github.com/$(gh repo view --json owner,name -q '.owner.login + '/' + .name')/releases/tag/v$version" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "Error: Failed to create release" -ForegroundColor Red
    exit 1
}

