// Boot and router. Routes are hash tokens: #home, #home-quiz, #problems[-filters] (see lib/hash.js), #p-<id>, #ranks, #duel, #profile, #leaderboard.
import { $, renderMe, initTheme, errorPanel, loadingPanel } from "./lib/ui.js";
import { loadIndex } from "./lib/problems.js";
import { loadTaxonomy } from "./lib/taxonomy.js";
import { isListHash } from "./lib/hash.js";
import { renderHome, showQuiz } from "./views/home.js";
import { renderProblems } from "./views/problems.js";
import { renderProblem } from "./views/problem.js";
import { D, stopDuel, renderDuelSetup } from "./views/duel.js";

const VIEWS = ["home", "problems", "problem", "ranks", "duel", "profile", "leaderboard"];
const TITLES = { home: "Cevian: contest maths, belt by belt", problems: "Problems · Cevian", problem: "Problem · Cevian", ranks: "Ranks and belts · Cevian", duel: "Duel · Cevian", profile: "Your profile · Cevian", leaderboard: "Leaderboard · Cevian" };

function lazy(view, load, fn) {
  const el = $("v-" + view);
  if (!el.firstElementChild) el.innerHTML = loadingPanel("this page");
  const at = location.hash;
  load().then((m) => { if (location.hash === at) m[fn](); }).catch(() => { el.innerHTML = errorPanel("this page"); });
}

let firstRoute = true;
function route() {
  const h = (location.hash || "#home").slice(1);
  let view = h, arg = null;
  if (h.startsWith("p-")) { view = "problem"; arg = h.slice(2); }
  if (isListHash(h)) view = "problems";
  const toQuiz = h === "home-quiz";
  if (toQuiz) view = "home";
  if (!VIEWS.includes(view)) view = "home";
  if (view !== "duel") stopDuel();
  document.querySelectorAll("main > .view").forEach((s) => { s.hidden = s.id !== "v-" + view; });
  document.querySelectorAll("#nav a").forEach((a) => {
    if (a.dataset.v === view || (view === "problem" && a.dataset.v === "problems")) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  document.title = TITLES[view];
  try {
    if (view === "home") renderHome();
    if (view === "problems") renderProblems();
    if (view === "problem") renderProblem(arg).catch(() => { $("v-problem").innerHTML = errorPanel("this problem"); });
    if (view === "ranks") lazy(view, () => import("./views/ranks.js"), "renderRanks");
    if (view === "duel" && !D.live) renderDuelSetup();
    if (view === "profile") lazy(view, () => import("./views/profile.js"), "renderProfile");
    if (view === "leaderboard") lazy(view, () => import("./views/leaderboard.js"), "renderBoard");
  } catch (e) {
    console.warn(e);
    $("v-" + view).innerHTML = errorPanel("this page");
  }
  window.scrollTo(0, 0);
  // Tell keyboard and screen-reader users the page changed. Not on first load, where the browser does it.
  if (!firstRoute) $("main").focus({ preventScroll: true });
  firstRoute = false;
  if (toQuiz) showQuiz();
}

initTheme();
renderMe();
Promise.all([loadIndex(), loadTaxonomy()]).then(() => {
  window.addEventListener("hashchange", route);
  route();
}, () => { $("v-home").innerHTML = errorPanel("the problems"); });
