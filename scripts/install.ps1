param(
  [string]$Platform = "agents",
  [switch]$Force
)

$skillName = "gpt-series-reasoning-style"
$source = Split-Path -Parent $PSScriptRoot

$paths = @{
  agents    = Join-Path $env:USERPROFILE ".agents\skills\$skillName"
  codex     = Join-Path $env:USERPROFILE ".codex\skills\$skillName"
  claude    = Join-Path $env:USERPROFILE ".claude\skills\$skillName"
  cursor    = Join-Path (Get-Location) ".cursor\rules\$skillName"
  windsurf  = Join-Path (Get-Location) ".windsurf\rules\$skillName"
  cline     = Join-Path (Get-Location) ".clinerules\$skillName"
  gemini    = Join-Path $env:USERPROFILE ".gemini\skills\$skillName"
  kiro      = Join-Path $env:USERPROFILE ".kiro\skills\$skillName"
  trae      = Join-Path (Get-Location) ".trae\rules\$skillName"
  goose     = Join-Path $env:USERPROFILE ".config\goose\skills\$skillName"
  opencode  = Join-Path $env:USERPROFILE ".config\opencode\skills\$skillName"
  roo       = Join-Path (Get-Location) ".roo\rules\$skillName"
  antigravity = Join-Path $env:USERPROFILE ".agents\skills\$skillName"
}

if (-not $paths.ContainsKey($Platform)) {
  Write-Error "Unknown platform: $Platform"
  exit 1
}

$dest = $paths[$Platform]
if ((Test-Path -LiteralPath $dest) -and -not $Force) {
  Write-Error "Destination already exists: $dest. Use -Force to overwrite."
  exit 1
}

New-Item -ItemType Directory -Path (Split-Path -Parent $dest) -Force | Out-Null
if (Test-Path -LiteralPath $dest) {
  Remove-Item -LiteralPath $dest -Recurse -Force
}
New-Item -ItemType Directory -Path $dest -Force | Out-Null
Copy-Item -Path (Join-Path $source '*') -Destination $dest -Recurse -Force
Write-Output "Installed $skillName to $dest"
