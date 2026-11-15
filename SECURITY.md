# Security

## How this addin works
The addin runs an HTTP listener inside Navisworks at `http://localhost:8765/`. The Python MCP server (`server_http.py`) sends it JSON commands. Anything that can reach that port can read and change the open model: select, hide, colour, create and delete clash tests, save and delete viewpoints.

The listener has no password or token. It only accepts connections from the same computer.

## What that means for you
- Open only models you are happy for an AI client to change. Save a copy first.
- Close Navisworks when you are not using the bridge. The port closes with it.
- Run one MCP client at a time.
- Do not open untrusted web pages while a sensitive model is loaded. A web page can send requests to a local port.
- Do not forward or tunnel port 8765.

A shared-secret token and request origin checks are the next hardening step. They need a rebuild of the addin, so they are not in this release.

## Verify before you install
From the repository root:

    pwsh ./tools/verify.ps1

or with Python 3:

    python3 tools/verify.py

Both check every file listed in `release/<year>/SHA256SUMS`. `Install.ps1` runs the same check before it copies anything. CI runs it on every push and pull request.

If you build your own DLL with `Build.ps1`, it writes `dist/<year>/SHA256SUMS` so you can compare builds.

## Report a problem
Open a private security advisory on this repository, or contact the owner through the GitHub profile.
