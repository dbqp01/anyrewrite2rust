# anyrewrite2rust (PoC)

Claude Code plugin to port a module from any language to Rust, with equivalence checked against the original by differential testing.

- `skills/anyrewrite2rust/SKILL.md`: the phased method (contract, spec, corpus, skeleton, implement, equivalence gate).
- `scripts/diffrun.py`: language-agnostic differential runner.
- `scripts/depmap.py`: inventory of a JS/TS project's runtime dependencies and the API surface it uses.
- `examples/calc/`: a full run on a Python integer calculator.
- `examples/dopamine/TRIAGE.md`: dependency triage of a real Electron app (not ported), sorting each dependency into a crate swap, a crate that behaves differently, or no equivalent.

## What the example run found
| Attempt | Result |
|---|---|
| Rust with `div_euclid` / `rem_euclid` | panicked on `i64::MIN % -1` after 164 inputs |
| Python floor semantics on `i64` | 907 mismatches: the original uses unbounded ints, and intermediate values like `10^30` are real behavior |
| `BigInt` + emulated Python quirks | 170,199 inputs, 0 mismatches, 9 accepted divergences (unicode digits) |

Quirks the port had to reproduce: floor division and modulo with negative divisors, left-to-right error ordering, Python's 4300-digit int/str limit, and the exact recursion depth where the original crashes.

## Run it
```
cd examples/calc/rust && cargo build --release && cd ..
python ../../scripts/diffrun.py --legacy "python legacy/calc.py" --new "rust/target/release/calc" --corpus corpus/edge.txt --gen "python gen.py 20000 1" --accept accept.py
```
