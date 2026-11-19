"""Divergences the human reviewer accepted (see spec.md, 'Decisiones para el port')."""

I64_MIN, I64_MAX = -(2**63), 2**63 - 1


def accepted(inp, legacy, new):
    # Rust uses i64: overflow is fine only where the original left i64 range (or crashed printing a huge int)
    if new == "err overflow":
        if legacy == "err crash":
            return True
        if legacy.startswith("ok "):
            v = int(legacy[3:])
            return not (I64_MIN <= v <= I64_MAX)
    # Rust only takes ASCII digits; Python's isdigit takes any unicode digit
    if new == "err parse" and any(c.isdigit() and not c.isascii() for c in inp):
        return True
    return False


if __name__ == "__main__":
    assert accepted("2^64", "ok 18446744073709551616", "err overflow")
    assert not accepted("2^62", "ok 4611686018427387904", "err overflow")
    assert accepted("٣+1", "ok 4", "err parse")
    assert not accepted("1+1", "ok 2", "err parse")
    print("accept.py self-check ok")
