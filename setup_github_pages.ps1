# Script to setup GitHub Pages
# This script helps configure index.html with your GitHub repository information

param(
    [string]$Username = "",
    [string]$RepoName = ""
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ChatList - GitHub Pages Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get repository info if not provided
if ([string]::IsNullOrEmpty($Username) -or [string]::IsNullOrEmpty($RepoName)) {
    Write-Host "Detecting GitHub repository..." -ForegroundColor Yellow
    
    # Try to get from git remote
    $remoteUrl = git remote get-url origin 2>$null
    if ($remoteUrl) {
        if ($remoteUrl -match 'github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$') {
            $detectedUsername = $matches[1]
            $detectedRepo = $matches[2] -replace '\.git$', ''
            
            Write-Host "Detected repository: $detectedUsername/$detectedRepo" -ForegroundColor Green
            
            if ([string]::IsNullOrEmpty($Username)) {
                $Username = $detectedUsername
            }
            if ([string]::IsNullOrEmpty($RepoName)) {
                $RepoName = $detectedRepo
            }
        }
    }
    
    # If still empty, ask user
    if ([string]::IsNullOrEmpty($Username)) {
        $Username = Read-Host "Enter your GitHub username"
    }
    if ([string]::IsNullOrEmpty($RepoName)) {
        $RepoName = Read-Host "Enter your repository name"
    }
}

Write-Host ""
Write-Host "Repository: $Username/$RepoName" -ForegroundColor Cyan
Write-Host ""

# Update index.html
if (Test-Path "index.html") {
    Write-Host "Updating index.html..." -ForegroundColor Yellow
    $content = Get-Content "index.html" -Raw -Encoding UTF8
    
    # Replace placeholders
    $content = $content -replace 'yourusername', $Username
    $content = $content -replace 'YOUR_USERNAME', $Username
    $content = $content -replace 'chatlist', $RepoName
    $content = $content -replace 'YOUR_REPO', $RepoName
    
    # Update version from version.py
    $version = python -c "from version import __version__; print(__version__)" 2>$null
    if ($version) {
        $version = $version.Trim()
        $content = $content -replace 'v1\.0\.0', "v$version"
        Write-Host "Updated version to: $version" -ForegroundColor Green
    }
    
    $content | Set-Content "index.html" -Encoding UTF8
    Write-Host "index.html updated successfully!" -ForegroundColor Green
} else {
    Write-Host "Error: index.html not found!" -ForegroundColor Red
    exit 1
}

# Ask about docs/ folder
Write-Host ""
$useDocs = Read-Host "Do you want to use docs/ folder for GitHub Pages? (y/N)"
if ($useDocs -eq 'y' -or $useDocs -eq 'Y') {
    if (-not (Test-Path "docs")) {
        New-Item -ItemType Directory -Path "docs" | Out-Null
    }
    Copy-Item "index.html" "docs\index.html" -Force
    Write-Host "Copied index.html to docs/" -ForegroundColor Green
    Write-Host ""
    Write-Host "GitHub Pages settings:" -ForegroundColor Cyan
    Write-Host "  Branch: main" -ForegroundColor Yellow
    Write-Host "  Folder: /docs" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "GitHub Pages settings:" -ForegroundColor Cyan
    Write-Host "  Branch: main" -ForegroundColor Yellow
    Write-Host "  Folder: / (root)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Commit and push index.html:" -ForegroundColor Yellow
Write-Host "   git add index.html" -ForegroundColor Gray
if ($useDocs -eq 'y' -or $useDocs -eq 'Y') {
    Write-Host "   git add docs/index.html" -ForegroundColor Gray
}
Write-Host "   git commit -m 'Add landing page for GitHub Pages'" -ForegroundColor Gray
Write-Host "   git push" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Configure GitHub Pages:" -ForegroundColor Yellow
Write-Host "   Go to: https://github.com/$Username/$RepoName/settings/pages" -ForegroundColor Gray
if ($useDocs -eq 'y' -or $useDocs -eq 'Y') {
    Write-Host "   Source: Branch 'main', Folder '/docs'" -ForegroundColor Gray
} else {
    Write-Host "   Source: Branch 'main', Folder '/ (root)'" -ForegroundColor Gray
}
Write-Host ""
Write-Host "3. Your site will be available at:" -ForegroundColor Yellow
Write-Host "   https://$Username.github.io/$RepoName/" -ForegroundColor Green
Write-Host ""

