// Problem data. data/index.json is the compact manifest for lists; each full problem
// (statement, hints, solution, answer hash) loads on demand from data/problems/<id>.json.
import { S, myKyu } from "./store.js";

const DATA = new URL("../../data/", import.meta.url);

export let INDEX = [];   // every problem in the manifest, easiest first
export let LISTED = [];  // the ones lists, counts and duels show: beta and ranked
export let byId = {};

export async function loadIndex() {
  const res = await fetch(new URL("index.json", DATA));
  if (!res.ok) throw new Error(`data/index.json: HTTP ${res.status}`);
  INDEX = await res.json();
  LISTED = INDEX.filter((p) => p.status === "beta" || p.status === "ranked");
  byId = Object.fromEntries(INDEX.map((p) => [p.id, p]));
}

const full = new Map();     // id -> problem, once loaded
const pending = new Map();  // id -> promise, while loading
export const cachedProblem = (id) => full.get(id) || null;
export function getProblem(id) {
  if (full.has(id)) return Promise.resolve(full.get(id));
  if (!byId[id]) return Promise.resolve(null);
  if (!pending.has(id)) {
    pending.set(id, fetch(new URL(`problems/${id}.json`, DATA))
      .then((res) => { if (!res.ok) throw new Error(`data/problems/${id}.json: HTTP ${res.status}`); return res.json(); })
      .then((p) => { full.set(id, p); return p; })
      .finally(() => pending.delete(id)));
  }
  return pending.get(id);
}

// Stats are real counts, all zero until there is data.
export const likedPct = (p) => (p.stats.solves ? Math.round((100 * p.stats.liked) / p.stats.solves) + "%" : "–");
export const likedRate = (p) => (p.stats.solves ? p.stats.liked / p.stats.solves : -1);

// Every unsolved problem, nearest this kyu first and harder before easier, for the home page's queue.
export function upNext(k = myKyu()) {
  return LISTED.filter((p) => !S.solved[p.id] && !S.forfeits[p.id]).sort((a, b) => Math.abs(a.kyu - k) - Math.abs(b.kyu - k) || a.kyu - b.kyu);
}

// A random unsolved problem at this kyu, or at the nearest kyu that has one (harder first).
export function randomUnsolved(k = myKyu()) {
  const open = LISTED.filter((p) => !S.solved[p.id] && !S.forfeits[p.id]);
  for (let d = 0; d < 8; d++) {
    for (const at of [k - d, k + d]) {
      const pool = open.filter((p) => p.kyu === at);
      if (pool.length) return pool[Math.floor(Math.random() * pool.length)];
    }
  }
  return null;
}
