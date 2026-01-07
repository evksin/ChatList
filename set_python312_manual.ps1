# Manual commands to set Python 3.12 as default
# Run these commands one by one in PowerShell

# Get current user PATH
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")

# Add Python 3.12 to the beginning
$python312 = "C:\Users\777\AppData\Local\Programs\Python\Python312"
$python312Scripts = "C:\Users\777\AppData\Local\Programs\Python\Python312\Scripts"

# Remove Python 3.9 if exists
$pathArray = $userPath -split ';' | Where-Object { $_ -notlike "*Python39*" }

# Add Python 3.12 at the beginning
$newPath = "$python312;$python312Scripts;" + ($pathArray -join ';')

# Set the new PATH
[Environment]::SetEnvironmentVariable("Path", $newPath, "User")

Write-Host "Python 3.12 set as default!" -ForegroundColor Green
Write-Host "Restart PowerShell and run: python --version" -ForegroundColor Yellow


