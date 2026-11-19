// Call exported functions of a JS module (ESM or CommonJS) over JSON lines, so a library can be diff-tested.
// usage: node js_harness.mjs path/to/module.js
// stdin : {"fn": "name", "args": [...]}            one call per line
// stdout: {"ok": <result>} | {"err": "<ErrorName>"}
// console output from the module goes to stderr so it can't corrupt the protocol.
import { pathToFileURL } from "node:url";
import { resolve } from "node:path";

for (const k of ["log", "info", "debug", "warn"]) console[k] = (...a) => process.stderr.write(a.join(" ") + "\n");

const mod = await import(pathToFileURL(resolve(process.argv[2])).href);
const lookup = (name) => mod[name] ?? mod.default?.[name];

// JSON.stringify drops undefined, turns NaN into null and throws on BigInt: tag them instead of losing them
const jsonable = (v) => {
  if (v === undefined) return { __undefined__: true };
  if (typeof v === "bigint") return { __bigint__: v.toString() };
  if (typeof v === "number" && !Number.isFinite(v)) return { __float__: String(v) };
  if (Array.isArray(v)) return v.map(jsonable);
  if (v instanceof Map) return Object.fromEntries([...v].map(([k, x]) => [String(k), jsonable(x)]));
  if (v instanceof Set) return [...v].map(jsonable);
  if (v && typeof v === "object") return Object.fromEntries(Object.entries(v).map(([k, x]) => [k, jsonable(x)]));
  return v;
};

// Not node:readline: it also splits on U+2028/U+2029, which Python and Rust don't, and outputs would misalign.
async function* lines(stream) {
  let buf = "";
  stream.setEncoding("utf8");
  for await (const chunk of stream) {
    buf += chunk;
    let i;
    while ((i = buf.indexOf("\n")) >= 0) {
      yield buf.slice(0, i);
      buf = buf.slice(i + 1);
    }
  }
  if (buf) yield buf;
}

for await (const line of lines(process.stdin)) {
  let res;
  try {
    const call = JSON.parse(line);
    const fn = lookup(call.fn);
    // harness-level error, same name in every harness, so it never looks like original behavior
    res = typeof fn === "function" ? { ok: jsonable(await fn(...(call.args ?? []))) } : { err: "NoSuchFunction" };
  } catch (e) {
    res = { err: e?.name ?? "Throw" };
  }
  process.stdout.write(JSON.stringify(res) + "\n");
}
