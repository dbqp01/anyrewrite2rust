"""Random expression generator for differential fuzzing. usage: python gen.py N SEED"""
import random
import sys

n, seed = int(sys.argv[1]), int(sys.argv[2])
rng = random.Random(seed)


def num():
    r = rng.random()
    if r < 0.6:
        return str(rng.randint(0, 20))
    if r < 0.9:
        return str(rng.randint(0, 10**6))
    return str(rng.choice([2**31, 2**62, 2**63 - 1, 2**63, 3037000500]))


def expr(d):
    if d <= 0 or rng.random() < 0.3:
        return num()
    k = rng.random()
    if k < 0.15:
        return "-" + expr(d - 1)
    if k < 0.3:
        return "(" + expr(d - 1) + ")"
    if k < 0.4:
        return expr(d - 1) + "^" + str(rng.randint(-1, 5))
    op = rng.choice("+-*/%")
    sp = rng.choice(["", " "])
    return expr(d - 1) + sp + op + sp + expr(d - 1)


def mutate(s):
    # occasionally break the input so error paths get exercised too
    r = rng.random()
    if r < 0.05 and s:
        i = rng.randrange(len(s))
        return s[:i] + s[i + 1:]
    if r < 0.08:
        return s + rng.choice(["(", ")", "+", "$", " 1"])
    return s


for _ in range(n):
    print(mutate(expr(rng.randint(1, 6))))
