"""Divergences a human accepted. Each rule matches a decision in spec.md."""
import json


def _lone_surrogates_dropped(legacy, new):
    # JS truncate can cut an emoji in half; Rust strings can't hold the lone half, so the port drops it
    lo, ne = json.loads(legacy).get("ok"), json.loads(new).get("ok")
    if not isinstance(lo, str) or not isinstance(ne, str):
        return False
    stripped = "".join(c for c in lo if not 0xD800 <= ord(c) <= 0xDFFF)
    return stripped != lo and stripped == ne


REGEX_META = set("{}[]()\\^$?|")


def _has_lone_surrogate(v):
    if isinstance(v, str):
        return any(0xD800 <= ord(c) <= 0xDFFF for c in v)
    return isinstance(v, list) and any(_has_lone_surrogate(x) for x in v)


def accepted(inp, legacy, new):
    if _lone_surrogates_dropped(legacy, new):
        return True
    call = json.loads(inp)
    args = call.get("args", [])
    # input strings with lone surrogates can't even be parsed into a Rust String
    if _has_lone_surrogate(args) and json.loads(new) == {"err": "SyntaxError"}:
        return True
    # sep with regex syntax beyond "." "+" "*": JS and Rust regex dialects differ ({, \p{L}, a{2}...);
    # "$" also covers JS replacement patterns like "$&", which the port inserts literally
    if call.get("fn") == "slugify" and len(args) > 1 and isinstance(args[1], str) and REGEX_META & set(args[1]):
        return True
    # non-string separators (JS coerces null to "null", 5 to "5"): the port rejects them with TypeError
    if call.get("fn") == "slugify" and len(args) > 1 and not isinstance(args[1], str):
        return json.loads(new) == {"err": "TypeError"}
    return False


if __name__ == "__main__":
    assert accepted('{"fn":"truncate","args":["\\ud83d\\ude00",1]}', '{"ok":"\\ud83d\\u2026"}', '{"ok":"\\u2026"}')
    assert not accepted('{"fn":"truncate","args":["ab",1]}', '{"ok":"a\\u2026"}', '{"ok":"b\\u2026"}')
    assert accepted('{"fn":"slugify","args":["a b",null]}', '{"ok":"anullb"}', '{"err":"TypeError"}')
    assert not accepted('{"fn":"slugify","args":["a b","-"]}', '{"ok":"a-b"}', '{"ok":"a_b"}')
    print("accept.py self-check ok")
