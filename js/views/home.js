// The main screen: your next problem, your belt progress and a dense list of what's up next.
// Everything on it is either the problem bank or this browser's own progress, so a new visitor sees an honest zero.
import { $, dayIndex, esc, errorPanel, renderMe, rankBar } from "../lib/ui.js";
import { KYU, LADDER, TOPICS, badge, beltSvg, rankOf, HINT_COST } from "../lib/ranks.js";
import { S, save, award, points, myKyu, touchDay, currentStreak } from "../lib/store.js";
import { LISTED, getProblem, upNext } from "../lib/problems.js";
import { check } from "../lib/answers.js";
import { tex, paras, texParas, safeText } from "../lib/tex.js";
import { renderQuiz } from "./quiz.js";
import { row } from "./problems.js";

const LIST_ROWS = 8;
let skipped = 0;      // how many times "Show another" has been pressed since the last solve
let flash = null;     // the problem you just solved here, to confirm it on the next render

function intro(placed, pts) {
  if (!placed) return `<div class="home-intro">
    <div><h1>Contest maths, belt by belt.</h1><p>Problems in the style of real contests, from AMC 8 to IMO proofs. Try the one below, or let three questions find your level.</p></div>
    <a class="btn" href="#home-quiz" id="ctaQuiz">Find your level</a>
  </div>`;
  const named = S.handle && S.handle !== "you" ? `, ${esc(S.handle)}` : "";
  return `<div class="home-intro">
    <div><h1>Welcome back${named}.</h1><p>You're practising at ${myKyu()} kyu with ${pts} ${pts === 1 ? "point" : "points"}.</p></div>
  </div>`;
}

function nextCard(next, queueLength) {
  const done = flash ? `<div class="flash" id="homeFlash" tabindex="-1" role="status"><span>Solved ${esc(flash.title)}. +${flash.pts} pts.</span><a href="#p-${esc(flash.id)}">See the solution</a></div>` : "";
  if (!next) return `<section class="panel next" aria-labelledby="nextH">
    ${done}<h2 class="sub" id="nextH">You've solved everything in the bank</h2>
    <p class="muted">That's all ${LISTED.length} problems. New ones are on the way, or you can <a href="#duel">race the ghost</a> on the ones you know.</p>
  </section>`;
  return `<section class="panel next belted" style="--belt:${KYU[next.kyu].bg}" aria-labelledby="nextH">
    ${done}
    <div class="next-tag"><span class="eyebrow">Your next problem</span><span class="faint">${TOPICS[next.topic]} · ${next.type === "proof" ? "Proof" : "Answer"} · ${next.type === "proof" ? "up to " : ""}+${KYU[next.kyu].pts} pts</span></div>
    <div class="next-head">${badge(next.kyu, null, "lg")}<h2 id="nextH"><a href="#p-${esc(next.id)}">${esc(next.title)}</a></h2></div>
    <div class="statement" id="nextBox" role="status"><span class="spinner" aria-hidden="true"></span>Loading…</div>
    ${next.type === "answer" ? `
    <form class="answer" id="nextForm" autocomplete="off">
      <input id="nextAns" inputmode="text" autocapitalize="off" spellcheck="false" placeholder="e.g. 42, 25/4 or 6.25" aria-label="Your answer to ${esc(next.title)}" aria-describedby="nextFb">
      <button class="btn primary" type="submit">Submit</button>
    </form>
    <div class="feedback" id="nextFb" role="status"></div>` : ""}
    <div class="next-foot">
      <div class="cta">${next.type === "proof" ? `<a class="btn primary" href="#p-${esc(next.id)}">Write a proof</a>` : `<a class="btn small ghost" href="#p-${esc(next.id)}">Hints and full page</a>`}${queueLength > 1 ? `<button class="btn small ghost" type="button" id="nextSkip">Show another</button>` : ""}</div>
    </div>
  </section>`;
}

function rack(level, pts) {
  const r = rankOf(pts);
  const belts = LADDER.map((k) => {
    const ps = LISTED.filter((p) => p.kyu === k);
    const solved = ps.filter((p) => S.solved[p.id]).length;
    const state = k < level ? "ahead" : k > level ? "passed" : "current";
    return `<a class="rack-belt ${state}" href="#problems-k${k}"${k === level ? ` aria-current="true"` : ""} aria-label="${k} kyu, ${KYU[k].belt} belt: ${solved} of ${ps.length} solved">${beltSvg(k)}<b aria-hidden="true">${k} kyu</b><span class="n" aria-hidden="true">${solved}/${ps.length}</span></a>`;
  }).join("");
  return `<section class="panel rack-panel" aria-labelledby="rackH">
    <div class="rack-top">
      ${badge(r.cur.k, r.cur.label, "lg solo")}
      <div class="rank-text"><h2 class="sub" id="rackH" style="margin:0"><b>${r.cur.label}${r.cur.k ? `, ${KYU[r.cur.k].belt.toLowerCase()} belt` : ""}</b></h2>
      <span class="faint">${pts} pts. ${r.next ? `${r.next.min - pts} more to ${r.next.label}.` : "Top rank."} <a href="#ranks">How ranks work</a></span></div>
    </div>
    ${rankBar(pts)}
    <nav class="rack" aria-label="Problems by belt">${belts}</nav>
  </section>`;
}

function today(potd) {
  if (!potd) return "";
  const solved = S.solved[potd.id];
  return `<section class="panel today" aria-labelledby="todayH">
    <h2 class="side-h" id="todayH">Today's problem</h2>
    <div class="today-t"><a href="#p-${esc(potd.id)}">${esc(potd.title)}</a>${badge(potd.kyu, null, "solo")}</div>
    <span class="faint">${TOPICS[potd.topic]} · ${solved ? "Solved" : `+${KYU[potd.kyu].pts} pts`}</span>
  </section>`;
}

