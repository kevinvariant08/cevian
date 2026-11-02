// Duel against a timed ghost.
import { $, esc, renderMe, errorPanel } from "../lib/ui.js";
import { KYU, badge, rankOf } from "../lib/ranks.js";
import { S, save, award, logEvent, points } from "../lib/store.js";
import { LISTED, getProblem } from "../lib/problems.js";
import { check } from "../lib/answers.js";
import { tex, paras, texParas, safeText } from "../lib/tex.js";

const GHOST = { 8: { t: 45, r: 900 }, 7: { t: 70, r: 1050 }, 6: { t: 110, r: 1200 }, 5: { t: 170, r: 1350 }, 4: { t: 260, r: 1500 }, 3: { t: 420, r: 1700 } };
// The problem page sets D.kyu for its "Duel at N kyu" button.
export const D = { kyu: 5, live: null, starting: false };
const fmt = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
export function stopDuel() { if (D.live) { clearInterval(D.live.tick); D.live = null; } }

export function renderDuelSetup() {
  const kyus = Object.keys(GHOST).map(Number).sort((a, b) => b - a);
  const d = S.duel;
  $("v-duel").innerHTML = `
  <div><h1 class="h2">Duel</h1><p class="muted lede-s">One problem, one clock. Your rating is ${Math.round(d.rating)}.</p></div>
  <div class="duel-setup">
    <div class="panel">
      <h2 class="sub" id="pickH">Pick a kyu</h2>
      <div class="frow" style="margin:10px 0 18px" role="group" aria-labelledby="pickH">${kyus.map((k) => `<button type="button" class="chip kchip" data-k="${k}" aria-pressed="${D.kyu === k}" aria-label="${k} kyu">${badge(k)}</button>`).join("")}</div>
      <h2 class="sub">Opponent</h2>
      <div style="margin-top:10px">
        <label class="opt"><input type="radio" name="opp" checked><span><b>Ghost solver</b><span class="faint">Plays like a typical ${D.kyu} kyu solver, about ${fmt(GHOST[D.kyu].t)} per problem. Rated ${GHOST[D.kyu].r}.</span></span></label>
        <label class="opt off"><input type="radio" name="opp" disabled><span><b>A friend, by link</b><span class="faint">Needs accounts and live rooms, which this draft doesn't have yet.</span></span></label>
      </div>
      <div class="cta" style="margin-top:18px"><button class="btn primary" type="button" id="startDuel">Start duel</button></div>
      <p class="feedback bad" id="duelNote" role="status"></p>
    </div>
    <div class="panel">
      <h2 class="sub">Rules</h2>
      <ul class="rubric">
        <li>Both sides see the same answer problem at the same moment.</li>
        <li>First correct answer wins. A wrong answer locks your box for 15 seconds.</li>
        <li>If nobody solves it before the time limit, the duel is a draw.</li>
        <li>Winning also counts as solving the problem, so it earns kyu points.</li>
      </ul>
      <dl class="kvlist" style="margin-top:14px">
        <dt>Duel rating</dt><dd>${Math.round(d.rating)}</dd>
        <dt>Record</dt><dd>${d.w}W ${d.l}L ${d.d}D</dd>
      </dl>
    </div>
  </div>`;
  $("v-duel").querySelectorAll("[data-k]").forEach((b) => b.addEventListener("click", () => { D.kyu = +b.dataset.k; renderDuelSetup(); }));
  $("startDuel").addEventListener("click", startDuel);
}

