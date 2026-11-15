#Requires -Version 5.1
<#
.SYNOPSIS
  Build MCPBridge.dll for Navisworks 2025, 2026 or 2027.

.DESCRIPTION
  The addin compiles against the Navisworks API files in your Navisworks
  install folder. Those files are not in this repository. Needs the .NET SDK
  and Navisworks Manage for the chosen year.

  Output: dist\<Year>\MCPBridge.dll with a SHA256SUMS file.
  Install it with .\Install.ps1 -Year <Year>.

.PARAMETER Year
  2025, 2026 or 2027. Default 2027.

.PARAMETER NavisworksInstallDir
  Override the install folder when Navisworks is in a custom location.

.EXAMPLE
  .\Build.ps1 -Year 2026
#>
[CmdletBinding()]
param(
    [ValidateSet(2025, 2026, 2027)][int]$Year = 2027,
    [string]$NavisworksInstallDir
)
$ErrorActionPreference = 'Stop'

if (-not $NavisworksInstallDir) {
    $NavisworksInstallDir = Join-Path $env:ProgramFiles "Autodesk\Navisworks Manage $Year"
}
$api = Join-Path $NavisworksInstallDir 'Autodesk.Navisworks.Api.dll'
if (-not (Test-Path -LiteralPath $api)) {
    throw "Autodesk.Navisworks.Api.dll not found in '$NavisworksInstallDir'. Install Navisworks Manage $Year or pass -NavisworksInstallDir."
}
if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) {
    throw 'The .NET SDK is required. Install it from https://dotnet.microsoft.com/download and try again.'
}

$out = Join-Path $PSScriptRoot "dist\$Year"
New-Item -ItemType Directory -Force $out | Out-Null

Write-Host "Building for Navisworks Manage $Year ..."
& dotnet build (Join-Path $PSScriptRoot 'NavisworksMcpAddin.csproj') -c Release `
    "-p:NavisworksInstallDir=$NavisworksInstallDir" "-p:NavisworksYear=$Year" "-o:$out"
if ($LASTEXITCODE -ne 0) {
    throw "Build failed for $Year. If the errors name an API member, that year's Navisworks API differs. Open an issue with the first error."
}

$dll = Join-Path $out 'MCPBridge.dll'
if (-not (Test-Path -LiteralPath $dll)) { throw "Build finished but $dll is missing." }

$lines = foreach ($n in 'MCPBridge.dll', 'MCPBridge.pdb') {
    $p = Join-Path $out $n
    if (Test-Path -LiteralPath $p) { '{0}  {1}' -f (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLowerInvariant(), $n }
}
Set-Content -LiteralPath (Join-Path $out 'SHA256SUMS') -Value $lines -Encoding ascii
Write-Host "Built: $dll" -ForegroundColor Green
Write-Host "Next : .\Install.ps1 -Year $Year   (run as Administrator)"
