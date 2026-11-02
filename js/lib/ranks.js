// Ranks: kyu belts, points grow like Fibonacci.
export const KYU = {
  8: { belt: "White",  bg: "#F4F4F1", ink: "#1B1E33", tape: "#15161C", pts: 2,  anchor: "<b>AMC 8</b>" },
  7: { belt: "Yellow", bg: "#E9C440", ink: "#1B1E33", tape: "#15161C", pts: 3,  anchor: "<b>AMC 8</b> late, AMC 10 P1–10" },
  6: { belt: "Orange", bg: "#E5832A", ink: "#1B1E33", tape: "#15161C", pts: 5,  anchor: "<b>AMC 10/12</b> middle" },
  5: { belt: "Green",  bg: "#2B864B", ink: "#FFFFFF", tape: "#15161C", pts: 8,  anchor: "<b>AMC 12</b> late, AIME 1–5" },
  4: { belt: "Blue",   bg: "#2A64C8", ink: "#FFFFFF", tape: "#15161C", pts: 13, anchor: "<b>AIME 6–10</b>" },
  3: { belt: "Purple", bg: "#6E43B8", ink: "#FFFFFF", tape: "#15161C", pts: 21, anchor: "<b>AIME 11–15</b>, olympiad openers" },
  2: { belt: "Brown",  bg: "#7A4A2B", ink: "#FFFFFF", tape: "#15161C", pts: 34, anchor: "<b>IMO P1/P4</b>, USAMO, USEMO, Balkan MO, CMO" },
  1: { belt: "Red",    bg: "#B8232A", ink: "#FFFFFF", tape: "#15161C", pts: 55, anchor: "<b>IMO P3/P6</b>, the hardest USAMO, USEMO, Balkan MO and CMO" },
  0: { belt: "Black",  bg: "#15161C", ink: "#FFFFFF", tape: "#B8232A", pts: 0,  anchor: "" }
};
// A kyu takes a grind: 20 solves at your own level to leave 8 kyu, rising by 5 a belt to 55 to leave 1 kyu.
export const RANKS = [
  { label: "8 kyu", k: 8, min: 0 }, { label: "7 kyu", k: 7, min: 40 }, { label: "6 kyu", k: 6, min: 115 },
  { label: "5 kyu", k: 5, min: 265 }, { label: "4 kyu", k: 4, min: 545 }, { label: "3 kyu", k: 3, min: 1065 },
  { label: "2 kyu", k: 2, min: 2010 }, { label: "1 kyu", k: 1, min: 3710 }, { label: "1 dan", k: 0, min: 6735 },
  { label: "2 dan", k: 0, min: 10000 }, { label: "3 dan", k: 0, min: 15000 }, { label: "4 dan", k: 0, min: 22000 }
];
// How a solve turns into points. store.js scores with these and the #ranks page quotes them.
export const HINT_COST = 0.25;       // share of the points each opened hint removes
export const MIN_HINT_SHARE = 0.25;  // the least a solve can be worth after hints
export const PROOF_MARKS = 7;        // proofs score points x grade / 7
export const LADDER = [8, 7, 6, 5, 4, 3, 2, 1];
// The rank mark: a belt tied at the waist, with the rank in the knot and the rank bar on each tail. Dan belts carry a stripe per dan.
export const beltVars = (k) => `--belt:${KYU[k].bg}`;
export const beltSvg = (k, num = k) => {
  const b = KYU[k];
  const stripes = k === 0 ? Array.from({ length: num }, (_, i) => `<path d="M${37.5 + i * 2.6} 9v8.2"/>`).join("") : "";
  return `<svg class="belt" viewBox="0 0 48 32" aria-hidden="true"><g fill="${b.bg}" stroke="var(--belt-edge)" stroke-width=".7"><path d="M20.5 19 13 29.5l5.5 2L25.5 20z"/><path d="M27.5 19 35 29.5l-5.5 2L22.5 20z"/><path d="M.5 7q23.5 3.5 47 0v9.5q-23.5 3.5-47 0z"/></g><g fill="${b.tape}"><path d="M15.1 26.6 13 29.5l5.5 2 2-3.2z"/><path d="M32.9 26.6 35 29.5l-5.5 2-2-3.2z"/></g>${stripes ? `<g stroke="#D9B44A" stroke-width="1.3">${stripes}</g>` : ""}<rect x="14.5" y="2.5" width="19" height="19.5" rx="3.5" fill="${b.bg}" stroke="${b.ink}" stroke-opacity=".38" stroke-width=".8"/><text x="24" y="17.8" text-anchor="middle" fill="${b.ink}">${num}</text></svg>`;
};
export const badge = (k, label, cls = "") => {
  const text = label || k + " kyu";
  return `<span class="kyu ${cls}">${beltSvg(k, parseInt(text, 10))}<span class="kyu-l">${text}</span></span>`;
};
export const rankOf = (pts) => {
  let i = 0; while (i + 1 < RANKS.length && pts >= RANKS[i + 1].min) i++;
  const cur = RANKS[i], next = RANKS[i + 1] || null;
  const frac = next ? (pts - cur.min) / (next.min - cur.min) : 1;
  return { cur, next, frac };
};
export const TOPICS = { A: "Algebra", C: "Combinatorics", G: "Geometry", N: "Number theory" };
