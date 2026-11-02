// Your profile: rank, streak, 12-week heatmap, achievements, subtopic strengths, topic and kyu bars, recent activity, backup.
import { $, esc, renderMe, rankBar } from "../lib/ui.js";
import { KYU, LADDER, badge, rankOf, TOPICS } from "../lib/ranks.js";
import { S, save, points, resetState, dayKey, currentStreak, exportJSON, importJSON } from "../lib/store.js";
import { LISTED, byId } from "../lib/problems.js";
import { subtopicName } from "../lib/taxonomy.js";
import { ACHIEVEMENTS, earnedAchievements } from "../lib/achievements.js";

const WEEKS = 12;
const SUB_ROWS = 12;
let confirmReset = false;
let pendingImport = null; // { name, text }, while asking merge or replace
let importMsg = "";
let allSubs = false;

const level = (n) => (n === 0 ? 0 : n === 1 ? 1 : n <= 3 ? 2 : n <= 6 ? 3 : 4);

function heatmap() {
  const today = new Date(); today.setHours(12, 0, 0, 0);
  const sinceMonday = (today.getDay() + 6) % 7;
  const first = new Date(today); first.setDate(today.getDate() - sinceMonday - 7 * (WEEKS - 1));
  let cells = "", months = "", lastMonth = -1, active = 0, total = 0;
  for (let w = 0; w < WEEKS; w++) {
    const monday = new Date(first); monday.setDate(first.getDate() + 7 * w);
    const m = monday.getMonth();
    months += `<span>${m !== lastMonth ? monday.toLocaleDateString("en-GB", { month: "short" }) : ""}</span>`;
    lastMonth = m;
    for (let d = 0; d < 7; d++) {
      const day = new Date(first); day.setDate(first.getDate() + 7 * w + d);
      if (day > today) { cells += `<i class="hm-off"></i>`; continue; }
      const n = S.activity[dayKey(day.getTime())] || 0;
      if (n) { active++; total += n; }
      cells += `<i class="hm-${level(n)}" title="${day.toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" })}: ${n ? n + (n === 1 ? " action" : " actions") : "nothing"}"></i>`;
    }
  }
  const summary = active ? `${active} active ${active === 1 ? "day" : "days"} and ${total} ${total === 1 ? "action" : "actions"} in the last ${WEEKS} weeks` : `No activity in the last ${WEEKS} weeks`;
  return `
    <div class="hm-wrap">
      <div class="hm-months" aria-hidden="true">${months}</div>
      <div class="hm-grid" role="img" aria-label="Activity heatmap. ${summary}.">${cells}</div>
      <div class="hm-foot"><span class="faint">${summary}</span>
        <span class="hm-legend" aria-hidden="true"><span class="faint">Less</span><i class="hm-0"></i><i class="hm-1"></i><i class="hm-2"></i><i class="hm-3"></i><i class="hm-4"></i><span class="faint">More</span></span></div>
    </div>`;
}

// One row per subtopic in the bank. Strength is solved out of the problems you've touched, once you've touched any.
function subtopicRows() {
  const rows = new Map();
  for (const p of LISTED) for (const s of p.subtopics) {
    if (!rows.has(s)) rows.set(s, { s, topic: p.topic, total: 0, solved: 0, tried: 0 });
    const r = rows.get(s);
    r.total++;
    if (S.solved[p.id]) { r.solved++; r.tried++; }
    else if (S.tries[p.id] || S.hints[p.id] || S.proofs[p.id]) r.tried++;
  }
  return [...rows.values()].sort((a, b) => b.tried - a.tried || (b.solved / (b.tried || 1)) - (a.solved / (a.tried || 1)) || b.total - a.total || a.s.localeCompare(b.s));
}

