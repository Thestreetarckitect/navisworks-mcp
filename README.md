# Navisworks MCP Bridge

Claude MCP integration for Autodesk Navisworks Manage 2027.

Two-piece architecture: a C# addin running inside Navisworks exposes an HTTP API on `localhost:8765`, and a Python MCP server bridges that API to Claude.

## Architecture

```
Claude (MCP client)
      ↕  stdio
Python MCP server (server_http.py)
      ↕  HTTP localhost:8765
C# Addin (MCPBridge.dll) inside Navisworks Manage 2027
      ↕  Navisworks API
.nwd / .nwf model
```

## Requirements

- Autodesk Navisworks Manage **2027** (Freedom not supported)
- Python 3.12+ — install path: `C:\Users\<user>\AppData\Local\Programs\Python\Python312\python.exe`
- `mcp` Python package: `pip install mcp`
- Claude Desktop or Claude Code with MCP support

## Install

### 1. Deploy the addin (requires admin / UAC)

```powershell
# Run as Administrator
.\elevate_deploy.ps1
```

Copies `release\MCPBridge.dll` to:
```
C:\Program Files\Autodesk\Navisworks Manage 2027\Plugins\MCPBridge\
```

> **Note:** Deploying to `%APPDATA%\Autodesk\...` alone does NOT load the addin. Must be in the Program Files plugins dir.

### 2. Configure Claude MCP

Add to `~/.claude.json` under `mcpServers`:

```json
"navisworks": {
  "command": "C:\\Users\\<user>\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
  "args": ["C:\\Users\\<user>\\NavisworksMCP\\server_http.py"]
}
```

### 3. Start Navisworks

Open Navisworks Manage 2027. The **Add-Ins** ribbon tab should show an **MCP Bridge** button.

### 4. Verify

```powershell
Invoke-RestMethod http://localhost:8765/health
```

Expected: `ok v2.1  35 routes`

## Files

| File | Purpose |
|---|---|
| `server_http.py` | Python MCP server — bridges Claude to Navisworks HTTP API |
| `MCPBridgePlugin.cs` | C# Navisworks addin source |
| `ClashGroupHandlers.cs` | Clash detection group handler source |
| `NavisworksMcpAddin.csproj` | VS project file (targets net48, Navisworks API v24) |
| `release/MCPBridge.dll` | Prebuilt addin DLL — deploy this |
| `release/MCPBridge.pdb` | Debug symbols |
| `elevate_deploy.ps1` | Deploy script (copies DLL to Program Files, needs admin) |
| `Install-Addin.ps1` | Original install script from upstream |
| `make_clash_report.py` | Utility: generate clash report from Navisworks via MCP |

## Known Gotchas

- The `.addin` manifest file is a Revit format — Navisworks ignores it. Remove it.
- `Install-Addin.ps1` from upstream has a parse error (`<` literal) — use `elevate_deploy.ps1` instead.
- Navisworks 2020 and 2022 also installed but NOT supported by this addin (API version mismatch).
- Python scripts dir is not on PATH — use full `python.exe` path in MCP config.
