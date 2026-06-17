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

if ($UseChocolatey) {
  if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    throw "Chocolatey is not installed. Install Chocolatey first, or install Tesseract and Poppler manually."
  }
  choco install tesseract poppler -y --no-progress
}

$tesseract = Get-Command tesseract -ErrorAction SilentlyContinue
$pdftoppm = Get-Command pdftoppm -ErrorAction SilentlyContinue

if (-not $tesseract) {
  $candidate = "C:\Program Files\Tesseract-OCR\tesseract.exe"
  if (Test-Path $candidate) {
    $tesseract = Get-Item $candidate
  }
}

if (-not $pdftoppm) {
  $candidate = "C:\ProgramData\chocolatey\bin\pdftoppm.exe"
  if (Test-Path $candidate) {
    $pdftoppm = Get-Item $candidate
  }
}

$tesseractPath = ""
if ($tesseract) {
  if ($tesseract.Source) { $tesseractPath = $tesseract.Source } else { $tesseractPath = $tesseract.FullName }
}

$pdftoppmPath = ""
if ($pdftoppm) {
  if ($pdftoppm.Source) { $pdftoppmPath = $pdftoppm.Source } else { $pdftoppmPath = $pdftoppm.FullName }
}

Write-Host "Tesseract:" $tesseractPath
Write-Host "pdftoppm:" $pdftoppmPath
Write-Host "Next, run: python tools\ocr_check.py --require-ocr"
