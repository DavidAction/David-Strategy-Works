$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Write-Error "Git is not installed. Install Git from https://git-scm.com/downloads or download the repository ZIP from GitHub."
}

git pull --ff-only
Write-Host "David Strategy Works is up to date."
