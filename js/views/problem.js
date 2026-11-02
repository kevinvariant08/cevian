// One problem: statement, answer box or proof editor, hints, solution, rating.
import { $, esc, renderMe, sourceLine, authorOf, fmtDate, errorPanel, loadingPanel } from "../lib/ui.js";
import { KYU, badge, TOPICS, HINT_COST } from "../lib/ranks.js";
import { S, save, award, logEvent, touchDay } from "../lib/store.js";
import { LISTED, byId, cachedProblem, getProblem, likedPct } from "../lib/problems.js";
import { check } from "../lib/answers.js";
import { tex, paras } from "../lib/tex.js";
import { solutionHtml, inlineFigures } from "../lib/figures.js";
import { subtopicName } from "../lib/taxonomy.js";
import { D } from "./duel.js";
import { lastListHash } from "./problems.js";

const REPO_ISSUES = "https://github.com/kevinvariant08/cevian/issues/new";
const REPORT_REASONS = ["The answer or solution looks wrong", "The statement has a typo or is unclear", "A hint gives too much away", "The kyu feels wrong", "It duplicates another problem", "Something else"];
const rubricLine = (r) => `${r.marks} mark${r.marks > 1 ? "s" : ""}: ${r.criterion}`;

// What the h and n keys act on. Registered once, below, because renderProblem runs again after every answer.
let keys = { hint: null, next: null };
const typingIn = (el) => el && (el.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(el.tagName));
document.addEventListener("keydown", (e) => {
  const v = $("v-problem");
  if (!v || v.hidden || e.ctrlKey || e.metaKey || e.altKey || document.querySelector("dialog[open]")) return;
  if (e.key === "Escape" && typingIn(e.target)) { e.target.blur(); return; }
  if (typingIn(e.target)) return;
  if (e.key === "h" && keys.hint) { e.preventDefault(); keys.hint(); }
  if (e.key === "n" && keys.next) { e.preventDefault(); location.hash = "#p-" + keys.next; }
});

// Neighbours in list order at this kyu, wrapping round.
function neighbours(p) {
  const same = LISTED.filter((x) => x.kyu === p.kyu);
  const i = same.findIndex((x) => x.id === p.id);
  if (same.length < 2 || i < 0) return { prev: null, next: null };
  return { prev: same[(i - 1 + same.length) % same.length], next: same[(i + 1) % same.length] };
}

function hintHtml(p, i) { return `<div class="hint" id="hint${i}" tabindex="-1"><b class="faint">Hint ${i + 1}.</b> ${p.hints[i]}</div>`; }

function hintButton(p, used) {
  return `<button class="btn small" type="button" id="hintBtn">Open hint ${used + 1} of ${p.hints.length}${p.type === "answer" ? ` (−${Math.round(HINT_COST * 100)}% pts)` : ""}</button>`;
}

function solvedBanner(p, solved) {
  if (!solved) return "";
  const what = solved.how === "proof" ? `Self-graded ${solved.grade}/7` : solved.how === "duel" ? "Won in a duel" : "Solved";
  const pts = solved.how === "proof" ? `+${solved.pts} provisional pts` : `+${solved.pts} pts`;
  return `<div class="solved-banner" id="solvedBanner" tabindex="-1"><span class="qed" aria-hidden="true"></span><div><b>${what}</b><span class="faint">${pts}${solved.at ? ` · ${fmtDate(solved.at)}` : ""}</span></div></div>`;
}

function reportDialog(p) {
  return `<dialog class="dlg" id="reportDlg" aria-labelledby="reportH">
    <form id="reportForm">
      <h2 class="sub" id="reportH">Report a problem</h2>
      <p class="faint">Problem ID: <code>${esc(p.id)}</code>. This writes a GitHub issue for you to check and send. You'll need a GitHub account.</p>
      <label class="field">What's wrong?<select id="reportWhy" class="sel">${REPORT_REASONS.map((r) => `<option>${esc(r)}</option>`).join("")}</select></label>
      <label class="field">Details (optional)<textarea id="reportText" rows="4" maxlength="1000"></textarea></label>
      <div class="cta"><a class="btn primary" id="reportGo" href="#" target="_blank" rel="noopener">Open the GitHub issue</a><button class="btn" type="button" id="reportClose">Cancel</button></div>
    </form>
  </dialog>`;
}

