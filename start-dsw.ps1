$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
  Copy-Item ".env.example" ".env"
  Write-Host "Created .env from .env.example. Add API keys later if needed."
}

$port = "8765"
if (Test-Path ".env") {
  Get-Content ".env" | ForEach-Object {
    if ($_ -match "^\s*PORT\s*=\s*(.+)\s*$") {
      $script:port = $Matches[1].Trim().Trim('"').Trim("'")
    }
  }
}

$url = "http://127.0.0.1:$port/"
Write-Host "Opening $url"
Start-Process $url

if (Get-Command py -ErrorAction SilentlyContinue) {
  py -3 server.py
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
  python server.py
} else {
  Write-Error "Python is not installed. Install Python 3.11+ from https://www.python.org/downloads/"
}
