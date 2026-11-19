// Legacy text helpers (CommonJS), the kind of small utility module that gets ported.

function slugify(s, sep = "-") {
  if (typeof s !== "string") throw new TypeError("slugify expects a string");
  return s
    .normalize("NFKD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, sep)
    .replace(new RegExp(`^${sep}+|${sep}+$`, "g"), "");
}

// Cuts to n "characters" as JS counts them (UTF-16 code units) and adds an ellipsis.
function truncate(s, n) {
  if (!Number.isInteger(n) || n < 0) throw new RangeError("bad length");
  return s.length <= n ? s : s.slice(0, n) + "…";
}

function parseSemver(v) {
  const m = /^v?(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?$/.exec(v.trim());
  if (!m) throw new Error("invalid version");
  return { major: Number(m[1]), minor: Number(m[2]), patch: Number(m[3]), pre: m[4] ?? null };
}

function wordCount(s) {
  return s.split(/\s+/).filter(Boolean).length;
}

module.exports = { slugify, truncate, parseSemver, wordCount };