export async function renderProblem(id, opts = {}) {
  const v = $("v-problem");
  keys = { hint: null, next: null };
  if (!byId[id]) { v.innerHTML = `<div class="panel state"><h1 class="h2">No such problem</h1><p class="muted">That link doesn't match a problem in the bank. <a href="#problems">Back to the problem list</a>.</p></div>`; return; }
  let p = cachedProblem(id);
  if (!p) {
    const at = location.hash;
    v.innerHTML = loadingPanel("the problem");
    try { p = await getProblem(id); }
    catch { if (location.hash === at) v.innerHTML = errorPanel("this problem"); return; }
    if (location.hash !== at) return;
  }
  document.title = `${p.title} · Cevian`;
  const solved = S.solved[p.id];
  const used = S.hints[p.id] || 0;
  const base = KYU[p.kyu].pts;
  const { prev, next } = neighbours(p);
  const unsolvedHere = LISTED.filter((x) => x.kyu === p.kyu && x.id !== p.id && !S.solved[x.id]);
  const upNext = unsolvedHere[0] || LISTED.find((x) => !S.solved[x.id] && x.id !== p.id);
  const nextId = next ? next.id : upNext ? upNext.id : null;
  const pf = S.proofs[p.id] || { text: "", submitted: false };
  const source = sourceLine(p);

  let work;
  if (p.type === "answer") {
    work = solved ? "" : `
    <div class="sec sec-answer"><h2 id="ansH">Your answer</h2>
      <form class="answer" id="ansForm" autocomplete="off">
        <input id="ans" inputmode="text" autocapitalize="off" spellcheck="false" placeholder="e.g. 42, 25/4 or 6.25" aria-labelledby="ansH" aria-describedby="fb">
        <button class="btn primary" type="submit">Submit</button>
      </form>
      <div class="feedback" id="fb" role="status">${S.tries[p.id] ? `${S.tries[p.id]} wrong attempt${S.tries[p.id] > 1 ? "s" : ""} so far. Wrong answers cost nothing here; in a duel they cost 15 seconds.` : `Worth ${base} pts, minus ${HINT_COST === 0.25 ? "a quarter" : Math.round(HINT_COST * 100) + "%"} for each hint you open.`}</div>
    </div>`;
  } else {
    work = `
    <div class="sec"><h2>Your proof</h2>
      <p class="faint" style="margin:0 0 10px">Write in plain text with LaTeX between dollar signs. The preview updates as you type.</p>
      <div class="proof-area">
        <textarea id="proofText" aria-label="Your proof" placeholder="Write your proof here. Maths goes between dollar signs, e.g. $\\frac{a}{b+c} \\ge 0$.">${esc(pf.text)}</textarea>
        <div class="preview" id="proofPrev" role="region" aria-label="Preview of your proof"></div>
      </div>
      <div class="cta" style="margin-top:12px">
        ${pf.submitted ? `<span class="status review">Submitted. In the full site this waits for two reviewers.</span>` : `<button class="btn primary" type="button" id="submitProof">Submit for review</button>`}
      </div>
      <p class="feedback" id="proofFb" role="status"></p>
      ${pf.submitted ? `
      <div class="sec"><h2>Self-grade against the rubric</h2>
        <ol class="rubric">${p.rubric.map((r) => `<li>${esc(rubricLine(r))}</li>`).join("")}</ol>
        <div class="grades" id="grades" role="group" aria-label="Your grade out of 7">${[0, 1, 2, 3, 4, 5, 6, 7].map((g) => `<button type="button" data-g="${g}" aria-pressed="${!!solved && solved.grade === g}" aria-label="Grade ${g} out of 7">${g}</button>`).join("")}</div>
        <p class="faint">${solved ? `Recorded ${solved.grade}/7: +${solved.pts} provisional pts until review.` : `Points are provisional: ${base} × grade ÷ 7.`}</p>
      </div>` : ""}
    </div>`;
  }

  const showSolution = p.type === "answer" ? !!solved : !!pf.submitted;
  const noHints = !p.hints.length ? `<p class="locked">This one has no hints.</p>` : "";
  v.innerHTML = `
  <div class="pbar">
    <a href="${lastListHash()}" class="back">← All problems</a>
    <div class="pbar-r">
      <span class="faint" id="copyNote" role="status"></span>
      <button class="btn small ghost" type="button" id="copyLink">Copy link</button>
      <button class="btn small ghost" type="button" id="reportBtn">Report a problem</button>
    </div>
  </div>
  <div class="pgrid">
    <article class="panel belted${solved ? " is-solved" : ""}" style="--belt:${KYU[p.kyu].bg}">
      ${solvedBanner(p, solved)}
      <div class="phead">${badge(p.kyu, null, "lg")}<h1 class="ptitle">${esc(p.title)}</h1></div>
      <div class="pmeta"><span>${TOPICS[p.topic]}</span><span>${p.type === "proof" ? "Proof, peer-reviewed" : "Single answer, auto-checked"}</span><span>${source ? "Source: " + esc(source) : "Original, by " + esc(authorOf(p))}</span></div>
      <div class="statement" id="statement">${paras(p.statement)}</div>
      ${work}
      <div class="sec"><h2>Hints</h2>
        <div id="hints">${p.hints.slice(0, used).map((_, i) => hintHtml(p, i)).join("")}</div>
        ${noHints}${p.hints.length && used < p.hints.length && !solved ? hintButton(p, used) : p.hints.length && used === 0 ? `<p class="locked">Solved without hints.</p>` : ""}
      </div>
      <div class="sec"><h2>${p.type === "proof" ? "Reference proof" : "Solution"}</h2>
        ${showSolution ? `<div class="solution">${solutionHtml(p)}</div>` : `<p class="locked">${p.type === "proof" ? "Unlocks when you submit a proof." : "Unlocks when you solve it, so nobody can peek their way up the ranks."}</p>`}
      </div>
      ${solved ? `
      <div class="sec"><h2>Rate this problem</h2>
        <div class="vote" id="votes" role="group" aria-label="How did the rank feel?">
          ${[["easier", "Felt easier"], ["right", "Rank feels right"], ["harder", "Felt harder"]].map(([x, n]) => `<button type="button" class="chip" data-vote="${x}" aria-pressed="${S.votes[p.id] === x}">${n}</button>`).join("")}
        </div>
        <p class="faint" id="voteNote" role="status">${S.votes[p.id] ? "Vote saved. Rank votes are how beta problems get their kyu." : "Rank votes are how beta problems get their kyu."}</p>
      </div>` : ""}
      <p class="keys faint"><kbd>Enter</kbd> submits · <kbd>h</kbd> opens the next hint · <kbd>n</kbd> goes to the next problem · <kbd>Esc</kbd> leaves the answer box</p>
    </article>
    <aside class="side" aria-label="About this problem">
      <div class="panel">
        <dl class="kvlist">
          <dt>Rank</dt><dd>${p.kyu} kyu · ${KYU[p.kyu].belt}</dd>
          <dt>Worth</dt><dd>${base} pts</dd>
          ${p.stats.solves ? `<dt>Solves</dt><dd>${p.stats.solves.toLocaleString("en-GB")}</dd>
          <dt>Liked by</dt><dd>${likedPct(p)}</dd>` : ""}
          <dt>Your status</dt><dd>${solved ? (solved.how === "proof" ? "self-graded" : "solved") : "open"}</dd>
        </dl>
        ${solved && p.subtopics.length ? `<div class="tags">${p.subtopics.map((s) => `<a class="tag" href="#problems?s=${encodeURIComponent(s)}">${esc(subtopicName(s))}</a>`).join("")}</div>` : ""}
      </div>
      ${p.type === "answer" ? `<div class="panel"><h2 class="side-h">Race someone on this kyu</h2><p class="faint" style="margin:4px 0 12px">A random ${p.kyu} kyu problem against the clock.</p><a class="btn" href="#duel" id="duelHere">Duel at ${p.kyu} kyu</a></div>` : ""}
      ${upNext ? `<div class="panel"><h2 class="side-h">Next unsolved</h2><div class="side-next"><b>${esc(upNext.title)}</b>${badge(upNext.kyu, null, "solo")}</div><a class="btn small" href="#p-${upNext.id}">Open</a></div>` : ""}
    </aside>
  </div>
  ${prev ? `<nav class="pnav" aria-label="Other problems at ${p.kyu} kyu">
    <a class="pnav-a" rel="prev" href="#p-${prev.id}"><span class="faint">← Previous at ${p.kyu} kyu</span><b>${esc(prev.title)}</b></a>
    <a class="pnav-a right" rel="next" href="#p-${next.id}"><span class="faint">Next at ${p.kyu} kyu →</span><b>${esc(next.title)}</b></a>
  </nav>` : ""}
  ${reportDialog(p)}`;

  keys.next = nextId;
  function openHint() {
    const n = S.hints[p.id] || 0;
    if (S.solved[p.id] || n >= p.hints.length) return;
    S.hints[p.id] = n + 1; save();
    $("hints").insertAdjacentHTML("beforeend", hintHtml(p, n));
    const el = $("hint" + n);
    tex(el);
    const btn = $("hintBtn");
    if (n + 1 < p.hints.length) btn.outerHTML = hintButton(p, n + 1);
    else btn.remove();
    if ($("hintBtn")) $("hintBtn").addEventListener("click", openHint);
    el.focus();
  }
  if ($("hintBtn")) { keys.hint = openHint; $("hintBtn").addEventListener("click", openHint); }

  if ($("ansForm")) $("ansForm").addEventListener("submit", (e) => {
    e.preventDefault();
    const val = $("ans").value; const r = check(p, val); const fb = $("fb");
    if (r === null) { fb.className = "feedback bad"; fb.textContent = "Enter a number, a fraction like 25/4, or a decimal."; return; }
    if (r) { award(p, "answer"); renderMe(); renderProblem(p.id, { focus: "solvedBanner" }); return; }
    S.tries[p.id] = (S.tries[p.id] || 0) + 1; touchDay(); save();
    fb.className = "feedback bad"; fb.textContent = `${val.trim()} is not it. Attempt ${S.tries[p.id]}.`;
  });
  if ($("duelHere")) $("duelHere").addEventListener("click", () => { D.kyu = p.kyu; });
  if ($("proofText")) {
    const ta = $("proofText"), pv = $("proofPrev");
    let timer = null;
    const draw = () => { pv.innerHTML = ta.value.trim() ? paras(esc(ta.value)) : `<span class="faint">Your rendered proof appears here.</span>`; tex(pv); };
    draw();
    ta.addEventListener("input", () => { S.proofs[p.id] = Object.assign(S.proofs[p.id] || {}, { text: ta.value }); save(); clearTimeout(timer); timer = setTimeout(draw, 350); });
  }
  if ($("submitProof")) $("submitProof").addEventListener("click", () => {
    const t = $("proofText").value.trim();
    if (t.length < 40) { $("proofText").focus(); $("proofFb").className = "feedback bad"; $("proofFb").textContent = "Write at least a few lines before submitting."; return; }
    S.proofs[p.id] = { text: t, submitted: true }; logEvent(`Submitted a proof for ${p.title}`); save(); renderProblem(p.id);
  });
  if ($("grades")) $("grades").querySelectorAll("button").forEach((b) => b.addEventListener("click", () => {
    const g = +b.dataset.g; delete S.solved[p.id];
    if (g > 0) award(p, "proof", g); else save();
    renderMe(); renderProblem(p.id);
  }));
  if ($("votes")) $("votes").querySelectorAll("button").forEach((b) => b.addEventListener("click", () => {
    S.votes[p.id] = b.dataset.vote; save();
    $("votes").querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", x === b));
    $("voteNote").textContent = "Vote saved. Rank votes are how beta problems get their kyu.";
  }));

  $("copyLink").addEventListener("click", async () => {
    const note = $("copyNote");
    try { await navigator.clipboard.writeText(location.href); note.textContent = "Link copied."; }
    catch { note.textContent = location.href; }
  });
  const dlg = $("reportDlg");
  const issueUrl = () => {
    const why = $("reportWhy").value;
    const body = `Problem: ${p.id} (${p.title}, ${p.kyu} kyu)\nLink: ${location.href}\n\nWhat's wrong: ${why}\n\n${$("reportText").value.trim()}`;
    return `${REPO_ISSUES}?title=${encodeURIComponent(`Problem report: ${p.id}`)}&body=${encodeURIComponent(body)}`;
  };
  const refreshIssue = () => { $("reportGo").href = issueUrl(); };
  $("reportBtn").addEventListener("click", () => { refreshIssue(); dlg.showModal(); });
  $("reportWhy").addEventListener("change", refreshIssue);
  $("reportText").addEventListener("input", refreshIssue);
  $("reportClose").addEventListener("click", () => dlg.close());
  $("reportForm").addEventListener("submit", (e) => e.preventDefault());
  $("reportGo").addEventListener("click", () => dlg.close());

  // After a re-render, keep the reader where the change happened.
  if (opts.focus && $(opts.focus)) $(opts.focus).focus({ preventScroll: true });
  tex(v.querySelector("article"));
  // Only an unlocked solution has placeholders, so nothing is fetched before then.
  inlineFigures(v);
}
