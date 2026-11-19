"""Self-check for depmap's import parsing. run: python scripts/test_depmap.py"""
from depmap import IMPORT, names_of, package_of

assert package_of("@angular/material/dialog") == "@angular/material"
assert package_of("fs-extra/lib") == "fs-extra"
assert package_of("./local") is None

src = """import Foo, { a, b as c } from 'pkg-a';
import * as X from "pkg-b";
import type { T } from 'pkg-c';
const y = require('pkg-d');
"""
found = {(m.group("mod") or m.group("req")): m.group("what") for m in IMPORT.finditer(src)}
assert set(found) == {"pkg-a", "pkg-b", "pkg-c", "pkg-d"}, found
assert names_of(found["pkg-a"]) == {"default", "a", "b"}
assert names_of(found["pkg-b"]) == {"*"}
assert names_of(found["pkg-c"]) == {"T"}
print("depmap self-check ok")
