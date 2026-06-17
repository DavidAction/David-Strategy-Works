param(
  [bool]$UseChocolatey = $true
)

$ErrorActionPreference = "Stop"

function Assert-Admin {
  $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
  $principal = New-Object Security.Principal.WindowsPrincipal($identity)
  if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "Run this script from an Administrator PowerShell window."
  }
}

Assert-Admin

function Resolve-Executable {
  param(
    [string]$Command,
    [string[]]$Candidates,
    [string[]]$SearchRoots,
    [string]$ExecutableName
  )
  $cmd = Get-Command $Command -ErrorAction SilentlyContinue
  if ($cmd) {
    if ($cmd.Source) { return $cmd.Source }
    if ($cmd.Path) { return $cmd.Path }
  }
  foreach ($candidate in $Candidates) {
    if ($candidate -and (Test-Path $candidate)) { return $candidate }
  }
  foreach ($root in $SearchRoots) {
    if (-not (Test-Path $root)) { continue }
    $match = Get-ChildItem $root -Recurse -Filter $ExecutableName -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($match) { return $match.FullName }
  }
  return ""
}

function Install-KoreanTessdata {
  param([string]$TesseractPath)
  if (-not $TesseractPath) { return }
  $tessdata = Join-Path (Split-Path $TesseractPath -Parent) "tessdata"
  if (-not (Test-Path $tessdata)) {
    New-Item -ItemType Directory -Path $tessdata | Out-Null
  }
  $korPath = Join-Path $tessdata "kor.traineddata"
  if (-not (Test-Path $korPath)) {
    $url = "https://github.com/tesseract-ocr/tessdata/raw/main/kor.traineddata"
    Write-Host "Downloading Korean tessdata..."
    Invoke-WebRequest -Uri $url -OutFile $korPath -UseBasicParsing
  }
}

function Install-PopplerBinary {
  $existing = Resolve-Executable `
    -Command "pdftoppm" `
    -Candidates @(
      "C:\ProgramData\chocolatey\bin\pdftoppm.exe",
      "C:\tools\poppler\bin\pdftoppm.exe",
      "C:\tools\poppler\Library\bin\pdftoppm.exe",
      "C:\Program Files\poppler\Library\bin\pdftoppm.exe",
      "C:\Program Files\poppler\bin\pdftoppm.exe"
    ) `
    -SearchRoots @("C:\tools\poppler", "C:\Program Files\poppler", "C:\ProgramData\chocolatey\lib\poppler") `
    -ExecutableName "pdftoppm.exe"
  if ($existing) { return $existing }

  Write-Host "Downloading Poppler Windows binary..."
  $release = Invoke-RestMethod -Uri "https://api.github.com/repos/oschwartz10612/poppler-windows/releases/latest" -UseBasicParsing
  $asset = $release.assets | Where-Object { $_.name -like "*.zip" -and $_.name -like "*Release*" } | Select-Object -First 1
  if (-not $asset) {
    $asset = $release.assets | Where-Object { $_.name -like "*.zip" } | Select-Object -First 1
  }
  if (-not $asset) {
    throw "Could not find a Poppler Windows zip asset in the latest GitHub release."
  }
  $installRoot = "C:\tools\poppler"
  $zipPath = Join-Path $env:TEMP $asset.name
  if (-not (Test-Path "C:\tools")) {
    New-Item -ItemType Directory -Path "C:\tools" | Out-Null
  }
  if (-not (Test-Path $installRoot)) {
    New-Item -ItemType Directory -Path $installRoot | Out-Null
  }
  Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zipPath -UseBasicParsing
  Expand-Archive -LiteralPath $zipPath -DestinationPath $installRoot -Force
  $installed = Resolve-Executable `
    -Command "pdftoppm" `
    -Candidates @(
      "C:\tools\poppler\bin\pdftoppm.exe",
      "C:\tools\poppler\Library\bin\pdftoppm.exe"
    ) `
    -SearchRoots @($installRoot) `
    -ExecutableName "pdftoppm.exe"
  return $installed
}

if ($UseChocolatey) {
  if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    throw "Chocolatey is not installed. Install Chocolatey first, or install Tesseract and Poppler manually."
  }
  choco install tesseract -y --no-progress
  choco install poppler -y --no-progress
}

$tesseractPath = Resolve-Executable `
  -Command "tesseract" `
  -Candidates @(
    "C:\Program Files\Tesseract-OCR\tesseract.exe",
    "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    "C:\tools\tesseract\tesseract.exe"
  ) `
  -SearchRoots @("C:\Program Files\Tesseract-OCR", "C:\tools\tesseract") `
  -ExecutableName "tesseract.exe"

Install-KoreanTessdata -TesseractPath $tesseractPath
$pdftoppmPath = Install-PopplerBinary

Write-Host "Tesseract:" $tesseractPath
Write-Host "pdftoppm:" $pdftoppmPath
Write-Host "Next, run: python tools\ocr_check.py --require-ocr"
