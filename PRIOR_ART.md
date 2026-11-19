# Prior art (searched 2026-11-19)

| Project | Languages | How it verifies | Gap this repo targets |
|---|---|---|---|
| [Noricum](https://github.com/JuanMarchetto/noricum) (CLI, MIT, 1 star) | C only | Compiles both, byte-exact stdout + exit code on the same inputs, LLM repair loop (5 tries) | C only, no dependency mapping, no UI |
| [rustport-skill](https://github.com/LakoMoor/rustport-skill) (Claude Code skill, Apache-2.0, 1 star) | Games/apps, C++/SDL2 example | Golden outputs, JSONL traces, optional Ghidra/Unicorn differential fuzzing | Game-runtime oriented; dependency handling not described |
| [Beautiful Rust: rust-port](https://www.prompthackers.co/claude-skills/beautiful-rust) (skill) | C, C++, Python, Go, JS | Ports the original's existing tests; no side-by-side run | Equivalence only as good as the original test suite |
| [Flourine](https://arxiv.org/abs/2405.11514) (paper) | C, Go | Differential fuzzing, counterexamples fed back to the LLM; 47% of benchmarks with the best LLM | Research, no reusable workflow |
| [ACToR](https://arxiv.org/html/2510.03879) (paper) | C | Adversarial agent looks for diverging inputs | C only |
| [RustAssure](https://arxiv.org/abs/2510.07604) (paper) | C | Differential symbolic testing | C only |
| [ORBIT](https://arxiv.org/pdf/2604.12048) (paper) | C | Test suites; 91.7% test success | C only |
| [DARPA TRACTOR](https://www.darpa.mil/research/programs/translating-all-c-to-rust) ([test corpus](https://github.com/DARPA-TRACTOR-Program/PUBLIC-Test-Corpus)) | C | Program benchmark | C only |

## What none of them do (this repo's niche)
1. Any source language behind one contract (JSON lines on stdin/stdout), not only C.
2. **Dependency triage** before porting: crate swap, crate that behaves differently, no equivalent (`scripts/depmap.py`, `examples/dopamine/TRIAGE.md`), including patches the app applies to its dependencies.
3. **UI target decision** (Tauri, native Rust toolkit, keep the toolkit via bindings) with the core ported and verified first.
4. Human-reviewed `accept.py`: every divergence from the original is a recorded decision, not a silent difference.

## Worth borrowing
- Noricum: automatic LLM repair loop on mismatch, float epsilon tolerance.
- ACToR: an adversarial agent whose only job is finding inputs where the two sides diverge (better than a random fuzzer at finding the 907-type bug early).
- rustport-skill: a ledger (SQLite/JSONL) of behaviors with status `compared`/`verified`, so long ports can resume.
