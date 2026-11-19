---
description: Start porting a module to Rust (triage, scaffold, spec)
argument-hint: <path to module or program> [port folder]
---

Start an anyrewrite2rust port of: $ARGUMENTS

Use the anyrewrite2rust skill. Scripts are in `${CLAUDE_PLUGIN_ROOT}/skills/anyrewrite2rust/scripts/`.
1. Look at what the target is (a library module or a program reading stdin) and its language. Run the dependency triage if it imports third-party packages.
2. Scaffold the port folder with `python ${CLAUDE_PLUGIN_ROOT}/skills/anyrewrite2rust/scripts/init.py <port folder> --module <file>` (or `--legacy-cmd "<command>"`).
3. Write spec.md with the quirks you measured by running the original, then stop and show it to me before writing Rust.
