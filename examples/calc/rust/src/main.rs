//! Port of legacy/calc.py following spec.md. Same line contract: `ok N` / `err KIND`.
use num_bigint::BigInt;
use num_integer::Integer;
use num_traits::{Signed, ToPrimitive, Zero};
use std::io::{self, BufRead, BufWriter, Write};

type R<T> = Result<T, &'static str>;

#[derive(Clone, PartialEq)]
enum Tok {
    Num(BigInt),
    Op(char),
}

// Python frames above the parser (module, main, evaluate) and below each atom (take -> peek).
const PY_LIMIT: usize = 1000;
const PY_OVERHEAD: usize = 3 + 2;
// Python 3.11+ refuses int<->str conversions above this many digits (sys.get_int_max_str_digits).
const PY_MAX_STR_DIGITS: usize = 4300;

fn tokenize(s: &str) -> R<Vec<Tok>> {
    let cs: Vec<char> = s.chars().collect();
    let (mut toks, mut i) = (Vec::new(), 0);
    while i < cs.len() {
        let c = cs[i];
        if c.is_whitespace() {
            i += 1;
        } else if c.is_ascii_digit() {
            let j = i;
            while i < cs.len() && cs[i].is_ascii_digit() {
                i += 1;
            }
            if i - j > PY_MAX_STR_DIGITS {
                return Err("crash");
            }
            let digits: String = cs[j..i].iter().collect();
            toks.push(Tok::Num(digits.parse().unwrap()));
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
    fn peek(&self) -> Option<&Tok> {
        self.t.get(self.i)
    }
    fn take(&mut self) -> Option<Tok> {
        let tok = self.t.get(self.i).cloned();
        self.i += 1;
        tok
    }
    fn is_op(&self, ops: &str) -> bool {
        matches!(self.peek(), Some(Tok::Op(c)) if ops.contains(*c))
    }
    /// Mirrors Python's RecursionError so deep inputs give `crash` at the same depth.
    fn enter(&mut self) -> R<()> {
        self.depth += 1;
        if self.depth + PY_OVERHEAD > PY_LIMIT { Err("crash") } else { Ok(()) }
    }

    fn expr(&mut self) -> R<BigInt> {
        self.enter()?;
        let mut v = self.term()?;
        while self.is_op("+-") {
            let plus = self.take() == Some(Tok::Op('+'));
            let r = self.term()?;
            v = if plus { v + r } else { v - r };
        }
        self.depth -= 1;
        Ok(v)
    }

    fn term(&mut self) -> R<BigInt> {
        self.enter()?;
        let mut v = self.unary()?;
        while self.is_op("*/%") {
            let op = self.take();
            let r = self.unary()?;
            v = match op {
                Some(Tok::Op('*')) => v * r,
                _ if r.is_zero() => return Err("div0"),
                // div_floor/mod_floor match Python's // and %; div_euclid would not for negative divisors
                Some(Tok::Op('/')) => v.div_floor(&r),
                _ => v.mod_floor(&r),
            };
        }
        self.depth -= 1;
        Ok(v)
    }

    fn unary(&mut self) -> R<BigInt> {
        self.enter()?;
        let v = if self.is_op("-") {
            self.take();
            -self.unary()?
        } else {
            self.power()?
        };
        self.depth -= 1;
        Ok(v)
    }

    fn power(&mut self) -> R<BigInt> {
        self.enter()?;
        let base = self.atom()?;
        let v = if self.is_op("^") {
            self.take();
            let exp = self.unary()?;
            if exp.is_negative() {
                return Err("negexp");
            }
            match exp.to_u32() {
                Some(e) if e <= 1000 => base.pow(e),
                _ => return Err("toobig"),
            }
        } else {
            base
        };
        self.depth -= 1;
        Ok(v)
    }

    fn atom(&mut self) -> R<BigInt> {
        self.enter()?;
        let v = match self.take() {
            Some(Tok::Num(n)) => n,
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

fn evaluate(line: &str) -> R<String> {
    let mut p = Parser { t: tokenize(line)?, i: 0, depth: 0 };
    let v = p.expr()?;
    if p.peek().is_some() {
        return Err("parse");
    }
    let s = v.to_string();
    if s.trim_start_matches('-').len() > PY_MAX_STR_DIGITS {
        return Err("crash");
    }
    Ok(s)
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
    fn ok(s: &str) -> R<String> {
        Ok(s.to_string())
    }
    #[test]
    fn precedence_and_errors() {
        assert_eq!(evaluate("2^3^2"), ok("512"));
        assert_eq!(evaluate("-2^2"), ok("-4"));
        assert_eq!(evaluate("(1/0"), Err("div0"));
        assert_eq!(evaluate("1/0 $"), Err("parse"));
        assert_eq!(evaluate("7/-2"), ok("-4"));
        assert_eq!(evaluate("7%-2"), ok("-1"));
        assert_eq!(evaluate("10^30/10^30"), ok("1"));
    }
}
