$ErrorActionPreference = "Stop"
$src  = "C:\Users\llampkin\AppData\Roaming\Autodesk\Navisworks Manage 2027\Plugins\MCPBridge"
$dest = "C:\Program Files\Autodesk\Navisworks Manage 2027\Plugins\MCPBridge"
New-Item -ItemType Directory -Force $dest | Out-Null
Copy-Item "$src\MCPBridge.dll" $dest -Force
Copy-Item "$src\MCPBridge.pdb" $dest -Force -ErrorAction SilentlyContinue
Get-ChildItem $dest -Recurse -File | Unblock-File -ErrorAction SilentlyContinue
"Deployed to install dir:" | Out-Host
Get-ChildItem $dest | ForEach-Object { "  $($_.Name)" } | Out-Host
