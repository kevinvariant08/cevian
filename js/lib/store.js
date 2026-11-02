// This browser's progress, under the localStorage key mathwars:v1. The key predates the rename to Cevian and keeps its name so existing progress survives.
import { KYU, HINT_COST, MIN_HINT_SHARE, PROOF_MARKS, rankOf } from "./ranks.js";

const KEY = "mathwars:v1";
const fresh = () => ({ handle: "you", solved: {}, tries: {}, hints: {}, proofs: {}, votes: {}, duel: { rating: 1200, w: 0, l: 0, d: 0 }, log: [], activity: {}, placement: null });

// Local calendar day, so a streak follows the solver's own midnight.
export const dayKey = (t = Date.now()) => {
  const d = new Date(t);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};

// S is one object for the whole session; resetState() empties it in place so every importer sees the change.
export const S = fresh();
try {
  const raw = localStorage.getItem(KEY);
  if (raw) {
    const saved = JSON.parse(raw);
    Object.assign(S, saved);
    // The 21 first-draft problems left the bank, so their solves stop counting towards rank.
    for (const id of "circle-in-the-square closest-approach cube-the-reciprocal divisor-census domino-corridor egyptian-pairs egz factorial-sandwich floor-staircase last-two-digits neither-fizz-nor-buzz nesbitts-guard polygon-from-one-angle prime-power-desert round-table-no-neighbours square-hunting the-13-14-15-triangle there-and-back twenty-to-four vieta-leap zeros-of-2026".split(" ")) delete S.solved[id];
    // Saves from before the activity map: rebuild it. The log is capped, so solves come from solved[*].at.
    if (!saved.activity) {
      const add = (at) => { const d = dayKey(at); S.activity[d] = (S.activity[d] || 0) + 1; };
      for (const s of Object.values(S.solved)) if (s.at) add(s.at);
      for (const e of S.log) if (!/^(Solved|Won a duel on|Self-graded)/.test(e.text)) add(e.at);
    }
  }
} catch {}

export const save = () => { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch {} };
export const resetState = () => { for (const k of Object.keys(S)) delete S[k]; Object.assign(S, fresh()); save(); };
export const points = () => Object.values(S.solved).reduce((a, s) => a + s.pts, 0);
export const touchDay = () => { const d = dayKey(); S.activity[d] = (S.activity[d] || 0) + 1; };
export const logEvent = (text) => { S.log.unshift({ at: Date.now(), text }); S.log = S.log.slice(0, 30); touchDay(); };

// The kyu to practise at: the points rank, or the placement quiz's answer if that's harder.
export function myKyu() {
  const k = rankOf(points()).cur.k || 1;
  return S.placement && S.placement < k ? S.placement : k;
}

// A streak survives until the end of the next day, so it doesn't read 0 every morning.
export function currentStreak() {
  const DAY = 86400000;
  const has = (d) => (S.activity[dayKey(d)] || 0) > 0;
  const noon = (t) => { const d = new Date(t); d.setHours(12, 0, 0, 0); return d.getTime(); };
  let t = noon(Date.now());
  if (!has(t)) t -= DAY;
  let n = 0;
  while (has(t)) { n++; t = noon(t - DAY); }
  return n;
}

// p needs id, kyu and title, so an index entry or a full problem both work.
export function award(p, how, grade) {
  if (S.solved[p.id]) return 0;
  const base = KYU[p.kyu].pts;
  const usedHints = S.hints[p.id] || 0;
  let pts = Math.max(1, Math.round(base * Math.max(MIN_HINT_SHARE, 1 - HINT_COST * usedHints)));
  if (grade !== undefined) pts = Math.round(base * grade / PROOF_MARKS);
  S.solved[p.id] = { at: Date.now(), pts, how, grade };
  logEvent(`${how === "duel" ? "Won a duel on" : how === "proof" ? "Self-graded " + grade + "/7 on" : "Solved"} ${p.title} (+${pts})`);
  save();
  return pts;
}
