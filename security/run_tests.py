#!/usr/bin/env python3
"""Runs every self-test of the repo and fails if any of them does not end in OK.

Usage:
    python security/run_tests.py [--only NAME ...]

Runs, from the repo root:
  - every skills/*/scripts/*.py with --test (and fails if one of the expected method scripts is missing),
  - mcp/test_server.py, install/install.py --test,
  - security/scan.py --test and security/manifest.py --test.
A test passes when it exits 0 and its last non-empty output line contains "OK".
Used by .github/workflows/tests.yml; runs the same way on Windows, macOS and Linux.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPECTED_SCRIPTS = (
    "skills/procurement/scripts/procurement.py",
    "skills/cost-and-pricing/scripts/cost_pricing.py",
    "skills/economic-evaluation/scripts/evaluate.py",
    "skills/financial-evaluation/scripts/financial_evaluation.py",
    "skills/map-context/scripts/map_context.py",
    "skills/research/scripts/validate_research.py",
    "skills/audit/scripts/rerun.py",
)
TIMEOUT = 600

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def plan() -> tuple[list[tuple[str, list[str]]], list[str]]:
    tests, missing = [], []
    found = sorted(p.relative_to(ROOT).as_posix() for p in ROOT.glob("skills/*/scripts/*.py"))
    for rel in EXPECTED_SCRIPTS:
        if rel not in found:
            missing.append(rel)
    for rel in found:
        tests.append((rel, [rel, "--test"]))
    for rel, args in (("mcp/test_server.py", []), ("install/install.py", ["--test"]),
                      ("security/scan.py", ["--test"]), ("security/manifest.py", ["--test"])):
        if (ROOT / rel).is_file():
            tests.append((rel, [rel, *args]))
        else:
            missing.append(rel)
    return tests, missing


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", nargs="*", help="run only tests whose path contains one of these strings")
    a = ap.parse_args(argv)
    tests, missing = plan()
    if a.only:
        tests = [t for t in tests if any(o in t[0] for o in a.only)]
        missing = []
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    failed = list(f"{m} (missing)" for m in missing)
    for rel, args in tests:
        start = time.time()
        try:
            r = subprocess.run([sys.executable, "-B", *args], cwd=ROOT, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=TIMEOUT, env=env)
            out = (r.stdout or "") + (r.stderr or "")
            last = next((ln for ln in reversed(out.splitlines()) if ln.strip()), "")
            ok = r.returncode == 0 and "OK" in last
        except subprocess.TimeoutExpired:
            out, last, ok = "", f"timeout after {TIMEOUT}s", False
        print(f"{'ok  ' if ok else 'FAIL'} {rel} ({time.time() - start:.1f}s) · {last.strip()[:100]}")
        if not ok:
            failed.append(rel)
            print("\n".join("    " + ln for ln in out.splitlines()[-25:]))
    for m in missing:
        print(f"FAIL {m} is missing")
    if failed:
        print(f"FAIL: {len(failed)} test(s): {', '.join(failed)}")
        return 1
    print(f"OK ({len(tests)} tests)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
