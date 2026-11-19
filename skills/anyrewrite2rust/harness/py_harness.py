"""Call functions of a Python module over JSON lines, so a library (not just a CLI) can be diff-tested.

usage: python py_harness.py path/to/module.py
stdin : {"fn": "name", "args": [...]}            one call per line
stdout: {"ok": <result>} | {"err": "<ExceptionName>"}
Prints from the module go to stderr so they can't corrupt the protocol.
"""
import importlib.util
import json
import math
import os
import sys


def jsonable(v):
    # floats like nan/inf are not JSON; tuples/sets would silently change shape
    if isinstance(v, float) and not math.isfinite(v):
        return {"__float__": repr(v)}
    if isinstance(v, (list, tuple)):
        return [jsonable(x) for x in v]
    if isinstance(v, (set, frozenset)):
        return sorted((jsonable(x) for x in v), key=repr)
    if isinstance(v, dict):
        return {str(k): jsonable(x) for k, x in v.items()}
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    return {"__repr__": repr(v)}


def main():
    path = os.path.abspath(sys.argv[1])
    sys.path.insert(0, os.path.dirname(path))
    out = sys.stdout
    sys.stdout = sys.stderr
    spec = importlib.util.spec_from_file_location(os.path.splitext(os.path.basename(path))[0], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for line in sys.stdin:
        line = line.rstrip("\n")
        try:
            call = json.loads(line)
            fn = getattr(mod, call["fn"], None)
            # harness-level error, same name in every harness, so it never looks like original behavior
            res = {"ok": jsonable(fn(*call.get("args", [])))} if callable(fn) else {"err": "NoSuchFunction"}
        except RecursionError:
            res = {"err": "RecursionError"}
        except Exception as e:  # the exception type is part of the observed behavior
            res = {"err": type(e).__name__}
        out.write(json.dumps(res, ensure_ascii=False, sort_keys=True) + "\n")
        out.flush()


if __name__ == "__main__":
    main()