function numbers(pts) {
  const streak = currentStreak();
  const log = S.log.slice(0, 4);
  return `<section class="panel" aria-labelledby="numsH">
    <h2 class="side-h" id="numsH" style="margin-bottom:10px">Your numbers</h2>
    <dl class="nums">
      <div><dt>Points</dt><dd>${pts}</dd></div>
      <div><dt>Solved</dt><dd>${Object.keys(S.solved).length} <small>of ${LISTED.length}</small></dd></div>
      <div><dt>Streak</dt><dd>${streak} <small>${streak === 1 ? "day" : "days"}</small></dd></div>
      <div><dt>Duel rating</dt><dd>${Math.round(S.duel.rating)}</dd></div>
    </dl>
    ${log.length ? `<ul class="mini-log">${log.map((e) => `<li><span>${esc(e.text)}</span><span>${new Date(e.at).toLocaleDateString("en-GB", { day: "numeric", month: "short" })}</span></li>`).join("")}</ul>` : ""}
  </section>`;
}

function notes(placed) {
  return `<details class="note"${placed ? "" : " open"}>
      <summary>How Cevian works</summary>
      <p><b>Solve.</b> From 8 to 4 kyu every problem has one numerical answer, checked the moment you submit. 3 kyu mixes answers and proofs. Solutions unlock once you have it right.</p>
      <p><b>Prove.</b> At 2 and 1 kyu you write proofs. They'll go to two reviewers ranked above the problem, who mark out of 7. For now you self-grade against the rubric.</p>
      <p><b>Duel.</b> One problem, one clock. First correct answer wins, and a wrong answer locks you out for 15 seconds. Today you race a timed ghost.</p>
    </details>
    <details class="note">
      <summary>What this first draft does and doesn't do</summary>
      <ul>
        <li>There are ${LISTED.length} problems so far, across all eight kyu.</li>
        <li>Answers are checked against hashes in the page, and your progress lives in this browser only.</li>
        <li>Friend duels, accounts, peer review and problem submission need a backend, which comes later.</li>
        <li>The leaderboard shows sample players so you can see the layout.</li>
      </ul>
    </details>`;
}

export function renderHome() {
  const pts = points();
  const level = myKyu();
  const placed = pts > 0 || S.placement;
  const queue = upNext(level);
  const next = queue.length ? queue[skipped % queue.length] : null;
  const answers = LISTED.filter((p) => p.type === "answer");
  const potd = answers.length ? answers[dayIndex() % answers.length] : null;
  const rest = queue.filter((p) => p !== next).slice(0, LIST_ROWS);
  $("v-home").innerHTML = `
  ${intro(placed, pts)}
  <div class="home-grid">
    <div class="home-main">
      ${nextCard(next, queue.length)}
      ${rack(level, pts)}
      ${rest.length ? `<section class="panel flush" aria-labelledby="upH">
        <div class="head-row"><h2 class="sub" id="upH">Up next</h2><a href="#problems" class="faint">All ${LISTED.length} problems</a></div>
        <ul class="plist plain">${rest.map(row).join("")}</ul>
      </section>` : ""}
    </div>
    <div class="home-side">
      ${today(potd)}
      <section class="panel quiz" id="quiz" aria-labelledby="quizH"></section>
      ${numbers(pts)}
      ${notes(placed)}
    </div>
  </div>`;
  renderQuiz();
  if (next) fillNext(next);
  if ($("homeFlash")) $("homeFlash").focus({ preventScroll: true });
  flash = null;
  if ($("nextSkip")) $("nextSkip").addEventListener("click", () => { skipped++; renderHome(); $("nextSkip")?.focus(); });
  if ($("ctaQuiz")) $("ctaQuiz").addEventListener("click", (e) => { e.preventDefault(); showQuiz(); });
}

async function fillNext(entry) {
  const box = $("nextBox");
  let p;
  try { p = await getProblem(entry.id); }
  catch { if ($("nextBox") === box) box.innerHTML = errorPanel("this problem"); return; }
  if ($("nextBox") !== box) return;
  box.innerHTML = texParas(p.statement);
  box.removeAttribute("role");
  tex(box);
  const form = $("nextForm");
  if (!form) return;
  const fb = $("nextFb");
  fb.textContent = `Worth ${KYU[p.kyu].pts} pts, minus ${HINT_COST === 0.25 ? "a quarter" : Math.round(HINT_COST * 100) + "%"} for each hint you open.`;
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const val = $("nextAns").value; const r = check(p, val);
    if (r === null) { fb.className = "feedback bad"; fb.textContent = "Enter a number, a fraction like 25/4, or a decimal."; return; }
    if (r) { const got = award(p, "answer"); flash = { id: p.id, title: p.title, pts: got }; skipped = 0; renderMe(); renderHome(); return; }
    S.tries[p.id] = (S.tries[p.id] || 0) + 1; touchDay(); save();
    fb.className = "feedback bad"; fb.textContent = `${val.trim()} is not it. Attempt ${S.tries[p.id]}.`;
  });
}

// Scrolls to the quiz without leaving the home route. #home-quiz is a route so other views can link here.
export function showQuiz() {
  const q = $("quiz");
  if (!q) return;
  q.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "center" });
  const go = $("quizGo") || q.querySelector("input, button, a");
  if (go) go.focus({ preventScroll: true });
}
