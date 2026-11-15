#Requires -Version 5.1
<#
.SYNOPSIS
  Install the MCP Bridge addin into Navisworks 2025, 2026 or 2027.

.DESCRIPTION
  Copies MCPBridge.dll to
    C:\Program Files\Autodesk\Navisworks Manage <Year>\Plugins\MCPBridge\
  This folder needs Administrator rights. Navisworks does not load the addin
  from %APPDATA%.

  Source order: dist\<Year>\ (your own build from Build.ps1), then
  release\<Year>\ (prebuilt, currently 2027 only). The files are checked
  against SHA256SUMS first.

.PARAMETER Year
  2025, 2026 or 2027. Default 2027.

.PARAMETER Uninstall
  Remove the addin folder.

.EXAMPLE
  .\Install.ps1 -Year 2027 -WhatIf
  .\Install.ps1 -Year 2026
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [ValidateSet(2025, 2026, 2027)][int]$Year = 2027,
    [switch]$Uninstall
)
$ErrorActionPreference = 'Stop'

$root = Join-Path $env:ProgramFiles "Autodesk\Navisworks Manage $Year"
$dest = Join-Path $root 'Plugins\MCPBridge'

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin -and -not $WhatIfPreference) {
    throw 'Run this script as Administrator. Right-click PowerShell and choose Run as administrator.'
}
if (-not (Test-Path -LiteralPath $root)) {
    throw "Navisworks Manage $Year not found at '$root'."
}
if (Get-Process -Name Roamer -ErrorAction SilentlyContinue) {
    throw 'Navisworks is running. Close it and run this again.'
}

if ($Uninstall) {
    if (Test-Path -LiteralPath $dest) {
        if ($PSCmdlet.ShouldProcess($dest, 'Remove addin folder')) { Remove-Item -LiteralPath $dest -Recurse -Force }
        Write-Host "Removed $dest"
    } else { Write-Host 'Nothing to remove.' }
    return
}

$source = $null
foreach ($c in (Join-Path $PSScriptRoot "dist\$Year"), (Join-Path $PSScriptRoot "release\$Year")) {
    if (Test-Path -LiteralPath (Join-Path $c 'MCPBridge.dll')) { $source = $c; break }
}
if (-not $source) {
    throw "No MCPBridge.dll for $Year. Build it first: .\Build.ps1 -Year $Year"
}

# Verify checksums before copying anything.
$sums = Join-Path $source 'SHA256SUMS'
if (-not (Test-Path -LiteralPath $sums)) { throw "Missing $sums. Refusing to install an unverified file." }
foreach ($line in Get-Content -LiteralPath $sums) {
    if (-not $line.Trim()) { continue }
    $hash, $name = $line -split '\s+', 2
    $p = Join-Path $source $name.Trim()
    if (-not (Test-Path -LiteralPath $p)) { throw "SHA256SUMS lists $name but the file is missing." }
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLowerInvariant() -ne $hash.ToLowerInvariant()) {
        throw "Checksum mismatch for $name. Do not install it. Download the repository again or rebuild."
    }
}
Write-Host "Source : $source (checksums OK)"
Write-Host "Dest   : $dest"

if ($PSCmdlet.ShouldProcess($dest, 'Install addin')) {
    New-Item -ItemType Directory -Force $dest | Out-Null
    foreach ($n in 'MCPBridge.dll', 'MCPBridge.pdb') {
        $p = Join-Path $source $n
        if (Test-Path -LiteralPath $p) { Copy-Item -LiteralPath $p -Destination $dest -Force }
    }
    Get-ChildItem -LiteralPath $dest -Recurse -File | Unblock-File -ErrorAction SilentlyContinue
    Write-Host "Done. Start Navisworks $Year, open the Add-Ins tab and click MCP Bridge." -ForegroundColor Green
}
