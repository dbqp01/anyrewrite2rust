"""Differential runner: feed the same input lines to the legacy and the new program, compare outputs line by line.

Contract both sides must follow: one input per stdin line, exactly one output line per input.

usage:
  python diffrun.py --legacy "python legacy/calc.py" --new "rust/target/release/calc" \
      --corpus corpus/edge.txt [--gen "python gen.py 5000 1"] [--accept accept.py] [--timeout 120]
Use forward slashes in commands. Exit code: 0 = equivalent, 1 = mismatches, 2 = a side failed to run.
"""
import argparse
import collections
import importlib.util
import json
import math
import os
import shlex
import shutil
import subprocess
import sys
import time


def run(cmd, data, timeout):
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    t0 = time.perf_counter()
    argv = shlex.split(cmd)
    argv[0] = shutil.which(argv[0]) or argv[0]  # Windows: finds calc.exe for "calc"
    p = subprocess.run(argv, input=data.encode("utf-8"), capture_output=True, timeout=timeout, env=env)
    dt = time.perf_counter() - t0
    out = p.stdout.decode("utf-8", errors="replace").replace("\r\n", "\n").split("\n")
    if out and out[-1] == "":
        out.pop()
    return p.returncode, out, p.stderr.decode("utf-8", errors="replace"), dt


def load_accept(path):
    if not path:
        return lambda inp, old, new: False
    spec = importlib.util.spec_from_file_location("accept", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.accepted


def same_json(a, b, tol):
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b or (tol > 0 and math.isclose(a, b, rel_tol=tol, abs_tol=tol))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same_json(a[k], b[k], tol) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same_json(x, y, tol) for x, y in zip(a, b))
    return a == b


def equal(o, n, as_json, tol):
    if o == n:
        return True
    if not as_json:
        return False
    try:
        return same_json(json.loads(o), json.loads(n), tol)
    except ValueError:
        return False


def kind(s):
    """Short label for grouping mismatches: 'ok', 'err div0', 'err TypeError'."""
    try:
        v = json.loads(s)
        if isinstance(v, dict) and "err" in v:
            return f"err {v['err']}"
        if isinstance(v, dict) and "ok" in v:
            return "ok"
    except ValueError:
        pass
    parts = s.split(" ")
    return parts[0] if parts[0] != "err" else " ".join(parts[:2])


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")  # Windows consoles default to cp1252
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", help="port.json with any of the options below")
    ap.add_argument("--legacy")
    ap.add_argument("--new")
    ap.add_argument("--corpus", nargs="*")
    ap.add_argument("--gen", help="command whose stdout is extra input lines")
    ap.add_argument("--accept", help="python file defining accepted(inp, legacy_out, new_out) -> bool")
    ap.add_argument("--json", action="store_true", default=None)
    ap.add_argument("--float-tol", type=float)
    ap.add_argument("--timeout", type=float)
    ap.add_argument("--show", type=int, default=15)
    a = ap.parse_args()
    if a.config:
        with open(a.config, encoding="utf-8") as fh:
            cfg = json.load(fh)
        os.chdir(os.path.dirname(os.path.abspath(a.config)))
        for k, v in cfg.items():
            if getattr(a, k.replace("-", "_"), None) is None:
                setattr(a, k.replace("-", "_"), v)
    if not a.legacy or not a.new:
        ap.error("--legacy and --new are required (directly or in --config)")
    a.corpus = a.corpus or []
    a.timeout = a.timeout or 120
    tol = a.float_tol or 0.0
    inputs = []
    for f in a.corpus:
        with open(f, encoding="utf-8", newline="") as fh:
            lines = fh.read().split("\n")
        inputs += lines[:-1] if lines and lines[-1] == "" else lines
    if a.gen:
        _, gen_lines, err, _ = run(a.gen, "", a.timeout)
        if not gen_lines:
            sys.exit(f"generator produced nothing: {err}")
        inputs += gen_lines
    # the line-based contract cannot carry these; fail loudly instead of misaligning
    bad = [i for i, s in enumerate(inputs) if "\r" in s]
    if bad:
        sys.exit(f"inputs contain \\r at lines {bad[:5]}")
    if not inputs:
        sys.exit("no inputs: add lines to the corpus or set a generator")
    data = "".join(s + "\n" for s in inputs)

    rc_old, old, err_old, t_old = run(a.legacy, data, a.timeout)
    rc_new, new, err_new, t_new = run(a.new, data, a.timeout)
    print(f"inputs: {len(inputs)}  legacy: {t_old:.2f}s  new: {t_new:.2f}s")
    for name, rc, out, err in (("legacy", rc_old, old, err_old), ("new", rc_new, new, err_new)):
        if rc != 0 or len(out) != len(inputs):
            print(f"FAIL {name}: exit {rc}, {len(out)} output lines for {len(inputs)} inputs\n{err[-2000:]}")
            sys.exit(2)

    accepted = load_accept(a.accept)
    n_acc, mism = 0, []
    for inp, o, n in zip(inputs, old, new):
        if equal(o, n, a.json, tol):
            continue
        if accepted(inp, o, n):
            n_acc += 1
        else:
            mism.append((inp, o, n))

    print(f"equal: {len(inputs) - n_acc - len(mism)}  accepted divergences: {n_acc}  mismatches: {len(mism)}")
    kinds = collections.Counter((kind(o), kind(n)) for _, o, n in mism)
    for (ko, kn), c in kinds.most_common():
        print(f"  {c:5d}  legacy[{ko}] vs new[{kn}]")
    for inp, o, n in mism[: a.show]:
        short = lambda s: s if len(s) <= 80 else s[:77] + "..."
        print(f"  in : {short(inp)!r}\n     legacy: {short(o)}\n     new   : {short(n)}")
    if mism:
        with open("mismatches.txt", "w", encoding="utf-8", newline="\n") as fh:
            fh.writelines(inp + "\n" for inp, _, _ in mism)
        print(f"wrote {len(mism)} failing inputs to {os.path.abspath('mismatches.txt')}")
    sys.exit(1 if mism else 0)


if __name__ == "__main__":
    main()
