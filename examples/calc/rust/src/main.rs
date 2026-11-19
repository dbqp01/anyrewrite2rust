//! Port of legacy/calc.py following spec.md. Same line contract: `ok N` / `err KIND`.
use std::io::{self, BufRead, BufWriter, Write};

type R<T> = Result<T, &'static str>;

#[derive(Clone, Copy, PartialEq)]
enum Tok {
    Num(i64),
    /// literal that does not fit i64; only an error once the parser reaches it, like the original
    Big,
    Op(char),
}

// Python frames above the parser (module, main, evaluate) and below each atom (take -> peek).
const PY_LIMIT: usize = 1000;
const PY_OVERHEAD: usize = 3 + 2;

fn tokenize(s: &str) -> R<Vec<Tok>> {
    let cs: Vec<char> = s.chars().collect();
    let (mut toks, mut i) = (Vec::new(), 0);
    while i < cs.len() {
        let c = cs[i];
        if c.is_whitespace() {
            i += 1;
        } else if c.is_ascii_digit() {
            let mut v: Option<i64> = Some(0);
            while i < cs.len() && cs[i].is_ascii_digit() {
                let d = cs[i] as i64 - '0' as i64;
                v = v.and_then(|v| v.checked_mul(10)).and_then(|v| v.checked_add(d));
                i += 1;
            }
            toks.push(v.map_or(Tok::Big, Tok::Num));
        } else if "+-*/%^()".contains(c) {
            toks.push(Tok::Op(c));
            i += 1;
        } else {
            return Err("parse");
        }
    }
    Ok(toks)
}

struct Parser {
    t: Vec<Tok>,
    i: usize,
    depth: usize,
}

impl Parser {
    fn peek(&self) -> Option<Tok> {
        self.t.get(self.i).copied()
    }
    fn take(&mut self) -> Option<Tok> {
        let tok = self.peek();
        self.i += 1;
        tok
    }
    fn is_op(&self, ops: &str) -> bool {
        matches!(self.peek(), Some(Tok::Op(c)) if ops.contains(c))
    }
    /// Mirrors Python's RecursionError so deep inputs give `crash` at the same depth.
    fn enter(&mut self) -> R<()> {
        self.depth += 1;
        if self.depth + PY_OVERHEAD > PY_LIMIT { Err("crash") } else { Ok(()) }
    }

    fn expr(&mut self) -> R<i64> {
        self.enter()?;
        let mut v = self.term()?;
        while self.is_op("+-") {
            let plus = self.take() == Some(Tok::Op('+'));
            let r = self.term()?;
            v = if plus { v.checked_add(r) } else { v.checked_sub(r) }.ok_or("overflow")?;
        }
        self.depth -= 1;
        Ok(v)
    }

    fn term(&mut self) -> R<i64> {
        self.enter()?;
        let mut v = self.unary()?;
        while self.is_op("*/%") {
            let op = self.take();
            let r = self.unary()?;
            v = match op {
                Some(Tok::Op('*')) => v.checked_mul(r).ok_or("overflow")?,
                _ if r == 0 => return Err("div0"),
                Some(Tok::Op('/')) => floor_div(v, r)?,
                _ => floor_mod(v, r),
            };
        }
        self.depth -= 1;
        Ok(v)
    }

    fn unary(&mut self) -> R<i64> {
        self.enter()?;
        let v = if self.is_op("-") {
            self.take();
            self.unary()?.checked_neg().ok_or("overflow")?
        } else {
            self.power()?
        };
        self.depth -= 1;
        Ok(v)
    }

    fn power(&mut self) -> R<i64> {
        self.enter()?;
        let base = self.atom()?;
        let v = if self.is_op("^") {
            self.take();
            let exp = self.unary()?;
            if exp < 0 {
                return Err("negexp");
            }
            if exp > 1000 {
                return Err("toobig");
            }
            base.checked_pow(exp as u32).ok_or("overflow")?
        } else {
            base
        };
        self.depth -= 1;
        Ok(v)
    }

    fn atom(&mut self) -> R<i64> {
        self.enter()?;
        let v = match self.take() {
            Some(Tok::Num(n)) => n,
            Some(Tok::Big) => return Err("overflow"),
            Some(Tok::Op('(')) => {
                let v = self.expr()?;
                if self.take() != Some(Tok::Op(')')) {
                    return Err("parse");
                }
                v
            }
            _ => return Err("parse"),
        };
        self.depth -= 1;
        Ok(v)
    }
}

fn floor_div(a: i64, b: i64) -> R<i64> {
    a.checked_div_euclid(b).ok_or("overflow")
}

fn floor_mod(a: i64, b: i64) -> i64 {
    a.rem_euclid(b)
}

fn evaluate(line: &str) -> R<i64> {
    let mut p = Parser { t: tokenize(line)?, i: 0, depth: 0 };
    let v = p.expr()?;
    if p.peek().is_some() {
        return Err("parse");
    }
    Ok(v)
}

fn main() {
    let out = io::stdout();
    let mut w = BufWriter::new(out.lock());
    for line in io::stdin().lock().lines() {
        let line = line.expect("stdin must be UTF-8");
        match evaluate(&line) {
            Ok(v) => writeln!(w, "ok {v}"),
            Err(k) => writeln!(w, "err {k}"),
        }
        .unwrap();
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn precedence_and_errors() {
        assert_eq!(evaluate("2^3^2"), Ok(512));
        assert_eq!(evaluate("-2^2"), Ok(-4));
        assert_eq!(evaluate("(1/0"), Err("div0"));
        assert_eq!(evaluate("1/0 $"), Err("parse"));
    }
}
