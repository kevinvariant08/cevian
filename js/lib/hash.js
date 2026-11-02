// The problem list's URL hash: short tokens joined by "-", then a query string for values that can
// contain "-" themselves. #problems-k54-AN-answer-open?s=vieta-jumping&q=sum&sort=hard&page=2
// Keep this module free of browser globals so it can be tested in Node.
export const SORTS = ["easy", "hard", "popular", "loved"];
export const blankFilters = () => ({ kyu: [], topic: [], type: "all", status: "all", fav: false, sub: "", q: "", sort: "easy", page: 1 });

export const isListHash = (h) => /^#?problems([-?]|$)/.test(h);

export function parseFilters(hash) {
  const F = blankFilters();
  const raw = String(hash).replace(/^#/, "");
  const at = raw.indexOf("?");
  const head = at < 0 ? raw : raw.slice(0, at);
  for (const tok of head.split("-").slice(1)) {
    if (/^k[1-8]+$/.test(tok)) F.kyu = [...new Set(tok.slice(1).split("").map(Number))].sort((a, b) => b - a);
    else if (/^[ACGN]+$/.test(tok)) F.topic = [...new Set(tok.split(""))].sort();
    else if (tok === "answer" || tok === "proof") F.type = tok;
    else if (tok === "open" || tok === "tried" || tok === "solved") F.status = tok;
    else if (tok === "fav") F.fav = true;
  }
  const q = new URLSearchParams(at < 0 ? "" : raw.slice(at + 1));
  F.sub = q.get("s") || "";
  F.q = q.get("q") || "";
  if (SORTS.includes(q.get("sort"))) F.sort = q.get("sort");
  const page = parseInt(q.get("page"), 10);
  if (page > 1) F.page = page;
  return F;
}

export function filtersToHash(F) {
  const toks = ["problems"];
  if (F.kyu.length) toks.push("k" + [...F.kyu].sort((a, b) => b - a).join(""));
  if (F.topic.length) toks.push([...F.topic].sort().join(""));
  if (F.type !== "all") toks.push(F.type);
  if (F.status !== "all") toks.push(F.status);
  if (F.fav) toks.push("fav");
  const q = new URLSearchParams();
  if (F.sub) q.set("s", F.sub);
  if (F.q) q.set("q", F.q);
  if (F.sort !== "easy") q.set("sort", F.sort);
  if (F.page > 1) q.set("page", F.page);
  const qs = q.toString();
  return "#" + toks.join("-") + (qs ? "?" + qs : "");
}
