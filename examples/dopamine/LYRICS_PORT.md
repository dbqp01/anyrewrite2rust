# Dopamine: one real module ported, and what the whole app would cost

Dopamine is GPL-3.0, so the ported Rust code (a derivative work) is not in this MIT repo. This page records the method and the numbers.
Source: github.com/digimezzo/dopamine @ 19bd0ab, 2026-11-19.

## The slice
`services/lyrics/lrc-lyrics-getter.ts` (97 lines), `srt-lyrics-getter.ts` (133) and `common/utils/string-utils.ts` (124): 354 lines of TS, ported to about 240 lines of Rust (`regex`, `unicode-normalization`).

## How the real code ran without Angular or Electron
- `adapter.ts` imports the three real files and exports plain functions (`parseLrc(lines)`, `getSortableString(s, prefixes)`, ...).
- The getters take a `FileAccessBase` through DI. The adapter passes a fake one that serves the lines given in the call, so the real parsing code runs unchanged.
- `@angular/core` is replaced by a one-line stub (`exports.Injectable = () => (c) => c;`) and esbuild bundles everything: `init.py port --module adapter.ts --alias @angular/core=./stub.js`.

## Results
| Step | Result |
|---|---|
| First diff run, 20,001 inputs | 29 mismatches, all `replaceAll(s, "", x)`: JS splits strings into UTF-16 units and puts `x` inside emoji. Accepted with `accept_helpers.lone_surrogate_output` |
| Coverage table (added to diffrun after this run exposed the gap) | Flagged `parseSrt`: 89% of calls gave the same empty result, and `getExtendedAlphabeticalHeader`: 86% gave `#`. The 0-mismatch result was weaker than it looked. After fixing the generator, `parseSrt` went from 320 to about 3,200 distinct results, still 0 mismatches |
| divergence-hunter (Haiku, 3 rounds, 123 inputs) | 2 root causes, both nested arrays passed as lyric lines, which the app can never produce. Fixed by enforcing `string[]` on both sides |
| Final, 4 seeds with the fixed generator | 160,496 inputs, 0 mismatches, 271 accepted (lone surrogates) |

The port matched on the first try for Turkish dotless/dotted I in headers, NFC/NFD, JS whitespace in `trim`, and LRC/SRT timestamp math, because the Known traps list in the skill already covered them.

## What porting all of Dopamine would take
Measured with a static scan (imports of Electron, Node I/O, native modules, browser audio).
| Part | Files | Lines (TS, no tests) | Approach | Relative effort |
|---|---|---|---|---|
| Pure logic (services/common/data, no platform imports) | 239 | 11,123 | This method, slice by slice | about 31 slices like this one |
| rxjs / Angular glue | 48 | 4,327 | Stays in TS if the Angular UI is kept (Tauri); becomes channels/state if not | small if kept |
| Platform I/O: SQLite, tags, files, HTTP, Discord, images, audio | 29 | 5,858 | Tier B/C triage (`TRIAGE.md`); diff-test with real audio files and DB snapshots | 3-5x per line |
| UI (components, templates) | n/a | 12,195 TS + 4,462 HTML | Keep it (Tauri) or rewrite it (a new product) | 0 or the biggest part |

A slice like this took about 15 agent steps on the main model plus one Haiku hunter run (about 90k tokens). Extrapolating: the pure logic is about 30 such runs, and the platform layer counts for about 20 more. Before the UI, that is on the order of 50 runs, and tens of millions of input tokens across all of them. To turn that into money, multiply by your provider's current prices.

**Recommendation.** For Dopamine itself, a full port is not worth it: the app works, and the cost is in the UI and the platform layer, not in the logic. The useful version is Tauri with the Angular UI kept, porting only what gains from Rust (indexing, metadata reading, the database layer), each piece diff-tested like this slice.
