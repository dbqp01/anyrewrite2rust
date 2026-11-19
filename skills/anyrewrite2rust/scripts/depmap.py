"""Dependency inventory for a JS/TS project: for each runtime dependency, which files import it and which names they use.

The API surface actually used (not the whole library) is what a Rust replacement or rewrite must cover.
usage: python depmap.py <project_dir> [--src src,main] [--json out.json]
"""
import argparse
import collections
import json
import os
import re

# import x from 'p' | import {a, b as c} from 'p' | import * as x from 'p' | require('p')
IMPORT = re.compile(r"""import\s+(?:type\s+)?(?P<what>[^'";]*?)\s*from\s*['"](?P<mod>[^'"]+)['"]|require\(\s*['"](?P<req>[^'"]+)['"]\s*\)""", re.S)


def package_of(spec):
    if spec.startswith((".", "/")):
        return None
    parts = spec.split("/")
    return "/".join(parts[:2]) if spec.startswith("@") else parts[0]


def names_of(what):
    what = what.strip()
    if not what:
        return set()
    names = set()
    braces = re.search(r"\{([^}]*)\}", what)
    if braces:
        names |= {n.split(" as ")[0].strip() for n in braces.group(1).split(",") if n.strip()}
        what = what.replace(braces.group(0), "")
    for part in what.split(","):
        part = part.strip()
        if part.startswith("* as"):
            names.add("*")
        elif part:
            names.add("default")
    return names


def scan(root, src_dirs, deps):
    files, names = collections.defaultdict(set), collections.defaultdict(set)
    paths = []
    for d in src_dirs:
        top = os.path.join(root, d)
        if os.path.isfile(top):
            paths.append(top)
        for dirpath, dirnames, filenames in os.walk(top):
            dirnames[:] = [x for x in dirnames if x != "node_modules"]
            paths += [os.path.join(dirpath, fn) for fn in filenames]
    for path in paths:
        if not path.endswith((".ts", ".js")) or path.endswith((".spec.ts", ".d.ts")):
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        for m in IMPORT.finditer(text):
            pkg = package_of(m.group("mod") or m.group("req"))
            if pkg in deps:
                files[pkg].add(os.path.relpath(path, root).replace("\\", "/"))
                names[pkg] |= names_of(m.group("what") or "") if m.group("mod") else {"require"}
    return files, names


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--src", default="src,main,main.ts")
    ap.add_argument("--json")
    a = ap.parse_args()
    with open(os.path.join(a.project, "package.json"), encoding="utf-8") as fh:
        deps = set(json.load(fh).get("dependencies", {}))
    files, names = scan(a.project, a.src.split(","), deps)
    rows = sorted(((d, sorted(files.get(d, ())), sorted(names.get(d, ()))) for d in deps), key=lambda r: -len(r[1]))
    for d, fs, ns in rows:
        print(f"{len(fs):4d} files  {d:32s} {', '.join(ns)[:90]}")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump([{"dep": d, "files": fs, "names": ns} for d, fs, ns in rows], fh, indent=1)


if __name__ == "__main__":
    main()
