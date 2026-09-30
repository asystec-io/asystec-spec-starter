#!/usr/bin/env python3
"""Generate/check release hashes; run only against reviewed source."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1] / "kit"
spec = importlib.util.spec_from_file_location("specctl", root / "specctl.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
files = {}
for path in sorted(root.rglob("*")):
    if path.is_file() and path.name != "release.json" and "__pycache__" not in path.parts:
        if path.is_symlink():
            raise SystemExit("Symlink in release")
        files[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
release = module.json_bytes({"schema_version": 1, "package": module.PACKAGE, "version": module.VERSION, "files": files})
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
path = root / "release.json"
if args.check:
    if not path.exists() or path.read_bytes() != release:
        raise SystemExit("Release manifest stale; review changes then regenerate")
    print("OK: release manifest")
else:
    path.write_bytes(release)
    print(f"Wrote {path} ({len(files)} files)")
