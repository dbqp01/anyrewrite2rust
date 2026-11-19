---
name: anyrewrite2rust
description: Rewrite or reimagine a module from any language (Python, JS/TS, Go, Java, C...) in Rust, proving the port behaves like the original with differential tests. Use when the user wants to port, migrate, rewrite or "pass to Rust" a script, CLI, library or module.
---

# anyrewrite2rust

Work on ONE module at a time (a CLI, a library function set, up to ~5k lines). For bigger systems, port leaves of the dependency graph first.

The rule that makes this work: **the original program's observed behavior is the spec**. Prose and pseudocode lose detail; the differential run does not.

## Phase 0: the contract
Pick a boundary both programs can expose: one input per stdin line, one output line per input (JSON per line if the data is structured). If the original has no such entry point, write a thin harness around it in its own language. Do not change its logic.
Fix sources of false differences: time, randomness, dict ordering, paths, float formatting.

## Phase 1: spec (human reviews)
Write `spec.md`: I/O contract, neutral pseudocode, and a **Quirks** section with behavior the original has whether or not anyone intended it (error ordering, integer size, unicode handling, recursion limits, crashes). Measure quirks by running the original; do not guess them.

## Phase 2: corpus
- `corpus/edge.txt`: edge cases written from the spec alone, without reading the original's code. Delegate this to a cheap subagent (Haiku) given only `spec.md`, with hard rules: no `\r`, max line length, keep outputs small, cover every category in the spec.
- `gen.py N SEED`: random input generator for fuzzing. Include small mutations (deleted char, stray paren) so error paths get hit.

## Phase 3: Rust skeleton (human reviews)
Types, function signatures and ownership decisions, with `todo!()` bodies. Decide here how to represent the original's data (e.g. Python int means `BigInt`, not `i64`). Commit.

## Phase 4: implement
One function per commit. Gate every step with:
```
cargo clippy -- -D warnings && cargo test && cargo build --release
```

## Phase 5: equivalence gate
```
python <plugin>/scripts/diffrun.py --legacy "<cmd>" --new "rust/target/release/<bin>" \
  --corpus corpus/edge.txt --gen "python gen.py 20000 1" --accept accept.py
```
Exit 0 means equivalent. On mismatches, fix the Rust side, or, if a human decides the original's behavior is not worth keeping, add a narrow rule to `accept.py` and record the decision in `spec.md`. Never widen `accept.py` to make a run pass without that decision. Re-run with several seeds before calling it done.

## Phase 6: report
Inputs compared, equal / accepted / mismatches, timings of both sides, and the list of accepted divergences with their reasons.

See `examples/calc/` for a complete worked run.
