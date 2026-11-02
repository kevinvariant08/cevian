// node --test scripts/review-server.test.mjs
// Every test runs on a temporary copy of the bank, so the real data/ is never touched.
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { cpSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { request } from "node:http";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { after, before, beforeEach, test } from "node:test";
import { fileURLToPath } from "node:url";
import { check, hashAnswer } from "../js/lib/answers.js";
import { digest, failureList, readDecisions } from "./rejection-digest.mjs";
import { createReviewServer } from "./review-server.mjs";

const REPO = fileURLToPath(new URL("..", import.meta.url));
const ID = "two-primes-test";
const PRIVATE = "AIME-2019-I-07";
let root, base, port, srv, nextReport;

const report = (verdict, checks = []) => ({ id: ID, verdict, checks, notes: [], usage: { api_equivalent_usd: 0.1, calls: 11 } });
const PASS = report("PASS", [{ check: "blind_solves", status: "pass", reason: "7/7", evidence: { right: 7, total: 7 } }]);
const flag = (check, reason) => report(`INVESTIGATE ${check}: ${reason}`, [{ check, status: "investigate", reason, evidence: {} }]);

const draft = (over = {}) => ({
  id: ID, title: "Two primes", kyu: 6, topic: "N", subtopics: ["modular-arithmetic"], type: "answer", status: "draft",
  statement: "How many integers $n$ with $1 \\le n \\le 30$ are multiples of $3$?",
  answer_format: "integer_0_999", answer_hash: hashAnswer(ID, "10"),
  hints: ["Look at the multiples.", "Divide."], solution: "There are $10$.",
  provenance: { kind: "original", author: "test", pipeline_run: "run-1" }, stats: { solves: 0, attempts: 0, liked: 0 },
  answer: "10", check_program: "print(sum(1 for n in range(1,31) if n%3==0))", inspired_by: PRIVATE,
  core_idea: "secret idea", variation_recipe: "secret recipe", ...over,
});

const pendingPath = (id = ID) => join(root, "review", "pending", `${id}.json`);
const putPending = (value, id = ID) => {
  mkdirSync(join(root, "review", "pending"), { recursive: true });
  writeFileSync(pendingPath(id), JSON.stringify(value));
};
const post = async (body) => {
  const res = await fetch(`${base}/api/decide`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  return { code: res.status, body: await res.json() };
};
async function decide(body) {
  const r = await post(body);
  if (!r.body.job) return r.body;
  for (;;) {
    const s = await (await fetch(`${base}/api/job/${r.body.job}`)).json();
    if (s.done) return s.result;
    await new Promise((d) => setTimeout(d, 20));
  }
}
const published = () => join(root, "data", "problems", `${ID}.json`);
const index = () => JSON.parse(readFileSync(join(root, "data", "index.json"), "utf8"));

before(() => {
  root = mkdtempSync(join(tmpdir(), "cevian-review-"));
  for (const p of ["scripts", "schema", "data", "figures", "docs/problem-standard.md", "js", "tools", "index.html"]) cpSync(join(REPO, p), join(root, p), { recursive: true });
  symlinkSync(join(REPO, "node_modules"), join(root, "node_modules"), "junction");
});
after(() => rmSync(root, { recursive: true, force: true }));

beforeEach(async () => {
  if (srv) await new Promise((d) => srv.server.close(d));
  rmSync(join(root, "review"), { recursive: true, force: true });
  rmSync(published(), { force: true });
  spawnSync(process.execPath, [join(root, "scripts", "build-index.mjs")]);
  nextReport = PASS;
  srv = createReviewServer({ root, verify: async () => nextReport });
  port = await srv.listen(0);
  base = `http://localhost:${port}`;
});
after(() => srv?.server.close());

test("approve writes the public form only, rebuilds the index, and the key still checks", async () => {
  putPending({ draft: draft(), report: PASS });
  const r = await decide({ id: ID, action: "approve" });
  assert.equal(r.status, "approved");
  const text = readFileSync(published(), "utf8");
  const p = JSON.parse(text);
  for (const k of ["answer", "check_program", "inspired_by", "core_idea", "variation_recipe", "report"]) assert.ok(!(k in p), k);
  assert.ok(!text.includes(PRIVATE));
  assert.equal(p.status, "beta");
  assert.equal(check(p, "10"), true);
  assert.equal(check(p, "11"), false);
  assert.match(p.verification, /^gate-/);
  assert.ok(index().some((e) => e.id === ID));
  assert.equal(spawnSync(process.execPath, [join(root, "scripts", "validate.mjs")]).status, 0);
  assert.ok(!existsSync(pendingPath()));
  assert.equal(JSON.parse(readFileSync(join(root, "review", "approved", `${ID}.json`), "utf8")).draft.answer, "10");
  const [d] = readDecisions(root);
  assert.equal(d.id, ID);
  assert.equal(d.decision, "approve");
  assert.ok(d.time);
});

test("all three pending shapes load", async () => {
  putPending({ ...draft(), report: PASS });
  assert.equal((await (await fetch(`${base}/api/draft/${ID}`)).json()).report.verdict, "PASS");
  putPending(draft());
  writeFileSync(join(root, "review", "pending", `${ID}.report.json`), JSON.stringify(PASS));
  const q = await (await fetch(`${base}/api/queue`)).json();
  assert.deepEqual(q.items.map((i) => [i.id, i.verdict]), [[ID, "PASS"]]);
  assert.equal((await decide({ id: ID, action: "approve" })).status, "approved");
  assert.ok(!existsSync(join(root, "review", "pending", `${ID}.report.json`)));
});

test("no report, FAIL and ERROR can't be approved; INVESTIGATE needs a second confirmation", async () => {
  putPending(draft());
  assert.equal((await decide({ id: ID, action: "approve" })).status, "blocked");
  putPending({ draft: draft(), report: report("FAIL standard: bad") });
  assert.equal((await decide({ id: ID, action: "approve", confirm: true })).status, "blocked");
  putPending({ draft: draft(), report: report("ERROR backend: down") });
  assert.equal((await decide({ id: ID, action: "approve", confirm: true })).status, "blocked");
  assert.ok(!existsSync(published()));
  putPending({ draft: draft(), report: flag("difficulty", "estimated 7 kyu, target 6 kyu") });
  const first = await decide({ id: ID, action: "approve" });
  assert.equal(first.status, "confirm");
  assert.match(first.reasons[0], /estimated 7/);
  assert.ok(!existsSync(published()));
  assert.equal((await decide({ id: ID, action: "approve", confirm: true })).status, "approved");
});

test("approving a draft that carries its figures writes them, and keeps the sources out of the public form", async () => {
  const svg = readFileSync(join(root, "figures", "two-orbits-solution.svg"), "utf8").replaceAll("two-orbits-solution-", "carried-fig-solution-");
  const version = createHash("sha256").update(svg).digest("hex").slice(0, 8);
  const id = "carried-fig";
  const d = draft({ id, answer_hash: hashAnswer(id, "10"), solution_figures: [{ src: `figures/${id}-solution.svg?v=${version}`, alt: "A clock.", after_paragraph: 1 }], figure_sources: [{ name: `${id}-solution`, tex: "% source", svg }] });
  putPending({ draft: d, report: { ...PASS, id } }, id);
  const r = await decide({ id, action: "approve" });
  assert.equal(r.status, "approved", r.reason);
  const p = JSON.parse(readFileSync(join(root, "data", "problems", `${id}.json`), "utf8"));
  assert.equal(p.solution_figures.length, 1);
  assert.equal(p.figure_sources, undefined);
  assert.equal(readFileSync(join(root, "figures", `${id}-solution.svg`), "utf8"), svg);
  assert.ok(existsSync(join(root, "figures", `${id}-solution.tex`)));
  rmSync(join(root, "data", "problems", `${id}.json`));
  rmSync(join(root, "figures", `${id}-solution.svg`));
  rmSync(join(root, "figures", `${id}-solution.tex`));
  spawnSync(process.execPath, [join(root, "scripts", "build-index.mjs")]);
});

test("a figure that fails validation is removed again with its draft", async () => {
  const id = "bad-fig";
  const svg = "<svg stroke='#808080'></svg>";
  const version = createHash("sha256").update(svg).digest("hex").slice(0, 8);
  const d = draft({ id, answer_hash: hashAnswer(id, "10"), solution_figures: [{ src: `figures/${id}-solution.svg?v=${version}`, alt: "A clock.", after_paragraph: 1 }], figure_sources: [{ name: `${id}-solution`, tex: "% source", svg }] });
  putPending({ draft: d, report: { ...PASS, id } }, id);
  const r = await decide({ id, action: "approve" });
  assert.equal(r.status, "blocked");
  assert.match(r.reason, /#808080/);
  assert.ok(!existsSync(join(root, "figures", `${id}-solution.svg`)));
  assert.ok(existsSync(pendingPath(id)));
  rmSync(pendingPath(id));
});

test("the bank's validator rolls back a bad approval", async () => {
  const before = readFileSync(join(root, "data", "index.json"), "utf8");
  putPending({ draft: draft({ subtopics: ["test-fixture"] }), report: PASS });
  const r = await decide({ id: ID, action: "approve" });
  assert.equal(r.status, "blocked");
  assert.match(r.reason, /test-fixture/);
  assert.ok(!existsSync(published()));
  assert.equal(readFileSync(join(root, "data", "index.json"), "utf8"), before);
  assert.ok(existsSync(pendingPath()));
});

test("an existing ID is never overwritten", async () => {
  writeFileSync(published(), "{}");
  putPending({ draft: draft(), report: PASS });
  const r = await decide({ id: ID, action: "approve" });
  assert.equal(r.status, "blocked");
  assert.match(r.reason, /already exists/);
  assert.equal(readFileSync(published(), "utf8"), "{}");
});

test("a private ID in public text blocks approval", async () => {
  putPending({ draft: draft({ solution: `Same as ${PRIVATE}.` }), report: PASS });
  assert.match((await decide({ id: ID, action: "approve" })).reason, /private ID/);
  assert.ok(!existsSync(published()));
});

test("an edit is verified before saving, and the diff is logged", async () => {
  putPending({ draft: draft(), report: PASS });
  let seen;
  await new Promise((d) => srv.server.close(d));
  srv = createReviewServer({ root, verify: async (x) => { seen = x; return PASS; } });
  port = await srv.listen(0);
  base = `http://localhost:${port}`;
  const r = await decide({ id: ID, action: "approve", edits: { title: "Thirds", kyu: 7, hints: ["Look at the multiples.", "Divide.", " "] } });
  assert.equal(r.status, "approved");
  assert.equal(seen.title, "Thirds");
  assert.equal(seen.answer, "10");
  const p = JSON.parse(readFileSync(published(), "utf8"));
  assert.equal(p.title, "Thirds");
  assert.equal(p.kyu, 7);
  assert.equal(p.hints.length, 2);
  const [d] = readDecisions(root);
  assert.equal(d.decision, "approve_with_edits");
  assert.deepEqual(d.edits.title, { from: "Two primes", to: "Thirds" });
  assert.ok(!("hints" in d.edits));
});

test("a failing edit is blocked with the reason, and the draft is untouched", async () => {
  const original = { draft: draft(), report: PASS };
  putPending(original);
  nextReport = report("FAIL schema: LaTeX: statement: unclosed $");
  const r = await decide({ id: ID, action: "approve", edits: { statement: "Broken $n" } });
  assert.equal(r.status, "blocked");
  assert.match(r.reason, /unclosed/);
  assert.ok(!existsSync(published()));
  assert.deepEqual(JSON.parse(readFileSync(pendingPath(), "utf8")), original);
  assert.equal(readDecisions(root).length, 0);
});

test("a statement edit that breaks the key can't be confirmed through", async () => {
  putPending({ draft: draft(), report: PASS });
  nextReport = flag("blind_solves", "wrong key or ambiguous: 7/7 agree on 13, the key is 10");
  const r = await decide({ id: ID, action: "approve", confirm: true, edits: { statement: "How many multiples of $3$ up to $40$?" } });
  assert.equal(r.status, "blocked");
  assert.match(r.reason, /wrong key/);
  assert.ok(!existsSync(published()));
});

test("a draft the solvers already doubted can have its statement fixed, after confirming", async () => {
  const doubted = flag("blind_solves", "only 3/7 reach the key and no majority agrees: too hard, or ambiguous");
  putPending({ draft: draft(), report: doubted });
  nextReport = doubted;
  const edits = { statement: "How many integers $n$ with $1 \le n \le 30$ are divisible by $3$?" };
  assert.equal((await decide({ id: ID, action: "approve", edits })).status, "confirm");
  assert.equal((await decide({ id: ID, action: "approve", edits, confirm: true })).status, "approved");
});

test("an edit flagged only for difficulty asks once and doesn't re-run the gate", async () => {
  putPending({ draft: draft(), report: PASS });
  let runs = 0;
  await new Promise((d) => srv.server.close(d));
  srv = createReviewServer({ root, verify: async () => { runs++; return flag("difficulty", "estimated 7 kyu, target 4 kyu"); } });
  port = await srv.listen(0);
  base = `http://localhost:${port}`;
  const edits = { kyu: 4 };
  assert.equal((await decide({ id: ID, action: "approve", edits })).status, "confirm");
  assert.equal((await decide({ id: ID, action: "approve", edits, confirm: true })).status, "approved");
  assert.equal(runs, 1);
});

test("only the listed fields can be edited", async () => {
  putPending({ draft: draft(), report: PASS });
  assert.equal((await post({ id: ID, action: "approve", edits: { answer: "11" } })).code, 400);
});

test("a gate job's error leaves the draft pending", async () => {
  putPending({ draft: draft(), report: PASS });
  nextReport = report("ERROR backend: plan limit: reset soon");
  const r = await decide({ id: ID, action: "approve", edits: { title: "New" } });
  assert.equal(r.status, "blocked");
  assert.match(r.reason, /plan limit/);
  assert.ok(existsSync(pendingPath()));
});

test("verify now stores a report beside a draft that has none", async () => {
  putPending(draft());
  assert.equal((await decide({ id: ID, action: "verify" })).status, "verified");
  assert.equal((await decide({ id: ID, action: "approve" })).status, "approved");
});

test("reject needs a reason from the list, writes the file and feeds the digest", async () => {
  putPending({ draft: draft(), report: PASS });
  assert.equal((await post({ id: ID, action: "reject" })).code, 400);
  assert.equal((await post({ id: ID, action: "reject", reason: ["B99"] })).code, 400);
  assert.equal((await post({ id: ID, action: "reject", reason: ["other"] })).code, 400);
  assert.ok(existsSync(pendingPath()));
  assert.equal((await post({ id: ID, action: "reject", reason: ["B2", "B7"], note: "Just arithmetic." })).body.status, "rejected");
  const saved = JSON.parse(readFileSync(join(root, "review", "rejected", `${ID}.json`), "utf8"));
  assert.deepEqual(saved.rejection.reason, ["B2", "B7"]);
  assert.ok(!existsSync(pendingPath()) && !existsSync(published()));
  const text = digest(readDecisions(root), failureList(root));
  assert.match(text, /rejected 1 of 1/);
  assert.match(text, /B2 a computation slog/);
  assert.match(text, /Just arithmetic/);
});

test("the digest copes with no rejections", () => {
  assert.match(digest([], failureList(REPO)), /No drafts have been rejected/);
});

test("the failure list is the standard's B1 to B10, plus Other", () => {
  assert.deepEqual(failureList(REPO).map((f) => f.code), ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9", "B10", "other"]);
});

function raw(path, headers, method = "GET", body) {
  return new Promise((done, fail) => {
    const req = request({ host: "127.0.0.1", port, path, method, headers }, (res) => { res.resume(); res.on("end", () => done(res)); });
    req.on("error", fail);
    req.end(body);
  });
}

test("other websites and hostnames can't use it", async () => {
  putPending({ draft: draft(), report: PASS });
  const host = `localhost:${port}`;
  assert.equal((await raw(`/api/draft/${ID}`, { Host: "evil.example" })).statusCode, 403);
  const json = { Host: host, "Content-Type": "application/json" };
  const body = JSON.stringify({ id: ID, action: "approve" });
  assert.equal((await raw("/api/decide", { ...json, Origin: "https://evil.example" }, "POST", body)).statusCode, 403);
  assert.equal((await raw("/api/decide", { Host: host, "Content-Type": "text/plain" }, "POST", body)).statusCode, 403);
  const ok = await raw(`/api/queue`, { Host: host });
  assert.equal(ok.headers["access-control-allow-origin"], undefined);
  assert.equal(srv.server.address().address, "127.0.0.1");
  assert.ok(!existsSync(published()));
});

test("private folders and traversal aren't served, and the site is", async () => {
  putPending({ draft: draft(), report: PASS });
  const host = { Host: `localhost:${port}` };
  for (const p of [`/review/pending/${ID}.json`, `/REVIEW/pending/${ID}.json`, `/review./pending/${ID}.json`, `/review%20/pending/${ID}.json`, `/%72eview/pending/${ID}.json`, `/data/..%2freview/pending/${ID}.json`, `/data/%2e%2e/review/pending/${ID}.json`, "/.git/config", "/out/x", "/pipeline/verify/README.md", "/scripts/review-server.mjs", "/node_modules/ajv/package.json"]) {
    assert.equal((await raw(p, host)).statusCode, 404, p);
  }
  assert.equal((await raw("/api/draft/..%2f..%2fetc", host)).statusCode, 404);
  assert.equal((await post({ id: "../../x", action: "reject", reason: ["B1"] })).code, 404);
  for (const p of ["/", "/index.html", "/tools/review.html", "/data/index.json", "/js/lib/tex.js"]) assert.equal((await raw(p, host)).statusCode, 200, p);
});

test("the page holds no private data and is inert away from localhost", () => {
  const page = readFileSync(join(REPO, "tools", "review.html"), "utf8");
  assert.match(page, /noindex/);
  assert.match(page, /\["localhost", "127\.0\.0\.1"\]\.includes\(location\.hostname\)/);
  assert.ok(!/check_program"\s*:|inspired_by"\s*:|answer"\s*:/.test(page));
  assert.ok(!/answer_hash|[A-Z]{3,}-\d{4}/.test(page));
  assert.ok(!/localStorage/.test(page));
});

test("review/ is gitignored and nothing in it is tracked", () => {
  const git = (...a) => spawnSync("git", a, { cwd: REPO, encoding: "utf8" });
  if (git("rev-parse", "--git-dir").status !== 0) return;
  for (const p of ["review/pending/x.json", "review/rejected/x.json", "review/approved/x.json", "review/decisions.jsonl"]) assert.equal(git("check-ignore", "-q", p).status, 0, p);
  assert.equal(git("ls-files", "review").stdout, "");
});

test("the real gate blocks a broken edit, for free", async (t) => {
  if (spawnSync("python", ["-c", "import jsonschema"]).status !== 0) return t.skip("no Python with jsonschema");
  await new Promise((d) => srv.server.close(d));
  srv = createReviewServer({ root, gateRoot: REPO });
  port = await srv.listen(0);
  base = `http://localhost:${port}`;
  putPending({ draft: draft(), report: PASS });
  const r = await decide({ id: ID, action: "approve", edits: { statement: "Broken $n" } });
  assert.equal(r.status, "blocked");
  assert.match(r.reason, /FAIL schema.*unclosed/);
  assert.ok(!existsSync(published()));
});
