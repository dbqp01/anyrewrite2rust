"""Divergences the human reviewer accepted (see spec.md, 'Decisiones para el port')."""


def accepted(inp, legacy, new):
    # Rust only takes ASCII digits; Python's isdigit takes any unicode digit
    return new == "err parse" and any(c.isdigit() and not c.isascii() for c in inp)


if __name__ == "__main__":
    assert accepted("٣+1", "ok 4", "err parse")
    assert not accepted("1+1", "ok 2", "err parse")
    print("accept.py self-check ok")
