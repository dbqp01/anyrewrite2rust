"""Reusable checks for accept.py. diffrun puts this folder on sys.path, so a port's accept.py can do:
    from accept_helpers import ok_value, has_lone_surrogate
Each helper answers one narrow question; the decision to accept stays in the port's accept.py.
"""
import json


def ok_value(out):
    """The value of a {"ok": ...} line, or None for errors and non-JSON lines."""
    try:
        v = json.loads(out)
    except ValueError:
        return None
    return v.get("ok") if isinstance(v, dict) else None


def has_lone_surrogate(v):
    """True if any string inside v holds half a UTF-16 surrogate pair. JS strings can; Rust's `String` can't."""
    if isinstance(v, str):
        return any(0xD800 <= ord(c) <= 0xDFFF for c in v)
    if isinstance(v, list):
        return any(has_lone_surrogate(x) for x in v)
    if isinstance(v, dict):
        return any(has_lone_surrogate(x) for x in v.values())
    return False


def lone_surrogate_output(legacy, new):
    """The original returned a string with a lone surrogate and the port returned a value without one."""
    lo = ok_value(legacy)
    return lo is not None and has_lone_surrogate(lo) and not has_lone_surrogate(ok_value(new))


def lone_surrogate_input(inp, new):
    """The call's arguments hold a lone surrogate, which serde_json refuses, so the port reports SyntaxError."""
    try:
        args = json.loads(inp).get("args", [])
    except (ValueError, AttributeError):
        return False
    return has_lone_surrogate(args) and new.replace(" ", "") == '{"err":"SyntaxError"}'


if __name__ == "__main__":
    assert lone_surrogate_output('{"ok":"\\ud83d-"}', '{"ok":"\\ud83d\\ude00"}')
    assert not lone_surrogate_output('{"ok":"a"}', '{"ok":"b"}')
    assert lone_surrogate_input('{"fn":"f","args":["\\ud800"]}', '{"err":"SyntaxError"}')
    assert not lone_surrogate_input('{"fn":"f","args":["a"]}', '{"err":"SyntaxError"}')
    print("accept_helpers self-check ok")