async function startDuel() {
  if (D.starting || D.live) return;
  const pool = LISTED.filter((p) => p.type === "answer" && p.kyu === D.kyu);
  if (!pool.length) { if ($("duelNote")) $("duelNote").textContent = `There are no answer problems at ${D.kyu} kyu yet. Pick another belt.`; return; }
  const fresh = pool.filter((p) => !S.solved[p.id]);
  const pick = (fresh.length ? fresh : pool)[Math.floor(Math.random() * (fresh.length ? fresh.length : pool.length))];
  D.starting = true;
  let p;
  try { p = await getProblem(pick.id); }
  catch { $("v-duel").innerHTML = errorPanel("this duel's problem"); return; }
  finally { D.starting = false; }
  if (location.hash !== "#duel") return;
  const g = GHOST[D.kyu];
  const ghostAt = Math.random() < 0.12 ? Infinity : g.t * (0.55 + Math.random() * 0.95);
  D.live = { p, start: Date.now(), ghostAt, limit: g.t * 2.5, lockUntil: 0, tries: 0, done: false };
  $("v-duel").innerHTML = `
  <h1 class="sr-only">Duel at ${D.kyu} kyu</h1>
  <div class="scoreboard">
    <div><div class="side-name">${badge(rankOf(points()).cur.k, rankOf(points()).cur.label)} ${esc(S.handle)}</div><div class="clock" id="myClock" aria-label="Your time" role="timer">0:00</div></div>
    <div class="vs">vs</div>
    <div class="right"><div class="side-name">Ghost ${badge(D.kyu)}</div><div class="clock" id="ghostState">working</div><div class="ghostbar" id="ghostBar"><i></i></div></div>
  </div>
  <div class="panel belted duel-q" style="--belt:${KYU[p.kyu].bg}">
    ${badge(p.kyu)} <span class="faint">Time limit ${fmt(D.live.limit)}</span>
    <div class="statement">${texParas(p.statement)}</div>
    <form class="answer" id="duelForm" autocomplete="off">
      <input id="duelAns" inputmode="text" autocapitalize="off" spellcheck="false" placeholder="Your answer" aria-label="Your answer">
      <button class="btn primary" type="submit" id="duelSubmit">Submit</button>
    </form>
    <div class="feedback" id="duelFb" role="status"></div>
    <div class="cta" style="margin-top:12px"><button class="btn small ghost" type="button" id="resign">Resign</button></div>
  </div>`;
  tex($("v-duel"));
  $("duelAns").focus();
  $("duelForm").addEventListener("submit", (e) => {
    e.preventDefault(); const L = D.live; if (!L || L.done) return;
    const now = Date.now(); if (now < L.lockUntil) return;
    const r = check(L.p, $("duelAns").value);
    if (r === null) { $("duelFb").className = "feedback bad"; $("duelFb").textContent = "Enter a number or a fraction."; return; }
    if (r) return endDuel("win");
    L.tries++; L.lockUntil = now + 15000;
    $("duelAns").disabled = true; $("duelSubmit").disabled = true;
    $("duelFb").className = "feedback bad"; $("duelFb").textContent = "Wrong. Locked for 15 seconds.";
  });
  $("resign").addEventListener("click", () => endDuel("lose", true));
  D.live.tick = setInterval(() => {
    const L = D.live; if (!L) return;
    const t = (Date.now() - L.start) / 1000;
    $("myClock").textContent = fmt(t);
    if (L.lockUntil && Date.now() >= L.lockUntil) { L.lockUntil = 0; $("duelAns").disabled = false; $("duelSubmit").disabled = false; $("duelFb").textContent = "Unlocked."; $("duelFb").className = "feedback"; $("duelAns").focus(); }
    else if (L.lockUntil) $("duelFb").textContent = `Wrong. Locked for ${Math.ceil((L.lockUntil - Date.now()) / 1000)} more seconds.`;
    if (t >= L.ghostAt) return endDuel("lose");
    if (t >= L.limit) return endDuel("draw");
  }, 250);
}

function endDuel(outcome, resigned) {
  const L = D.live; if (!L || L.done) return; L.done = true;
  const t = (Date.now() - L.start) / 1000; stopDuel();
  const g = GHOST[D.kyu];
  const exp = 1 / (1 + Math.pow(10, (g.r - S.duel.rating) / 400));
  const score = outcome === "win" ? 1 : outcome === "draw" ? 0.5 : 0;
  const delta = Math.round(32 * (score - exp));
  S.duel.rating += delta;
  S.duel[outcome === "win" ? "w" : outcome === "draw" ? "d" : "l"]++;
  let gained = 0;
  if (outcome === "win") gained = award(L.p, "duel");
  else logEvent(`${outcome === "draw" ? "Drew" : resigned ? "Resigned" : "Lost"} a ${D.kyu} kyu duel on ${L.p.title}`);
  save(); renderMe();
  const msg = outcome === "win" ? `Solved in ${fmt(t)}${L.tries ? ` after ${L.tries} wrong attempt${L.tries > 1 ? "s" : ""}` : ""}.` :
    outcome === "draw" ? "Time ran out with nobody solving it." : resigned ? "You resigned." : `The ghost answered at ${fmt(L.ghostAt)}.`;
  $("v-duel").innerHTML = `
  <div class="panel result">
    <h1 class="big ${outcome}">${outcome === "win" ? "Victory" : outcome === "draw" ? "Draw" : "Defeat"}</h1>
    <p class="muted">${msg}</p>
    <p class="mono">Duel rating ${Math.round(S.duel.rating)} (${delta >= 0 ? "+" : ""}${delta})${gained ? ` · +${gained} kyu pts` : ""}</p>
    <div class="cta" style="justify-content:center;margin-top:16px">
      <button class="btn primary" type="button" id="rematch">Rematch at ${D.kyu} kyu</button>
      <a class="btn" href="#p-${L.p.id}">See the problem${outcome === "win" ? " and solution" : ""}</a>
      <button class="btn ghost" type="button" id="backSetup">Change kyu</button>
    </div>
  </div>`;
  $("rematch").addEventListener("click", startDuel);
  $("backSetup").addEventListener("click", renderDuelSetup);
}
