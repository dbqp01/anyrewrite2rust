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

## Phase 0.5: dependency triage (before any spec)
Run `python <plugin>/scripts/depmap.py <project>` for JS/TS (for other languages, list imports by hand the same way). What matters is the API surface the code actually uses, not the whole library. Put every dependency in one tier:
- **A, direct crate**: same job, same contract (rusqlite for better-sqlite3, uuid). Swap it and diff-test the call sites.
- **B, crate that behaves differently**: same job, different output (tag readers, date formatting, image resizing, color extraction). Diff-test the library itself through the harness before trusting it. When output can't match (a different algorithm), the human picks one: accept with a tolerance in `accept.py`, or go to C.
- **C, no equivalent**: choose the cheapest option that still works:
  1. **Keep it out of the port.** Leave that part in the original language and call it over a boundary (subprocess + JSON lines, or a sidecar). Most UI frameworks land here, and so do browser APIs and huge libraries.
  2. **Port only the used surface.** If the code calls 3 functions of a big library, port those 3 as a small Rust module with its own corpus and diff-test. This is the usual answer to "do I rewrite the library": you rewrite the slice you use.
  3. **Bind to the native library** under the JS package (FFI) when it wraps C/C++.
  4. **Full library rewrite**: only when it is small and central. Treat it as its own anyrewrite2rust run.
Also look for **patches to dependencies** (`patch-package`, postinstall scripts, vendored edits). They are behavior the port must keep, and no crate will have them.
Write the result as `TRIAGE.md` (see `examples/dopamine/TRIAGE.md`). If tier C covers the core of the app, say so: that is a rewrite of the product, not a port.

## Phase 0.7: UI target (only if the app has a UI)
The UI can't be diff-tested line by line. Port the core (data, parsing, rules, I/O) first as a Rust library the old UI calls, then decide the UI:
| Original UI | Cheapest target | Native Rust alternative |
|---|---|---|
| Web stack in Electron (Angular, React, Vue) | Tauri, frontend kept as is | Dioxus (components, React-like), Slint, Iced |
| GTK (C) | gtk4-rs / Relm4: widgets map almost 1:1 | |
| Qt / QML (C++) | cxx-qt: keep Qt, logic in Rust | Slint (closest to QML) |
| Win32 / WinUI | `windows` crate (Microsoft's bindings) | Slint, Iced |
| Dear ImGui / tools | egui | |
Real apps on native Rust UI: Zed (GPUI), COSMIC desktop (Iced). Rewriting the UI is reimagining, not porting: verify it with screenshots and manual flows, not with `diffrun.py`.

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
