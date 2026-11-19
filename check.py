"""Repo self-test: unit self-checks, both example ports built and diff-tested. run: python check.py"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(ROOT, "skills", "anyrewrite2rust", "scripts")
steps = [
    ([sys.executable, "test_diffrun.py"], SCRIPTS),
    ([sys.executable, "test_depmap.py"], SCRIPTS),
    ([sys.executable, "accept_helpers.py"], SCRIPTS),
]
for ex in ("calc", "slug"):
    d = os.path.join(ROOT, "examples", ex)
    steps += [
        ([sys.executable, "accept.py"], d),
        (["cargo", "clippy", "-q", "--", "-D", "warnings"], os.path.join(d, "rust")),
        (["cargo", "test", "-q"], os.path.join(d, "rust")),
        (["cargo", "build", "--release", "-q"], os.path.join(d, "rust")),
        ([sys.executable, os.path.join(SCRIPTS, "diffrun.py"), "--config", "port.json"], d),
    ]

failed = 0
for cmd, cwd in steps:
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    label = f"{os.path.relpath(cwd, ROOT)}: {' '.join(os.path.basename(c) for c in cmd[:3])}"
    print(("ok   " if p.returncode == 0 else "FAIL ") + label)
    if p.returncode:
        failed += 1
        print((p.stdout + p.stderr)[-1500:])
sys.exit(1 if failed else 0)