function subtopicTable() {
  const rows = subtopicRows();
  if (!rows.length) return `<p class="faint">There are no subtopics to show until the bank has problems.</p>`;
  const touched = rows.filter((r) => r.tried);
  const shown = allSubs ? rows : (touched.length ? touched : rows).slice(0, SUB_ROWS);
  return `
    ${touched.length ? "" : `<p class="faint">Nothing to measure yet. Solve or try a few problems and your strengths fill in here.</p>`}
    <div class="tablebox bare" tabindex="0" role="region" aria-labelledby="subH"><table class="fit">
      <thead><tr><th scope="col">Subtopic</th><th scope="col" class="hide-s">Topic</th><th scope="col" class="num">Solved</th><th scope="col" class="num">Tried</th><th scope="col" class="num">Strength</th></tr></thead>
      <tbody>${shown.map((r) => {
        const strength = r.tried ? Math.round((100 * r.solved) / r.tried) : null;
        return `<tr><th scope="row" class="sub-name"><a href="#problems?s=${encodeURIComponent(r.s)}">${esc(subtopicName(r.s))}</a></th><td class="hide-s">${TOPICS[r.topic]}</td><td class="num">${r.solved}/${r.total}</td><td class="num">${r.tried}</td><td class="num">${strength === null ? "–" : `<span class="meter" aria-hidden="true"><i style="width:${strength}%"></i></span>${strength}%`}</td></tr>`;
      }).join("")}</tbody>
    </table></div>
    ${rows.length > shown.length || allSubs ? `<div class="cta" style="margin-top:12px"><button class="btn small" type="button" id="subsMore">${allSubs ? "Show fewer" : `Show all ${rows.length} subtopics`}</button></div>` : ""}`;
}

const barWidth = (c, tot) => (tot ? (c / tot) * 100 : 0);

function achievementsBox(streak) {
  const earned = new Set(earnedAchievements(S, LISTED, streak).map((a) => a.id));
  return `
    <section class="panel" aria-labelledby="achH">
      <h2 class="sub" id="achH">Achievements <span class="faint">${earned.size}/${ACHIEVEMENTS.length}</span></h2>
      <div class="ach-grid">${ACHIEVEMENTS.map((a) => `<div class="ach${earned.has(a.id) ? " got" : ""}"><b>${esc(a.title)}</b><span class="faint">${esc(a.note)}</span></div>`).join("")}</div>
    </section>`;
}

function backupBox() {
  return `
    <section class="panel" aria-labelledby="backupH">
      <h2 class="sub" id="backupH">Back up your progress</h2>
      <p class="faint" style="margin:0 0 12px">Progress lives in this browser only. Export a copy before clearing site data or moving to a new device, and import it back here or anywhere else.</p>
      <div class="cta">
        <button class="btn small" type="button" id="exportBtn">Export progress</button>
        <label class="btn small ghost" for="importFile" style="cursor:pointer">Import progress</label>
        <input type="file" id="importFile" accept="application/json" style="position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)">
      </div>
      ${importMsg ? `<p class="feedback${/not/.test(importMsg) ? " bad" : ""}" role="status" style="margin-top:10px">${esc(importMsg)}</p>` : ""}
      ${pendingImport ? `<div class="confirm"><span>Add <code>${esc(pendingImport.name)}</code> to your progress here, or replace what's here with it?</span>
        <button class="btn small primary" type="button" id="importMerge">Merge</button>
        <button class="btn small" type="button" id="importReplace">Replace</button>
        <button class="btn small ghost" type="button" id="importCancel">Cancel</button></div>` : ""}
    </section>`;
}

function bindBackup() {
  $("exportBtn").addEventListener("click", () => {
    const a = Object.assign(document.createElement("a"), {
      href: URL.createObjectURL(new Blob([exportJSON()], { type: "application/json" })),
      download: `cevian-progress-${dayKey()}.json`
    });
    a.click();
    URL.revokeObjectURL(a.href);
  });
  $("importFile").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    e.target.value = "";
    if (!file) return;
    pendingImport = { name: file.name, text: await file.text() };
    importMsg = "";
    renderProfile();
  });
  if ($("importMerge")) $("importMerge").addEventListener("click", () => finishImport("merge"));
  if ($("importReplace")) $("importReplace").addEventListener("click", () => finishImport("replace"));
  if ($("importCancel")) $("importCancel").addEventListener("click", () => { pendingImport = null; renderProfile(); });
}

function finishImport(mode) {
  try {
    importJSON(pendingImport.text, mode);
    importMsg = mode === "replace" ? "Progress replaced from the file." : "Progress merged from the file.";
  } catch (e) {
    importMsg = e.message || "That file could not be read as Cevian progress.";
  }
  pendingImport = null;
  renderMe();
  renderProfile();
}

