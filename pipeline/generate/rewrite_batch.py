"""Phase 1 of the API session: rewrite the bank's solutions as one batch, then audit every solution as a second batch.

python -m pipeline.generate.rewrite_batch rewrite   # Sonnet writes, up to two rounds (the second carries the failure reason)
python -m pipeline.generate.rewrite_batch audit     # a different model audits every solution and flags, never fixes

The writer is Sonnet throughout. The auditor is Opus for 3 kyu and proofs, Haiku below that, and Sonnet for the one
earlier rewrite that Opus wrote. A rewrite is saved only when it passes the free checks and its answer matches the stored hash.
Audit results go to out/rewrite/audit.jsonl and are not acted on, so a flagged solution stays as written and goes to Kevin.
"""
import json
import sys

from .. import batch, ledger
from ..verify.config import BANK_DIR, HAIKU, OPUS, OUT, SONNET
from . import rewrite as rw

LOG = rw.LOG
AUDIT_LOG = OUT / "rewrite" / "audit.jsonl"
OPUS_WROTE = {"a-lone-solution"}  # Rewritten earlier by the live rewriter, which used Opus below 6 kyu.


def bank():
    return {p["id"]: p for p in (json.loads(f.read_text(encoding="utf-8")) for f in sorted(BANK_DIR.glob("*.json")))}


def logged():
    return {r["id"]: r for r in (json.loads(x) for x in LOG.read_text(encoding="utf-8").splitlines() if x.strip())} if LOG.exists() else {}


def append(path, row):
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def rewrite_phase():
    problems, done = bank(), logged()
    todo = {i: p for i, p in problems.items() if done.get(i, {}).get("outcome") != "rewritten"}
    print(f"{len(todo)} to rewrite, {len(problems) - len(todo)} already done")
    failures = {}
    for rnd in (1, 2):
        pending = {i: p for i, p in todo.items() if i not in done}
        if not pending:
            break
        reqs = [batch.req(i, SONNET, rw.REWRITE_SYSTEM, rw.build_prompt(p, failures.get(i, "")), "medium", rw.CAP[p["kyu"]]) for i, p in pending.items()]
        results = batch.run(f"rewrite-round{rnd}", "rewrite_batch:rewrite", reqs)
        for i, p in pending.items():
            r = results[i]
            try:
                if not r["ok"]:
                    raise ValueError(r["error"])
                if r["stop_reason"] == "max_tokens":
                    raise ValueError("the reply was cut off")
                solution, places = rw.parse_reply(p, r["text"])
                d = rw.apply(p, solution, places)
                problem = rw.mechanical(p, d)
                if problem:
                    raise ValueError(problem)
            except ValueError as e:
                failures[i] = str(e)
                print(f"round {rnd} {i}: {str(e)[:120]}")
                continue
            rw.save(d)
            row = dict(id=i, kyu=p["kyu"], words_before=len(rw.strip_why(p["solution"]).split()), words_after=len(solution.split()), outcome="rewritten", round=rnd)
            append(LOG, row)
            done[i] = row
    for i, p in todo.items():
        if i not in done:
            rw.save(dict(p, solution=rw.strip_why(p["solution"])))  # Keeps the old solution, minus its "Why this works" paragraph.
            append(LOG, dict(id=i, kyu=p["kyu"], outcome="kept_original", reason=failures.get(i, "")[:300]))
            print(f"kept original: {i}: {failures.get(i, '')[:120]}")
    print(f"rewritten {sum(1 for r in logged().values() if r['outcome'] == 'rewritten')} of {len(problems)}; spend ${ledger.total():.2f}")


def auditor(p):
    if p["id"] in OPUS_WROTE:
        return SONNET
    return OPUS if (p["kyu"] <= 3 or p["type"] == "proof") else HAIKU


def audit_phase():
    problems = bank()
    reqs = []
    for i, p in problems.items():
        prompt = rw.AUDIT.format(statement=p["statement"], solution=p["solution"], rubric=rw.rubric_block(p),
                                 rubric_field=',"rubric_matches":true|false' if rw.is_proof(p) else "")
        reqs.append(batch.req(i, auditor(p), "You audit maths solutions strictly. You have no tools.", prompt, "medium", rw.CAP[p["kyu"]]))
    results = batch.run("audit-1", "rewrite_batch:audit", reqs)
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_LOG.write_text("", encoding="utf-8")
    flagged = 0
    for i, p in problems.items():
        r = results[i]
        a = rw.last_json(r["text"]) if r["ok"] else None
        if a is None:
            verdict, reason = "unreadable", r.get("error") or "the audit reply was unreadable"
        else:
            verdict, reason = "pass", ""
            if not a.get("correct") or not a.get("complete") or a.get("issues"):
                verdict, reason = "flag", "; ".join(map(str, a.get("issues") or ["the audit says it is incorrect or incomplete"]))[:500]
            elif rw.is_proof(p) and not a.get("rubric_matches"):
                verdict, reason = "flag", "the proof no longer matches its rubric"
            elif not rw.answer_ok(p, a.get("final_answer", "")):
                verdict, reason = "flag", f"the auditor reads the final answer as {str(a.get('final_answer'))[:40]}, which doesn't match the stored hash"
        flagged += verdict != "pass"
        append(AUDIT_LOG, dict(id=i, kyu=p["kyu"], auditor=auditor(p), verdict=verdict, reason=reason, outcome=logged().get(i, {}).get("outcome")))
    print(f"audited {len(problems)}, {flagged} flagged or unreadable; spend ${ledger.total():.2f}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    {"rewrite": rewrite_phase, "audit": audit_phase}[sys.argv[1]]()
