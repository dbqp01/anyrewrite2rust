"""Legacy integer calculator. One expression per stdin line -> 'ok N' or 'err KIND'."""
import sys


class CalcError(Exception):
    pass


def tokenize(s):
    toks, i = [], 0
    while i < len(s):
        c = s[i]
        if c.isspace():
            i += 1
        elif c.isdigit():
            j = i
            while j < len(s) and s[j].isdigit():
                j += 1
            toks.append(int(s[i:j]))
            i = j
        elif c in "+-*/%^()":
            toks.append(c)
            i += 1
        else:
            raise CalcError("parse")
    return toks


class Parser:
    def __init__(self, toks):
        self.t, self.i = toks, 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else None

    def take(self):
        tok = self.peek()
        self.i += 1
        return tok

    def expr(self):
        v = self.term()
        while self.peek() in ("+", "-"):
            v = v + self.term() if self.take() == "+" else v - self.term()
        return v

    def term(self):
        v = self.unary()
        while self.peek() in ("*", "/", "%"):
            op, r = self.take(), self.unary()
            if op == "*":
                v *= r
            elif r == 0:
                raise CalcError("div0")
            elif op == "/":
                v //= r
            else:
                v %= r
        return v

    def unary(self):
        if self.peek() == "-":
            self.take()
            return -self.unary()
        return self.power()

    def power(self):
        base = self.atom()
        if self.peek() == "^":
            self.take()
            exp = self.unary()
            if exp < 0:
                raise CalcError("negexp")
            if exp > 1000:
                raise CalcError("toobig")
            return base ** exp
        return base

    def atom(self):
        tok = self.take()
        if isinstance(tok, int):
            return tok
        if tok == "(":
            v = self.expr()
            if self.take() != ")":
                raise CalcError("parse")
            return v
        raise CalcError("parse")


def evaluate(line):
    p = Parser(tokenize(line))
    v = p.expr()
    if p.peek() is not None:
        raise CalcError("parse")
    return v


def main():
    for line in sys.stdin:
        line = line.rstrip("\n")
        try:
            out = f"ok {evaluate(line)}"
        except CalcError as e:
            out = f"err {e}"
        except Exception:
            out = "err crash"
        print(out)


if __name__ == "__main__":
    main()
