// Solution figures. They are inlined rather than put in an <img>, because an <img> SVG can't inherit the page's
// colour, and that is how they follow the theme. Each is fetched only once its solution is on the page.
import { texParas } from "./tex.js";

// Not ui.js's: the review page uses this file too, and it has no player state to load.
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const parasOf = (s) => texParas(s).match(/<p>[\s\S]*?<\/p>/g) || [];

function placeholder(f) {
  return `<figure class="sol-fig" data-fig-src="${esc(f.src)}" role="img" aria-label="${esc(f.alt)}"></figure>`;
}

// after_paragraph counts the paragraphs above the figure, so 0 puts it first.
export function solutionHtml(p) {
  const figures = p.solution_figures || [];
  if (!figures.length) return texParas(p.solution);
  const parts = parasOf(p.solution);
  const out = [];
  for (let i = 0; i <= parts.length; i++) {
    for (const f of figures) if (Math.min(f.after_paragraph, parts.length) === i) out.push(placeholder(f));
    if (i < parts.length) out.push(parts[i]);
  }
  return out.join("");
}

const cache = new Map();
function fetchSvg(src) {
  if (!cache.has(src)) cache.set(src, fetch(src).then((r) => {
    if (!r.ok) throw new Error(String(r.status));
    return r.text();
  }).then((text) => {
    if (!text.trimStart().startsWith("<svg")) throw new Error("not an SVG");
    return text;
  }).catch((e) => { cache.delete(src); throw e; }));
  return cache.get(src);
}

// A figure that won't load still gives its description, since the solution can usually be followed without it.
export function inlineFigures(root, fetcher = fetchSvg) {
  return Promise.all([...root.querySelectorAll("[data-fig-src]")].map(async (el) => {
    try {
      el.innerHTML = await fetcher(el.dataset.figSrc);
      const svg = el.querySelector("svg");
      if (svg) svg.setAttribute("aria-hidden", "true");
    } catch {
      el.removeAttribute("role");
      el.innerHTML = `<p class="fig-missing">The figure didn't load. It shows: ${esc(el.getAttribute("aria-label"))}</p>`;
      el.removeAttribute("aria-label");
    }
  }));
}
