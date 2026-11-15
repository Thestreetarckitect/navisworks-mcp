#Requires -Version 5.1
# Verify release\<year>\SHA256SUMS against the files next to them.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$failed = 0; $checked = 0
foreach ($sums in Get-ChildItem -Path (Join-Path $root 'release') -Recurse -Filter SHA256SUMS -File) {
    foreach ($line in Get-Content -LiteralPath $sums.FullName) {
        if (-not $line.Trim()) { continue }
        $hash, $name = $line -split '\s+', 2
        $p = Join-Path $sums.DirectoryName $name.Trim()
        $checked++
        if (-not (Test-Path -LiteralPath $p)) { Write-Host "MISSING $p" -ForegroundColor Red; $failed++; continue }
        if ((Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLowerInvariant() -ne $hash.ToLowerInvariant()) {
            Write-Host "CHECKSUM MISMATCH $p" -ForegroundColor Red; $failed++
        }
    }
}
Write-Host "Checked $checked files, failures: $failed"
if ($failed) { exit 1 }
