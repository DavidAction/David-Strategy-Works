$ErrorActionPreference = "Stop"

$Root = Split-Path $PSScriptRoot -Parent
$EnvPath = Join-Path $Root ".env"
$ExamplePath = Join-Path $Root ".env.example"

if (-not (Test-Path $EnvPath)) {
  if (Test-Path $ExamplePath) {
    Copy-Item $ExamplePath $EnvPath
  } else {
    New-Item -ItemType File -Path $EnvPath | Out-Null
  }
}

function Convert-SecretToPlainText {
  param([Security.SecureString]$Secret)
  if (-not $Secret -or $Secret.Length -eq 0) { return "" }
  $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Secret)
  try {
    return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
  } finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
  }
}

function Normalize-ApiKey {
  param(
    [string]$Name,
    [string]$Value
  )
  $clean = ($Value -replace "`r", "" -replace "`n", "").Trim().Trim('"').Trim("'")
  if ($clean.Contains("=")) {
    $clean = $clean.Substring($clean.IndexOf("=") + 1).Trim().Trim('"').Trim("'")
  }
  if ($Name -eq "OPENAI_API_KEY" -and $clean -match "(sk-[A-Za-z0-9_\-]+)") {
    return $Matches[1]
  }
  if ($Name -eq "ANTHROPIC_API_KEY" -and $clean -match "(sk-ant-[A-Za-z0-9_\-]+)") {
    return $Matches[1]
  }
  if ($Name -eq "GEMINI_API_KEY") {
    if ($clean -match "(AIza[A-Za-z0-9_\-]+)") { return $Matches[1] }
    if ($clean -match "(AQ\.[A-Za-z0-9_\-]+)") { return $Matches[1] }
  }
  return $clean
}

function Set-EnvLine {
  param(
    [string[]]$Lines,
    [string]$Name,
    [string]$Value
  )
  $pattern = "^\s*$([regex]::Escape($Name))\s*="
  $updated = $false
  $next = foreach ($line in $Lines) {
    if ($line -match $pattern) {
      $updated = $true
      "$Name=$Value"
    } else {
      $line
    }
  }
  if (-not $updated) {
    $next += "$Name=$Value"
  }
  return $next
}

$lines = @()
if (Test-Path $EnvPath) {
  $lines = @(Get-Content $EnvPath)
}

$keys = @("GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY")
$status = @{}

foreach ($name in $keys) {
  $current = ($lines | Where-Object { $_ -match "^\s*$([regex]::Escape($name))\s*=" } | Select-Object -First 1)
  $currentSet = $false
  if ($current) {
    $currentValue = $current.Substring($current.IndexOf("=") + 1).Trim()
    $currentSet = -not [string]::IsNullOrWhiteSpace($currentValue)
  }
  $suffix = if ($currentSet) { "leave blank to keep existing" } else { "required for live check" }
  $secret = Read-Host "$name ($suffix)" -AsSecureString
  $plain = Convert-SecretToPlainText $secret
  if ([string]::IsNullOrWhiteSpace($plain)) {
    $status[$name] = $currentSet
    continue
  }
  $normalized = Normalize-ApiKey -Name $name -Value $plain
  $lines = Set-EnvLine -Lines $lines -Name $name -Value $normalized
  $status[$name] = -not [string]::IsNullOrWhiteSpace($normalized)
}

Set-Content -Path $EnvPath -Value $lines -Encoding UTF8

Write-Host "Updated local .env. Key presence:"
foreach ($name in $keys) {
  Write-Host ("- {0}: {1}" -f $name, $(if ($status[$name]) { "set" } else { "not set" }))
}
Write-Host "Next: restart the local server, then run python tools\ai_live_check.py"
