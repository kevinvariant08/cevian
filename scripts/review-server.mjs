// The review queue's local server: serves tools/review.html and the site, and writes Kevin's decisions.
//   npm run review                     then open http://localhost:8377/tools/review.html
//   npm run review -- --pending <dir>  to read drafts from another checkout's review/pending
// It only ever listens on 127.0.0.1. review/ is gitignored because drafts hold answers and inspired_by.
import { spawn } from "node:child_process";
import { appendFileSync, existsSync, mkdirSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import { createServer } from "node:http";
import { homedir } from "node:os";
import { extname, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { failureList } from "./rejection-digest.mjs";

const REPO = resolve(fileURLToPath(new URL("..", import.meta.url)));
const PORT = 8377;
const ID = /^[a-z0-9]+(-[a-z0-9]+)*$/;
const EDITABLE = ["title", "statement", "solution", "hints", "kyu"];
const MAX_BODY = 5e6;

// Only what the site needs. An allow-list, because Windows also opens review./ and REVIEW/ as review/.
const STATIC_DIRS = new Set(["assets", "css", "data", "figures", "js"]);
const STATIC_FILES = new Set(["index.html", "site.webmanifest", "tools/review.html"]);
const MIME = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8", ".svg": "image/svg+xml", ".png": "image/png", ".webmanifest": "application/manifest+json" };

const run = (cmd, args, cwd, env) => new Promise((done) => {
  const p = spawn(cmd, args, { cwd, env, windowsHide: true });
  let out = "";
  p.stdout.on("data", (d) => { out += d; });
  p.stderr.on("data", (d) => { out += d; });
  p.on("error", (e) => done({ code: -1, out: String(e.message) }));
  p.on("close", (code) => done({ code, out }));
});

function gateEnv() {
  const env = { ...process.env, PYTHONIOENCODING: "utf-8" };
  const usual = join(homedir(), "mathwars-corpus");
  if (!env.CEVIAN_CORPUS && !env.KYUCLID_CORPUS && !env.MATHWARS_CORPUS && existsSync(usual)) env.CEVIAN_CORPUS = usual;
  return env;
}

// The real gate. Any exit code can carry a report: 0 pass, 1 fail or investigate, 3 model error.
function gateVerifier(root, gateRoot) {
  return async (draft) => {
    const dir = join(root, "out", "review");
    mkdirSync(dir, { recursive: true });
    const draftFile = join(dir, `${draft.id}.draft.json`);
    const reportFile = join(dir, `${draft.id}.report.json`);
    rmSync(reportFile, { force: true });
    writeFileSync(draftFile, JSON.stringify(draft, null, 2));
    const r = await run(process.env.PYTHON || "python", ["-m", "pipeline.verify", draftFile, "--report", reportFile], gateRoot, gateEnv());
    const report = existsSync(reportFile) ? JSON.parse(readFileSync(reportFile, "utf8")) : null;
    rmSync(draftFile, { force: true });
    rmSync(reportFile, { force: true });
    return report || { id: draft.id, verdict: `ERROR gate: ${r.out.trim().slice(-300) || "no report written"}`, checks: [], notes: [] };
  };
}

const verdictWord = (report) => (report ? report.verdict.split(" ")[0].replace(":", "") : "UNVERIFIED");
const flagged = (report) => report.checks.filter((c) => c.status === "investigate").map((c) => `${c.check}: ${c.reason}`);

// An edit may have changed the true answer, and the check program can't notice because it wasn't edited.
// Only the blind solvers can, so new doubts about an edited statement block it outright.
// A hard draft they already doubted can still have a typo fixed, after the usual second confirmation.
function editBlock(report, statementChanged, original) {
  const word = verdictWord(report);
  if (word === "FAIL" || word === "ERROR") return report.verdict;
  const blind = report.checks.find((c) => c.check === "blind_solves");
  const doubtedBefore = original?.checks.some((c) => c.check === "blind_solves" && c.status === "investigate");
  if (statementChanged && blind?.status === "investigate" && !doubtedBefore) return `The edited statement may no longer match its answer. ${blind.reason}`;
  return null;
}

export function createReviewServer({ root = REPO, pendingDir, verify, gateRoot } = {}) {
  root = resolve(root);
  const reviewDir = join(root, "review");
  const pending = pendingDir ? resolve(pendingDir) : join(reviewDir, "pending");
  const verifyDraft = verify || gateVerifier(root, gateRoot || root);
  const schema = JSON.parse(readFileSync(join(root, "schema", "problem.schema.json"), "utf8"));
  const failures = failureList(root);
  const failureCodes = new Set(failures.map((f) => f.code));
  const jobs = new Map();
  const running = new Set();
  const verified = new Map(); // id -> { json, report }, for an edit waiting on "approve anyway"
  let nextJob = 1;
  let writes = Promise.resolve();
  let origins = new Set();

  // One decision at a time, because each rebuilds data/index.json.
  const serial = (fn) => {
    const result = writes.then(fn);
    writes = result.catch(() => {});
    return result;
  };

  const pendingFile = (id) => join(pending, `${id}.json`);
  const countJson = (dir) => (existsSync(dir) ? readdirSync(dir).filter((f) => f.endsWith(".json")).length : 0);

  function pendingIds() {
    if (!existsSync(pending)) return [];
    return readdirSync(pending).filter((f) => f.endsWith(".json") && !f.endsWith(".report.json") && !f.startsWith("_")).map((f) => f.slice(0, -5)).filter((id) => ID.test(id));
  }

  // Task 06 writes { draft, report }. A flat draft with a report key or a sibling <id>.report.json also works.
  function load(id) {
    const raw = JSON.parse(readFileSync(pendingFile(id), "utf8"));
    const { report: inner, draft: wrapped, ...flat } = raw;
    const draft = wrapped || flat;
    const sibling = join(pending, `${id}.report.json`);
    let report = inner || (existsSync(sibling) ? JSON.parse(readFileSync(sibling, "utf8")) : null);
    if (report && report.id !== draft.id) report = null;
    if (draft.id !== id) throw new Error(`the file is ${id}.json but the draft's id is "${draft.id}"`);
    return { draft, report };
  }

  // Keeps only what the public schema names, so answer, check_program, inspired_by and anything added later stay out.
  function finalForm(draft) {
    const p = {};
    for (const k of Object.keys(schema.properties)) if (k in draft) p[k] = draft[k];
    p.status = "beta";
    p.verification = `gate-${new Date().toISOString().slice(0, 10)}-${draft.id}`;
    return p;
  }

  // A generated draft carries its figures, so a rejected one never leaves files in the public repo.
  function writeFigures(draft) {
    const written = [];
    for (const { name, tex, svg } of draft.figure_sources || []) {
      if (!/^[a-z0-9][a-z0-9-]*$/.test(name)) throw new Error(`bad figure name "${name}"`);
      for (const [ext, content] of [["tex", tex], ["svg", svg]]) {
        const path = join(root, "figures", `${name}.${ext}`);
        if (!existsSync(path)) { mkdirSync(join(root, "figures"), { recursive: true }); writeFileSync(path, content); written.push(path); }
      }
    }
    return written;
  }

  // A backfilled figure is mapped by ID in figures/index.json until it is attached.
  function withMappedFigures(p) {
    const index = join(root, "figures", "index.json");
    if (p.solution_figures || !existsSync(index)) return p;
    const mapped = JSON.parse(readFileSync(index, "utf8"))[p.id];
    return mapped ? { ...p, solution_figures: mapped } : p;
  }

  async function publish(draft) {
    const p = withMappedFigures(finalForm(draft));
    const text = JSON.stringify(p, null, 2);
    if (draft.inspired_by && text.includes(draft.inspired_by)) return `Public text mentions the private ID ${draft.inspired_by}.`;
    const file = join(root, "data", "problems", `${draft.id}.json`);
    if (existsSync(file)) return `data/problems/${draft.id}.json already exists, and IDs are permanent. Reject this draft or give it a new ID.`;
    const indexFile = join(root, "data", "index.json");
    const before = readFileSync(indexFile);
    const figures = writeFigures(draft);
    writeFileSync(file, text + "\n");
    const build = await run(process.execPath, [join(root, "scripts", "build-index.mjs")], root);
    const check = build.code === 0 ? await run(process.execPath, [join(root, "scripts", "validate.mjs")], root) : build;
    if (check.code === 0) return null;
    rmSync(file, { force: true });
    for (const path of figures) rmSync(path, { force: true });
    writeFileSync(indexFile, before);
    return `The bank's validator refused it, so nothing was saved. ${check.out.trim().slice(0, 600)}`;
  }

  function log(entry) {
    mkdirSync(reviewDir, { recursive: true });
    appendFileSync(join(reviewDir, "decisions.jsonl"), JSON.stringify({ ...entry, time: new Date().toISOString() }) + "\n");
  }

  // Moves a decided draft out of the queue. The private copy keeps its answer and program for later re-verification.
  function file(id, folder, record) {
    const dir = join(reviewDir, folder);
    mkdirSync(dir, { recursive: true });
    writeFileSync(join(dir, `${id}.json`), JSON.stringify(record, null, 2));
    rmSync(pendingFile(id), { force: true });
    rmSync(join(pending, `${id}.report.json`), { force: true });
  }

  const finish = (id, draft, report, edits) => serial(async () => {
    const error = await publish(draft);
    if (error) return { status: "blocked", reason: error, report };
    file(id, "approved", { draft, report, approved_at: new Date().toISOString() });
    const decision = Object.keys(edits).length ? "approve_with_edits" : "approve";
    log({ id, decision, reason: [], note: "", edits, verdict: report.verdict });
    verified.delete(id);
    return { status: "approved", id, report };
  });

  function cleanEdits(edits) {
    const out = {};
    for (const [k, v] of Object.entries(edits || {})) {
      if (!EDITABLE.includes(k)) throw new Error(`"${k}" can't be edited here`);
      out[k] = k === "hints" ? v.map((h) => String(h).trim()).filter(Boolean) : v;
    }
    return out;
  }

  const diff = (draft, edited) => {
    const d = {};
    for (const k of EDITABLE) if (JSON.stringify(draft[k]) !== JSON.stringify(edited[k])) d[k] = { from: draft[k], to: edited[k] };
    return d;
  };

  function startJob(id, work) {
    const job = String(nextJob++);
    const state = { done: false, started: Date.now() };
    jobs.set(job, state);
    running.add(id);
    work().then((result) => { state.result = result; }, (e) => { state.result = { status: "blocked", reason: e.message }; }).finally(() => {
      state.done = true;
      running.delete(id);
    });
    return { job };
  }

  async function verifyEdit(id, original, edited, changes, confirm) {
    const json = JSON.stringify(edited);
    const held = verified.get(id);
    const report = held?.json === json ? held.report : await verifyDraft(edited);
    const block = editBlock(report, "statement" in changes, original);
    if (block) return { status: "blocked", reason: block, report };
    if (flagged(report).length && !confirm) {
      verified.set(id, { json, report });
      return { status: "confirm", reasons: flagged(report), report };
    }
    return finish(id, edited, report, changes);
  }

  async function decide(body) {
    const { id, action } = body;
    if (!ID.test(String(id)) || !existsSync(pendingFile(id))) return [404, { error: `no pending draft "${id}"` }];
    if (running.has(id)) return [409, { error: "the gate is still running on this draft" }];
    const { draft, report } = load(id);

    if (action === "reject") {
      const reason = Array.isArray(body.reason) ? body.reason : [];
      const note = String(body.note || "").trim();
      if (!reason.length || !reason.every((c) => failureCodes.has(c))) return [400, { error: "Rejecting needs a reason from the list." }];
      if (reason.includes("other") && !note) return [400, { error: '"Other" needs a note.' }];
      await serial(() => {
        file(id, "rejected", { draft, report, rejection: { reason, note, time: new Date().toISOString() } });
        log({ id, decision: "reject", reason, note, edits: {}, verdict: report?.verdict || null });
      });
      return [200, { status: "rejected", id }];
    }

    if (action === "verify") {
      return [202, startJob(id, async () => {
        const fresh = await verifyDraft(draft);
        writeFileSync(join(pending, `${id}.report.json`), JSON.stringify(fresh, null, 2));
        return { status: "verified", report: fresh };
      })];
    }

    if (action !== "approve") return [400, { error: `unknown action "${action}"` }];
    const edited = { ...draft, ...cleanEdits(body.edits) };
    const changes = diff(draft, edited);
    if (Object.keys(changes).length) return [202, startJob(id, () => verifyEdit(id, report, edited, changes, !!body.confirm))];

    if (!report) return [200, { status: "blocked", reason: "This draft has no verification report. Verify it first." }];
    const word = verdictWord(report);
    if (word === "FAIL" || word === "ERROR") return [200, { status: "blocked", reason: report.verdict, report }];
    if (flagged(report).length && !body.confirm) return [200, { status: "confirm", reasons: flagged(report), report }];
    return [200, await finish(id, draft, report, {})];
  }

  function queue() {
    const items = [];
    const warnings = [];
    for (const id of pendingIds()) {
      try {
        const { draft, report } = load(id);
        items.push({ id, title: draft.title, kyu: draft.kyu, topic: draft.topic, verdict: verdictWord(report), running: running.has(id) });
      } catch (e) { warnings.push(`${id}.json: ${e.message}`); }
    }
    items.sort((a, b) => b.kyu - a.kyu || (a.id < b.id ? -1 : 1));
    const env = gateEnv();
    if (!env.CEVIAN_CORPUS && !env.KYUCLID_CORPUS && !env.MATHWARS_CORPUS) warnings.push("CEVIAN_CORPUS isn't set, so re-verifying an edit compares originality with the bank only.");
    return { items, warnings, failures, approved: countJson(join(reviewDir, "approved")), rejected: countJson(join(reviewDir, "rejected")) };
  }

  const send = (res, code, body) => {
    res.writeHead(code, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" });
    res.end(JSON.stringify(body));
  };

  function serveStatic(pathname, res) {
    let rel;
    try { rel = relative(root, resolve(root, "." + decodeURIComponent(pathname))); }
    catch { return send(res, 400, { error: "bad path" }); }
    const name = rel.split(sep).join("/") || "index.html";
    const path = join(root, name);
    if (!(STATIC_FILES.has(name) || STATIC_DIRS.has(name.split("/")[0])) || !existsSync(path) || !statSync(path).isFile()) return send(res, 404, { error: "not found" });
    res.writeHead(200, { "Content-Type": MIME[extname(path)] || "application/octet-stream", "Cache-Control": "no-store" });
    res.end(readFileSync(path));
  }

  const readBody = (req) => new Promise((done, fail) => {
    let body = "";
    req.on("data", (d) => {
      body += d;
      if (body.length > MAX_BODY) { fail(new Error("too large")); req.destroy(); }
    });
    req.on("end", () => done(body));
    req.on("error", fail);
  });

  const server = createServer(async (req, res) => {
    // Other websites can reach 127.0.0.1 from Kevin's browser, so check who is asking. No CORS headers are ever sent.
    if (!origins.has(`http://${req.headers.host}`)) return send(res, 403, { error: "local use only" });
    const url = new URL(req.url, `http://${req.headers.host}`);
    try {
      if (req.method === "POST") {
        const sameOrigin = !req.headers.origin || origins.has(req.headers.origin);
        if (!sameOrigin || !String(req.headers["content-type"]).startsWith("application/json")) return send(res, 403, { error: "local use only" });
        if (url.pathname !== "/api/decide") return send(res, 404, { error: "not found" });
        const [code, body] = await decide(JSON.parse(await readBody(req)));
        return send(res, code, body);
      }
      if (req.method !== "GET" && req.method !== "HEAD") return send(res, 405, { error: "method not allowed" });
      if (url.pathname === "/api/queue") return send(res, 200, queue());
      const m = url.pathname.match(/^\/api\/draft\/([a-z0-9-]+)$/);
      if (m) return ID.test(m[1]) && existsSync(pendingFile(m[1])) ? send(res, 200, load(m[1])) : send(res, 404, { error: "no such draft" });
      const j = url.pathname.match(/^\/api\/job\/(\d+)$/);
      if (j) return jobs.has(j[1]) ? send(res, 200, jobs.get(j[1])) : send(res, 404, { error: "no such job" });
      if (url.pathname.startsWith("/api/")) return send(res, 404, { error: "not found" });
      return serveStatic(url.pathname, res);
    } catch (e) {
      return send(res, 400, { error: e.message });
    }
  });

  const listen = (port = PORT) => new Promise((done, fail) => {
    server.once("error", fail);
    server.listen(port, "127.0.0.1", () => {
      const p = server.address().port;
      origins = new Set([`http://localhost:${p}`, `http://127.0.0.1:${p}`]);
      done(p);
    });
  });
  return { server, listen };
}

function openBrowser(url) {
  const [cmd, args] = process.platform === "win32" ? ["cmd", ["/c", "start", "", url]] : [process.platform === "darwin" ? "open" : "xdg-open", [url]];
  spawn(cmd, args, { stdio: "ignore", detached: true, windowsHide: true }).on("error", () => {}).unref();
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  const opt = (name) => (args.includes(name) ? args[args.indexOf(name) + 1] : undefined);
  const { listen } = createReviewServer({ pendingDir: opt("--pending") });
  listen(Number(opt("--port")) || PORT).then((port) => {
    const url = `http://localhost:${port}/tools/review.html`;
    console.log(`Review queue: ${url}\nThe site, with approved problems: http://localhost:${port}/\nCtrl+C stops it. Approved problems wait in data/ for you to commit.`);
    if (!args.includes("--no-open")) openBrowser(url);
  }, (e) => {
    console.error(e.code === "EADDRINUSE" ? "The review server is already running, or the port is taken. Try --port <n>." : e.message);
    process.exit(1);
  });
}
