"""Scaffold a port folder: port.json, corpus/, accept.py, spec.md and a Rust crate that speaks the same contract.

usage:
  python init.py <port_dir> --module path/to/lib.py|lib.js     function-level port (JSON lines via a harness)
  python init.py <port_dir> --module adapter.ts [--alias @angular/core=./stub.js]   TS, bundled with esbuild
  python init.py <port_dir> --legacy-cmd "python tool.py"      program-level port (the program already reads stdin lines)
Then: fill spec.md, add calls to corpus/edge.txt, implement rust/src/main.rs, run
  python diffrun.py --config <port_dir>/port.json
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fwd = lambda p: p.replace("\\", "/")

SPEC = """# {name}: spec

## Contract
{contract}

## Functions (pseudocode, with file:line of the original)

## Quirks (measured by running the original, not guessed)

## Port decisions (human-reviewed; every accepted divergence is listed here and in accept.py)
"""

ACCEPT = '''"""Divergences a human accepted. Each rule must match a decision written in spec.md."""


def accepted(inp, legacy, new):
    return False


if __name__ == "__main__":
    assert not accepted("x", "a", "b")
    print("accept.py self-check ok")
'''


def write(path, text):
    if os.path.exists(path):
        print(f"keep   {path}")
        return
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(f"create {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("port_dir")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--module", help="Python or JS module whose functions are ported")
    src.add_argument("--legacy-cmd", help="command of an original that already reads one input per stdin line")
    ap.add_argument("--name", help="crate name (default: port folder name)")
    ap.add_argument("--alias", action="append", default=[],
                    help="TS only, repeatable: replace an import when bundling, e.g. @angular/core=./stubs/angular.js")
    a = ap.parse_args()

    root = os.path.abspath(a.port_dir)
    name = (a.name or os.path.basename(root)).replace("-", "_")
    os.makedirs(os.path.join(root, "corpus"), exist_ok=True)

    if a.module:
        mod = fwd(os.path.relpath(os.path.abspath(a.module), root))
        ext = os.path.splitext(mod)[1]
        try:  # relative when possible, so the port folder can move or be committed with the plugin
            harness = fwd(os.path.relpath(os.path.join(SKILL, "harness"), root))
        except ValueError:  # different drive on Windows
            harness = fwd(os.path.join(SKILL, "harness"))
        if ext in (".ts", ".tsx", ".mts"):
            # TS can't run as is: bundle it to one CommonJS file, then use the JS harness on the bundle
            bundle = os.path.join(root, "legacy.bundle.cjs")
            cmd = ["npx", "--yes", "esbuild", os.path.abspath(a.module), "--bundle", "--platform=node",
                   "--format=cjs", f"--outfile={bundle}", "--log-level=warning"] + [f"--alias:{x}" for x in a.alias]
            print(" ".join(cmd))
            if subprocess.run(cmd, shell=os.name == "nt").returncode:
                sys.exit("esbuild failed: stub framework imports with --alias pkg=./stub.js (see SKILL.md, TypeScript)")
            mod, ext = "legacy.bundle.cjs", ".cjs"
        if ext == ".py":
            legacy = f'python "{harness}/py_harness.py" "{mod}"'
        elif ext in (".js", ".mjs", ".cjs"):
            legacy = f'node "{harness}/js_harness.mjs" "{mod}"'
        else:
            sys.exit(f"no harness for {ext}: write one (see harness/) or use --legacy-cmd")
        contract = 'stdin `{"fn": "name", "args": [...]}` per line; stdout `{"ok": value}` or `{"err": "ErrorName"}`.'
        as_json = True
    else:
        legacy, contract, as_json = a.legacy_cmd, "One input per stdin line, exactly one output line per input.", False

    cfg = {"legacy": legacy, "new": f"rust/target/release/{name}", "corpus": ["corpus/edge.txt"],
           "gen": None, "accept": "accept.py", "json": as_json, "float-tol": 1e-9 if as_json else 0}
    write(os.path.join(root, "port.json"), json.dumps(cfg, indent=2) + "\n")
    write(os.path.join(root, "corpus", "edge.txt"), "")
    write(os.path.join(root, "accept.py"), ACCEPT)
    write(os.path.join(root, "spec.md"), SPEC.format(name=name, contract=contract))

    crate = os.path.join(root, "rust")
    if not os.path.exists(crate):
        subprocess.run(["cargo", "new", "--vcs", "none", "--name", name, crate, "-q"], check=True)
        if as_json:
            subprocess.run(["cargo", "add", "serde_json", "-q"], cwd=crate, check=True)
            shutil.copy(os.path.join(SKILL, "templates", "main.rs"), os.path.join(crate, "src", "main.rs"))
        print(f"create {crate}")
    print(f"\nnext: python \"{fwd(SKILL)}/scripts/diffrun.py\" --config \"{fwd(root)}/port.json\"")


if __name__ == "__main__":
    main()
