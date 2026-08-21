#!/usr/bin/env python3
"""Verify sha256 + byte size of committed aggregate_source files vs JSON provenance.

This is a source-hash gate, not a PNG-hash gate. Public provenance_manifest
strips figure-file hashes by design. Fails if a provenance.sources entry
points at a missing or mutated file. Does not download anything.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "web" / "public" / "data"
JSON = ROOT / "results" / "json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_dir(folder: Path) -> int:
    fails = 0
    for path in sorted(folder.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        sources = (payload.get("provenance") or {}).get("sources") or []
        for src in sources:
            rel = src.get("file")
            digest = src.get("sha256")
            nbytes = src.get("bytes")
            if not rel or not digest:
                print(f"SKIP incomplete provenance in {path.name}: {src}")
                continue
            target = ROOT / rel
            if not target.is_file():
                print(f"FAIL missing {rel} (from {path.name})", file=sys.stderr)
                fails += 1
                continue
            got = sha256(target)
            size = target.stat().st_size
            if got != digest or (nbytes is not None and size != nbytes):
                print(
                    f"FAIL hash/size {rel} from {path.name}: "
                    f"disk {got}/{size} json {digest}/{nbytes}",
                    file=sys.stderr,
                )
                fails += 1
            else:
                print(f"OK {rel} ({size} B)")
    return fails


def main() -> None:
    fails = check_dir(DATA) + check_dir(JSON)
    if fails:
        raise SystemExit(1)
    print("source-hash PASS")


if __name__ == "__main__":
    main()
