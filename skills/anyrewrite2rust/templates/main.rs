//! Rust side of the JSON-lines contract: {"fn","args"} in, {"ok"} | {"err"} out.
//! Fill `dispatch` with one arm per ported function; the harness loop stays as is.
use serde_json::{json, Value};
use std::io::{self, BufRead, BufWriter, Write};

/// Err(kind) must use the same kind names the original reports (e.g. "ValueError", "TypeError").
fn dispatch(name: &str, args: &[Value]) -> Result<Value, String> {
    match name {
        // "my_fn" => Ok(json!(my_fn(arg_str(args, 0)?))),
        _ => Err("NoSuchFunction".into()),
    }
}

#[allow(dead_code)]
fn arg_str(args: &[Value], i: usize) -> Result<&str, String> {
    args.get(i).and_then(Value::as_str).ok_or_else(|| "TypeError".into())
}

#[allow(dead_code)]
fn arg_i64(args: &[Value], i: usize) -> Result<i64, String> {
    args.get(i).and_then(Value::as_i64).ok_or_else(|| "TypeError".into())
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
