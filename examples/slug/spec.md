# textkit: spec extracted from `legacy/textkit.js`

## Contract
stdin `{"fn": "name", "args": [...]}` per line; stdout `{"ok": value}` or `{"err": "ErrorName"}` (via `harness/js_harness.mjs`).

## Functions
```
slugify(s, sep = "-")          textkit.js:3
  s not a string -> TypeError
  NFKD, drop U+0300..U+036F, toLowerCase
  every run of chars outside [a-z0-9] -> sep
  strip leading/trailing sep with RegExp(`^${sep}+|${sep}+$`)   <- sep is NOT escaped
truncate(s, n)                 textkit.js:14
  n not an integer or < 0 -> RangeError (2.0 is an integer, 2.5 is not)
  length and slice in UTF-16 code units, then append "…"
parseSemver(v)                 textkit.js:19
  trim (JS whitespace), match ^v?(\d+)\.(\d+)\.(\d+)(-[0-9A-Za-z.-]+)?$  (\d is ASCII-only in JS)
  no match -> Error; numbers via Number() (doubles: 99999999999999999999 -> 1e20)
wordCount(s)                   textkit.js:25
  number of non-empty pieces of s.split(/\s+/)
```

## Quirks (measured by running the original)
- sep goes into a regex unescaped: `"."` trims the whole slug to `""`; `"("`, `"*"`, `""` throw SyntaxError; `"ab"` means `a` then `b+`.
- sep goes into `String.replace` as a replacement string, so `$&` inserts the matched text.
- JS whitespace (`\s`, `trim`) includes U+FEFF and excludes U+0085; Rust's `char::is_whitespace` is the opposite on both.
- `truncate` can split a surrogate pair and return a lone half.

## Port decisions (human-reviewed; mirrored in accept.py)
- Lone surrogate after truncate: Rust drops it. Accepted (Rust `String` can't hold it).
- Non-string `sep`: Rust returns TypeError instead of coercing. Accepted.
- `$` patterns in `sep`: not emulated. Accepted.
- Regex-in-sep emulated with the `regex` crate on the unescaped sep. It matches JS for plain text and `.`, `+`, `*`, `|`.
  Seps with `{}[]()\^$?` hit dialect differences (a lone `{` is literal in JS and an error in Rust; `\p{L}` is
  literal text in JS and a Unicode class in Rust). Accepted: emulating the JS regex dialect is out of scope.
- Input strings with lone surrogates (`"\ud800a"`): serde_json refuses them, so the port answers SyntaxError. Accepted.
- Found by the divergence-hunter agent (Haiku, 1 round, 47 inputs): a real bug where `truncate` also stripped a
  genuine U+FFFD from the input. Fixed, with a unit test.
- Found by diffrun, not by reading code: Node's `readline` splits on U+2028/U+2029, which misaligned outputs. The harness now splits on `\n` only.
