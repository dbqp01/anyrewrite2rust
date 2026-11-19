"""Self-check for diffrun's comparison. run: python test_diffrun.py"""
from diffrun import equal, kind

assert equal('{"ok": 1}', '{"ok":1.0}', True, 0)
assert equal('{"a":1,"b":[1,2]}', '{"b":[1,2],"a":1}', True, 0)
assert not equal('{"ok": true}', '{"ok": 1}', True, 0)
assert equal('{"ok": 0.1}', '{"ok": 0.10000000001}', True, 1e-9)
assert not equal('{"ok": 0.1}', '{"ok": 0.2}', True, 1e-9)
assert not equal('ok 1', 'ok 1.0', False, 0)
assert kind('{"err":"TypeError"}') == "err TypeError" and kind("err div0") == "err div0" and kind("ok 5") == "ok"
print("diffrun self-check ok")