export function renderProfile() {
  const pts = points(); const r = rankOf(pts);
  const solvedList = Object.keys(S.solved).map((id) => byId[id]).filter(Boolean);
  const topicCount = (t) => solvedList.filter((p) => p.topic === t).length;
  const topicTotal = (t) => LISTED.filter((p) => p.topic === t).length;
  const streak = currentStreak();
  $("v-profile").innerHTML = `
  <h1 class="sr-only">Your profile</h1>
  <div class="panel prof-head">
    ${badge(r.cur.k, r.cur.label, "xl")}
    <div class="prof-id">
      <div><label class="eyebrow" for="handle">Your handle</label><br>
      <input id="handle" value="${esc(S.handle)}" maxlength="24" spellcheck="false"></div>
      ${rankBar(pts)}
      <div class="faint">${r.next ? `${pts} pts. ${r.next.min - pts} more to ${r.next.label}. <a href="#ranks">How ranks work</a>` : `${pts} pts. Top rank.`}</div>
    </div>
  </div>
  <div class="tiles">
    <div class="tile"><span class="eyebrow">Points</span><b>${pts}</b></div>
    <div class="tile"><span class="eyebrow">Solved</span><b>${solvedList.length} <small>of ${LISTED.length}</small></b></div>
    <div class="tile"><span class="eyebrow">Streak</span><b>${streak} <small>${streak === 1 ? "day" : "days"}</small></b></div>
    <div class="tile"><span class="eyebrow">Duel rating</span><b>${Math.round(S.duel.rating)}</b><span class="faint">${S.duel.w}W ${S.duel.l}L ${S.duel.d}D</span></div>
  </div>
  <div class="two">
    <section class="panel" aria-labelledby="hmH"><h2 class="sub" id="hmH">Last ${WEEKS} weeks</h2>${heatmap()}</section>
    <div class="panel"><h2 class="sub">Recent activity</h2>
      ${S.log.length ? `<ul class="log">${S.log.slice(0, 8).map((e) => `<li><span>${esc(e.text)}</span><span class="faint">${new Date(e.at).toLocaleDateString("en-GB", { day: "numeric", month: "short" })}</span></li>`).join("")}</ul>` : `<p class="faint">Nothing yet. <a href="#problems">Solve a problem</a> or <a href="#duel">start a duel</a> and it shows up here.</p>`}
    </div>
  </div>
  <div class="two">
    <div class="panel"><h2 class="sub">By kyu</h2>
      <div class="bars">${LADDER.map((k) => { const tot = LISTED.filter((p) => p.kyu === k).length, c = solvedList.filter((p) => p.kyu === k).length; return `<div class="bar"><span>${badge(k)}</span><span class="track"><i style="width:${barWidth(c, tot)}%;background:${KYU[k].bg}"></i></span><span class="n">${c}/${tot}</span></div>`; }).join("")}</div>
    </div>
    <div class="panel"><h2 class="sub">By topic</h2>
      <div class="bars">${Object.entries(TOPICS).map(([t, n]) => `<div class="bar"><span>${n}</span><span class="track"><i style="width:${barWidth(topicCount(t), topicTotal(t))}%"></i></span><span class="n">${topicCount(t)}/${topicTotal(t)}</span></div>`).join("")}</div>
    </div>
  </div>
  ${achievementsBox(streak)}
  <section class="panel"><h2 class="sub" id="subH">Strengths by subtopic</h2><div id="subBox">${subtopicTable()}</div></section>
  ${backupBox()}
  <div class="confirm" id="resetBox">
    ${confirmReset ? `<span>Erase all progress in this browser?</span><button class="btn small primary" type="button" id="resetYes">Erase</button><button class="btn small" type="button" id="resetNo">Keep it</button>` : `<button class="btn small ghost" type="button" id="resetBtn">Reset progress</button>`}
  </div>`;
  $("handle").addEventListener("change", (e) => { S.handle = e.target.value.trim().slice(0, 24) || "you"; save(); });
  if ($("resetBtn")) $("resetBtn").addEventListener("click", () => { confirmReset = true; renderProfile(); });
  if ($("resetNo")) $("resetNo").addEventListener("click", () => { confirmReset = false; renderProfile(); });
  if ($("resetYes")) $("resetYes").addEventListener("click", () => { resetState(); confirmReset = false; renderMe(); renderProfile(); });
  bindSubs();
  bindBackup();
}

function bindSubs() {
  if ($("subsMore")) $("subsMore").addEventListener("click", () => {
    allSubs = !allSubs;
    $("subBox").innerHTML = subtopicTable();
    bindSubs();
    if ($("subsMore")) $("subsMore").focus();
  });
}
