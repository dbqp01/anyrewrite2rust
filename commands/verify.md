---
description: Run the equivalence gate on a port folder and hunt for divergences
argument-hint: [port folder, default: current folder]
---

Verify the anyrewrite2rust port in: $ARGUMENTS (the current folder if empty)

1. `cargo build --release` and `cargo clippy -- -D warnings` in its `rust/` folder.
2. `python ${CLAUDE_PLUGIN_ROOT}/skills/anyrewrite2rust/scripts/diffrun.py --config <folder>/port.json`, then again with two more generator seeds if `gen` is set.
3. If it passes, launch the `anyrewrite2rust:divergence-hunter` agent on the folder, giving it the absolute diffrun path above.
4. Report: inputs compared, equal / accepted / mismatches per run, and each root cause the hunter found. Do not edit accept.py to make anything pass; ask me.
