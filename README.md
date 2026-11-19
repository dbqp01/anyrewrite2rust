# anyrewrite2rust

A Claude Code plugin for porting code from Python, JavaScript or another language to Rust, with **proof that the port behaves like the original**. The original and the port get the same inputs, sometimes tens of thousands of them, and every difference in output must either be fixed or written down as a decision.

Translating is the easy part for an LLM. The hard part is knowing the result is right. This plugin covers that part.

## Install
```
claude plugin marketplace add <path or git URL of this repo>
claude plugin install anyrewrite2rust@anyrewrite2rust
```
You need Python 3.10+, Rust (cargo, with clippy), and Node 18+ if the original is JS.

## Use
In Claude Code:
```
/anyrewrite2rust:port path/to/textkit.js ports/textkit
```
Claude scaffolds the port, measures how the original behaves, writes `spec.md` and stops for you to review it. Then it writes the Rust code. Next:
```
/anyrewrite2rust:verify ports/textkit
```
This builds the port, runs the equivalence gate and then the **divergence-hunter** agent (Haiku), which reads both versions and tries to make them disagree.

Without Claude, the tools work on their own:
```
python skills/anyrewrite2rust/scripts/init.py ports/textkit --module path/to/textkit.js
python skills/anyrewrite2rust/scripts/diffrun.py --config ports/textkit/port.json
```

## What's inside
| Piece | What it does |
|---|---|
| `skills/anyrewrite2rust/SKILL.md` | The method: contract, dependency triage, UI target, spec, corpus, skeleton, implement, gate. Ends with the language traps found so far. |
| `scripts/init.py` | Scaffolds `port.json`, `spec.md`, `accept.py`, the corpus folder and a Rust crate that speaks the contract. |
| `harness/py_harness.py`, `harness/js_harness.mjs` | Let you diff-test the functions of a library, not just CLIs: `{"fn","args"}` in, `{"ok"}`/`{"err"}` out. |
| `scripts/diffrun.py` | Differential runner. Compares as JSON (key order and `1` vs `1.0` don't count, float tolerance) and writes failing inputs to `mismatches.txt`. |
| `accept.py` (per port) | The only place a divergence can be accepted, one narrow rule per human decision. |
| `scripts/depmap.py` | Lists which npm dependencies are used, where, and which functions of each. Feeds the triage. |
| `agents/divergence-hunter.md` | Adversarial tester (Haiku). It reports problems and never edits code. |

## Proof it works
| Example | Original | Inputs compared | Result |
|---|---|---|---|
| `examples/calc` | Python program (integer calculator) | 170,199 | 0 mismatches after 2 failed attempts the gate caught: a panic, then 907 mismatches from using `i64` |
| `examples/slug` | JS library (slugify, truncate, semver, word count) | 60,092 | 0 mismatches. The hunter found 1 real bug and 2 language limits in one round, after 60k random inputs had passed |
| `examples/dopamine/TRIAGE.md` | Electron app, 90k lines (triage only, not ported) | n/a | Each dependency sorted into a crate swap, a crate that behaves differently, or no equivalent |

`python check.py` re-runs all of it: self-checks, clippy, tests and both equivalence gates.

## Limits
- One module at a time, up to a few thousand lines. Big systems are ported leaf by leaf.
- Only covers behavior visible through the contract. UIs, timing and side effects (files, network) need their own harness or a manual check.
- Harnesses exist for Python and JS. Other languages need about 40 lines of harness, following the two included.
- Passing the gate means "equal on every input tried", not a formal proof.

See `PRIOR_ART.md` for related tools (Noricum, rustport-skill, the TRACTOR program) and how this differs from them.
