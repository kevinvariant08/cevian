// "Find your level": one answer problem per kyu from 8 to 4. Starts in the middle, goes harder after a
// right answer and easier after a wrong one, and stops at a kyu it has already asked. Three questions at most.
import { $, esc, renderMe, errorPanel } from "../lib/ui.js";
import { badge } from "../lib/ranks.js";
import { S, save, award, points } from "../lib/store.js";
import { LISTED, getProblem } from "../lib/problems.js";
import { check } from "../lib/answers.js";
import { tex, paras, texParas, safeText } from "../lib/tex.js";

const LADDER = [8, 7, 6, 5, 4];
const START = 6;
// Lives outside the render so a quiz in progress survives leaving the home page.
let Q = null;

const pool = (k) => LISTED.filter((p) => p.type === "answer" && p.kyu === k);
const available = () => LADDER.filter((k) => pool(k).length);

function pick(k) {
  const all = pool(k), open = all.filter((p) => !S.solved[p.id]);
  const from = open.length ? open : all;
  return from[Math.floor(Math.random() * from.length)];
}

// The next kyu to ask, or null when the quiz is over. Levels with no problems are stepped over.
function nextKyu(k, right) {
  const asked = new Set(Q.asked.map((a) => a.k));
  const dir = right ? -1 : 1;
  for (let at = k + dir; at >= 4 && at <= 8; at += dir) {
    if (asked.has(at)) return null;
    if (pool(at).length) return at;
  }
  return null;
}

const start = () => {
  const levels = available();
  const k = levels.includes(START) ? START : levels[0];
  Q = { k, asked: [], p: null, result: null };
  ask();
};

async function ask() {
  const host = $("quiz");
  host.innerHTML = `<div class="state" role="status"><span class="spinner" aria-hidden="true"></span>Loading the question…</div>`;
  try { Q.p = await getProblem(pick(Q.k).id); }
  catch { host.innerHTML = errorPanel("the question"); return; }
  if ($("quiz") === host) draw();
}

function finish() {
  const right = Q.asked.filter((a) => a.right).map((a) => a.k);
  Q.result = right.length ? Math.min(...right) : 8;
  S.placement = Q.result; save(); renderMe();
  draw();
}

function answer(right) {
  Q.asked.push({ k: Q.k, right });
  if (right) { award(Q.p, "answer"); renderMe(); }
  const next = nextKyu(Q.k, right);
  if (next === null) return finish();
  Q.k = next; Q.p = null;
  ask();
}

function draw() {
  const host = $("quiz");
  if (!host) return;
  if (!Q) {
    const placed = S.placement;
    host.innerHTML = `
      <h2 class="sub" id="quizH">Find your level</h2>
      <p class="muted">Up to three problems, from ${LADDER[0]} to ${LADDER[LADDER.length - 1]} kyu. They get harder when you're right and easier when you're not.</p>
      ${placed ? `<p class="faint">Last time you placed at ${placed} kyu.</p>` : ""}
      <div class="cta"><button class="btn primary" type="button" id="quizGo">${placed ? "Retake the quiz" : "Start the quiz"}</button></div>`;
    $("quizGo").addEventListener("click", () => { start(); });
    return;
  }
  if (Q.result) {
    const k = Q.result;
    const summary = Q.asked.map((a) => `<li>${badge(a.k)} ${a.right ? "Right" : "Missed"}</li>`).join("");
    host.innerHTML = `
      <h2 class="sub" id="quizH" tabindex="-1">Start at ${k} kyu</h2>
      <p class="muted">${Q.asked.some((a) => a.right) ? `The ${k} kyu problem was the hardest one you got right. Right answers count as solves, so you've got ${points()} ${points() === 1 ? "point" : "points"} already.` : `Start with the warm-ups. They're quick, and the belts go up fast from there.`}</p>
      <ul class="quiz-log">${summary}</ul>
      <div class="cta"><a class="btn primary" href="#problems-k${k}-open">Unsolved at ${k} kyu</a><button class="btn" type="button" id="quizAgain">Retake</button></div>`;
    $("quizAgain").addEventListener("click", () => { start(); });
    $("quizH").focus({ preventScroll: true });
    return;
  }
  if (!Q.p) { ask(); return; }  // still loading when the home page was last left
  const n = Q.asked.length + 1;
  const p = Q.p;
  host.innerHTML = `
    <div class="quiz-head"><h2 class="sub" id="quizH" tabindex="-1">Question ${n}</h2>${badge(p.kyu)}</div>
    <div class="statement quiz-q" id="quizQ">${texParas(p.statement)}</div>
    <form class="answer" id="quizForm" autocomplete="off">
      <input id="quizAns" inputmode="text" autocapitalize="off" spellcheck="false" placeholder="e.g. 42, 25/4 or 6.25" aria-label="Your answer to question ${n}">
      <button class="btn primary" type="submit">Submit</button>
      <button class="btn ghost" type="button" id="quizSkip">I don't know</button>
    </form>
    <div class="feedback" id="quizFb" role="status"></div>`;
  tex($("quizQ"));
  $("quizH").focus({ preventScroll: true });
  $("quizForm").addEventListener("submit", (e) => {
    e.preventDefault();
    const r = check(p, $("quizAns").value);
    if (r === null) { $("quizFb").className = "feedback bad"; $("quizFb").textContent = "Enter a number, a fraction like 25/4, or a decimal."; return; }
    answer(r);
  });
  $("quizSkip").addEventListener("click", () => answer(false));
}

// Draws the quiz into a #quiz element on the home page.
export function renderQuiz() {
  if (!available().length) {
    $("quiz").innerHTML = `<h2 class="sub">Find your level</h2><p class="muted">The quiz needs answer problems from ${esc(LADDER[0])} to ${esc(LADDER[LADDER.length - 1])} kyu, and there are none in the bank yet.</p>`;
    return;
  }
  // A question that's still open was rendered before: draw it again rather than asking a new one.
  draw();
}
