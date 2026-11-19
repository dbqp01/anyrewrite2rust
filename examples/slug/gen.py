"""Random calls for textkit. usage: python gen.py N SEED"""
import json
import random
import sys

n, seed = int(sys.argv[1]), int(sys.argv[2])
rng = random.Random(seed)
# pieces chosen for the traps: accents, ligatures, Turkish İ, Greek sigma, emoji (surrogate pairs), JS-only spaces
PIECES = ["hello", "World", "Ünïcödé", "ﬁ", "İstanbul", "ΣΑΣ", "日本", "😀", "👍🏽", "123", "v1", "a.b",
          " ", "  ", "\t", "\n", " ", "\u0085", "﻿", " ", "　", "-", "_", "!", "é", "é", "Ⅻ", "²"]
SEPS = ["-", "_", "", ".", "+", "*", "~", "--", "ab", "|", "\\"]


def text():
    return "".join(rng.choice(PIECES) for _ in range(rng.randint(0, 6)))


def version():
    parts = [str(rng.choice([0, 1, 12, 99999999999999999999])) for _ in range(rng.choice([2, 3, 3, 3, 4]))]
    v = ".".join(parts)
    if rng.random() < 0.3:
        v += "-" + rng.choice(["rc.1", "beta", "", "x_y", "a-b"])
    return rng.choice(["", "v", " ", "﻿", "V"]) + v + rng.choice(["", " ", "\n", "\u0085"])


for _ in range(n):
    f = rng.choice(["slugify", "slugify", "truncate", "parseSemver", "wordCount"])
    if f == "slugify":
        args = [text()] + ([rng.choice(SEPS)] if rng.random() < 0.5 else [])
    elif f == "truncate":
        args = [text(), rng.choice([0, 1, 2, 3, 5, 8, 2.0, 2.5, -1])]
    elif f == "parseSemver":
        args = [version()]
    else:
        args = [text()]
    print(json.dumps({"fn": f, "args": args}, ensure_ascii=False))
