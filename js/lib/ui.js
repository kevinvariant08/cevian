// Small shared pieces of the page.
import { S, points } from "./store.js";
import { KYU, badge, rankOf } from "./ranks.js";

export const $ = (id) => document.getElementById(id);
export const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

// The bar fills in your current belt's colour. A black belt would vanish on the rail, so dan ranks use its red rank bar.
export const beltFill = (k) => (k ? KYU[k].bg : KYU[k].tape);

export function renderMe() {
  const pts = points(); const r = rankOf(pts);
  const chip = $("meChip");
  chip.setAttribute("aria-label", `Your rank: ${r.cur.label}, ${pts} points. Open your profile.`);
  chip.innerHTML = `${badge(r.cur.k, r.cur.label)}<span class="me-pts">${pts} pts</span>
    <span class="me-track"><i style="width:${Math.max(2, r.frac * 100)}%;background:${beltFill(r.cur.k)}"></i></span>
    <span class="me-next">${r.next ? `${r.next.min - pts} pts to ${r.next.label}` : "Top rank"}</span>`;
}

// Progress to the next rank, with the belt you're working towards at the end of the bar.
export function rankBar(pts) {
  const r = rankOf(pts);
  return `<div class="rankbar">
    <div class="track" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.round(r.frac * 100)}" aria-label="Progress to next rank"><i style="width:${Math.max(2, r.frac * 100)}%;background:${beltFill(r.cur.k)}"></i></div>
    ${r.next ? badge(r.next.k, r.next.label) : ""}
  </div>`;
}

// Dark unless you've chosen light. The choice has its own key, so it isn't part of your progress and survives a reset.
const THEME_KEY = "kyuclid:theme";
export function initTheme() {
  const btn = $("themeBtn"), root = document.documentElement;
  const sync = () => {
    const light = root.dataset.theme === "light";
    btn.textContent = light ? "Dark theme" : "Light theme";
    btn.setAttribute("aria-label", `Switch to the ${light ? "dark" : "light"} theme`);
  };
  btn.addEventListener("click", () => {
    if (root.dataset.theme === "light") delete root.dataset.theme;
    else root.dataset.theme = "light";
    try { localStorage.setItem(THEME_KEY, root.dataset.theme || "dark"); } catch {}
    sync();
  });
  sync();
}

export const statusTag = (p) => {
  const s = S.solved[p.id];
  if (s && s.how === "proof") return `<span class="status review">Self-graded ${s.grade}/7</span>`;
  if (s) return `<span class="status solved">Solved</span>`;
  if (S.forfeits[p.id]) return `<span class="status forfeit">Forfeited</span>`;
  if (S.proofs[p.id] && S.proofs[p.id].submitted) return `<span class="status review">In review</span>`;
  return "";
};

export const dayIndex = () => Math.floor(Date.now() / 86400000);
export const fmtDate = (t) => new Date(t).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });

// What the list and the problem page say about where a problem comes from.
export const sourceLine = (p) => (p.provenance ? p.provenance.source : p.source);
export const authorOf = (p) => (p.provenance ? p.provenance.author : p.author);

// Shown when a view can't fetch what it needs.
export const errorPanel = (what) => `<div class="panel state" role="alert"><h1 class="h2">Couldn't load ${what}</h1><p class="muted">Check your connection and <a href="">reload the page</a>. Your progress is safe in this browser.</p></div>`;
export const loadingPanel = (what) => `<div class="panel state" role="status"><span class="spinner" aria-hidden="true"></span>Loading ${what}…</div>`;
