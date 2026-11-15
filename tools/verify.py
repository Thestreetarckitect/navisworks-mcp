#!/usr/bin/env python3
"""Verify release/*/SHA256SUMS, scan for committed secrets and oversized files."""
import glob, hashlib, os, re, sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
failed = 0
checked = 0
for sums in sorted(glob.glob(os.path.join(root, "release", "*", "SHA256SUMS"))):
    base = os.path.dirname(sums)
    for line in open(sums, encoding="utf-8"):
        if not line.strip():
            continue
        h, name = line.split(None, 1)
        p = os.path.join(base, name.strip())
        checked += 1
        if not os.path.isfile(p):
            print("MISSING", os.path.relpath(p, root)); failed += 1; continue
        if hashlib.sha256(open(p, "rb").read()).hexdigest() != h.lower():
            print("CHECKSUM MISMATCH", os.path.relpath(p, root)); failed += 1
print("checked", checked, "release files, failures:", failed)

pat = re.compile(r'(auth_token|api[_-]?key|secret|password)\s*["\']?\s*[:=]\s*["\']?[A-Za-z0-9+/=_-]{16,}', re.I)
personal = re.compile(r'C:\\Users\\(?!<user>|\w*\.\.\.)[A-Za-z0-9._-]+\\', re.I)
leaks = 0
for d, dirs, files in os.walk(root):
    dirs[:] = [x for x in dirs if x not in (".git", "release", "dist", "bin", "obj")]
    for n in files:
        if os.path.splitext(n)[1].lower() not in (".md", ".json", ".ps1", ".py", ".cs", ".csproj", ".yml", ".txt", ""):
            continue
        p = os.path.join(d, n)
        t = open(p, encoding="utf-8", errors="ignore").read()
        rel = os.path.relpath(p, root)
        if rel.replace("\\", "/") == "tools/verify.py":
            continue
        if pat.search(t):
            print("POSSIBLE SECRET", rel); leaks += 1
        if personal.search(t):
            print("PERSONAL PATH", rel); leaks += 1
print("secret and personal-path hits:", leaks)

for d, dirs, files in os.walk(root):
    dirs[:] = [x for x in dirs if x != ".git"]
    for n in files:
        if os.path.getsize(os.path.join(d, n)) >= 100 * 1024 * 1024:
            print("TOO LARGE", n); failed += 1
sys.exit(1 if (failed or leaks) else 0)
