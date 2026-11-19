//! Port of legacy/textkit.js. Contract: {"fn","args"} in, {"ok"} | {"err"} out (see spec.md).
use regex::Regex;
use serde_json::{json, Value};
use std::io::{self, BufRead, BufWriter, Write};
use unicode_normalization::UnicodeNormalization;

/// JS `\s` and `String.prototype.trim` whitespace. Not Rust's `char::is_whitespace`:
/// JS includes U+FEFF and excludes U+0085.
fn js_space(c: char) -> bool {
    matches!(c, '\t' | '\n' | '\u{b}' | '\u{c}' | '\r' | ' ' | '\u{a0}' | '\u{1680}' | '\u{2000}'..='\u{200a}'
        | '\u{2028}' | '\u{2029}' | '\u{202f}' | '\u{205f}' | '\u{3000}' | '\u{feff}')
}

fn slugify(s: &str, sep: &str) -> Result<String, String> {
    let folded: String = s.nfkd().filter(|c| !('\u{300}'..='\u{36f}').contains(c)).collect::<String>().to_lowercase();
    let mut out = String::new();
    let mut in_run = false;
    for c in folded.chars() {
        if c.is_ascii_lowercase() || c.is_ascii_digit() {
            out.push(c);
            in_run = false;
        } else if !in_run {
            out.push_str(sep);
            in_run = true;
        }
    }
    // The original builds this regex from `sep` unescaped, so "." trims everything and "(" throws.
    let trim = Regex::new(&format!("^{sep}+|{sep}+$")).map_err(|_| "SyntaxError")?;
    if sep.is_empty() {
        return Err("SyntaxError".into()); // JS rejects /^+|+$/ ("nothing to repeat")
    }
    Ok(trim.replace_all(&out, "").into_owned())
}

/// Counts and cuts in UTF-16 code units, like JS `length` and `slice`.
fn truncate(s: &str, n: usize) -> String {
    let units: Vec<u16> = s.encode_utf16().collect();
    if units.len() <= n {
        return s.to_string();
    }
    // A cut inside a surrogate pair leaves a lone half in JS; Rust strings can't hold it, so only that
    // half is dropped (accepted divergence, see accept.py). The input was valid, so the cut is the only break.
    let end = if n > 0 && (0xD800..0xDC00).contains(&units[n - 1]) { n - 1 } else { n };
    String::from_utf16(&units[..end]).expect("cut only splits at the end") + "…"
}

fn parse_semver(v: &str) -> Result<Value, String> {
    let re = Regex::new(r"^v?([0-9]+)\.([0-9]+)\.([0-9]+)(?:-([0-9A-Za-z.-]+))?$").unwrap();
    let m = re.captures(v.trim_matches(js_space)).ok_or("Error")?;
    let num = |i: usize| js_number(&m[i]);
    Ok(json!({ "major": num(1), "minor": num(2), "patch": num(3), "pre": m.get(4).map(|g| g.as_str()) }))
}

/// `Number("123")`: a double; print as an integer when it is one, like JSON.stringify.
fn js_number(digits: &str) -> Value {
    let f: f64 = digits.parse().unwrap();
    if f < 9_007_199_254_740_992.0 { json!(f as i64) } else { json!(f) }
}

fn word_count(s: &str) -> usize {
    s.split(js_space).filter(|w| !w.is_empty()).count()
}

fn dispatch(name: &str, args: &[Value]) -> Result<Value, String> {
    let s = || args.first().and_then(Value::as_str).ok_or_else(|| "TypeError".to_string());
    match name {
        "slugify" => {
            let sep = match args.get(1) {
                None => "-",
                Some(Value::String(x)) => x.as_str(),
                Some(_) => return Err("TypeError".into()), // non-string sep: accepted divergence
            };
            Ok(json!(slugify(s()?, sep)?))
        }
        "truncate" => {
            let s = s()?;
            match args.get(1).and_then(Value::as_f64) {
                Some(n) if n >= 0.0 && n.fract() == 0.0 => Ok(json!(truncate(s, n.min(usize::MAX as f64) as usize))),
                _ => Err("RangeError".into()),
            }
        }
        "parseSemver" => parse_semver(s()?),
        "wordCount" => Ok(json!(word_count(s()?))),
        _ => Err("NoSuchFunction".into()),
    }
}

fn main() {
    let mut w = BufWriter::new(io::stdout().lock());
    for line in io::stdin().lock().lines() {
        let line = line.expect("stdin must be UTF-8");
        let res = match serde_json::from_str::<Value>(&line) {
            Ok(call) => {
                let name = call["fn"].as_str().unwrap_or("");
                let args = call["args"].as_array().map(Vec::as_slice).unwrap_or(&[]);
                match dispatch(name, args) {
                    Ok(v) => json!({ "ok": v }),
                    Err(k) => json!({ "err": k }),
                }
            }
            Err(_) => json!({ "err": "SyntaxError" }),
        };
        writeln!(w, "{res}").unwrap();
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn quirks() {
        assert_eq!(slugify("Héllo Wörld!", "-").unwrap(), "hello-world");
        assert_eq!(slugify("Hi there!", ".").unwrap(), "");
        assert!(slugify("x", "(").is_err());
        assert_eq!(truncate("hello", 3), "hel…");
        assert_eq!(truncate("a😀b", 2), "a…");
        assert_eq!(truncate("\u{fffd}\u{fffd}x", 1), "\u{fffd}…"); // found by divergence-hunter
        assert_eq!(word_count("\u{feff}a\u{85}b"), 1);
    }
}
