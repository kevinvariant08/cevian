"""Rewrites the bank's solutions in Kevin's style, with a blind audit. Statements, keys, kyus and rubrics don't change.

python -m pipeline.generate.rewrite [--only id,id] [--kyus 876] [--limit 10] [--concurrency 6] [--stop-file path]

A rewrite is saved only once its audit passes and its stated answer matches the stored hash. A rewrite that fails twice
keeps the old solution with its "Why this works" paragraph removed, and is listed in the log. Re-running resumes.
"""
import argparse
import json
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ..verify import answers, standard
from ..verify.backend import ModelError, PlanLimit, Usage, last_json, make_backend
from ..verify.config import BANK_DIR, OPUS, OUT, SONNET
from . import drafts, prompts

LOG = OUT / "rewrite" / "log.jsonl"
SOLUTION_RULES = ("M8", "S8", "S9", "S10", "S12")
CAP = {8: 4000, 7: 4000, 6: 5000, 5: 9000, 4: 9000, 3: 14000, 2: 14000, 1: 14000}
_write = threading.Lock()

REWRITE = """Rewrite this solution to a {kyu} kyu problem.

{style}

{length}

Keep the mathematics correct and complete, and keep the same route unless a shorter correct one is obvious. Every point name must match the statement{figure_note}. Use $...$ and $$...$$ for maths, \\dfrac in display maths and \\frac inline, \\cdot, \\le and \\ge. Use only <b> as markup, and separate paragraphs with a blank line. UK spelling.{figure_rule}{rubric_rule}

<problem>
{statement}
</problem>

<old_solution>
{old}
</old_solution>
{rubric}{failure}
Reply with only:
<solution>The new solution.</solution>
<answer>{answer_format}</answer>"""

AUDIT = """You audit a written solution to a maths contest problem. You did not write it. It is deliberately short, in the style of a strong olympiad student, so steps a strong contestant can verify in a line or two are fine, and terseness alone is not a fault. Check every claim. Material faults are a false step, a missed case, a real gap that is not routine, or a conclusion that doesn't follow.

<problem>
{statement}
</problem>

<solution>
{solution}
</solution>
{rubric}
Reply with JSON only: {{"correct":true|false,"complete":true|false,"final_answer":"<the value the solution ends at, or empty for a proof>","issues":["<max 25 words each, material faults only>"]{rubric_field}}}"""


def is_proof(p):
    return p["type"] == "proof"


def paragraphs(text):
    return [x.strip() for x in re.split(r"\n\s*\n", text.strip()) if x.strip()]


def strip_why(text):
    return "\n\n".join(x for x in paragraphs(text) if not x.startswith("<b>Why this works"))


def with_markers(p):
    """The old solution with a marker where each figure sits, so the writer can place it again."""
    paras = paragraphs(strip_why(p["solution"]))
    figures = p.get("solution_figures") or []
    out = []
    for i in range(len(paras) + 1):
        out += [f"[FIGURE {n + 1}]" for n, f in enumerate(figures) if min(f["after_paragraph"], len(paras)) == i]
        if i < len(paras):
            out.append(paras[i])
    return "\n\n".join(out)


def place_figures(p, text):
    """Takes the markers out. Returns (solution, after_paragraph values), or raises ValueError if one is missing."""
    paras, places = [], {}
    for x in paragraphs(text):
        m = re.fullmatch(r"\[FIGURE (\d+)\]", x)
        if m:
            places[int(m.group(1))] = len(paras)
        else:
            paras.append(x)
    figures = p.get("solution_figures") or []
    if sorted(places) != list(range(1, len(figures) + 1)):
        raise ValueError(f"every figure marker must appear once, on its own line: expected {len(figures)}, found {sorted(places)}")
    return "\n\n".join(paras), [places[i + 1] for i in range(len(figures))]


def mechanical(p, candidate):
    """Free checks on a rewrite. Returns the first problem, or None."""
    problem = drafts._lint_text(candidate["solution"])
    if problem:
        return problem
    def fails(d):
        return {f for f in standard.run(dict(d, answer="2"))[2].get("failures", []) if f.split(":")[0] in SOLUTION_RULES}
    new = fails(candidate) - fails(dict(p, solution="Done."))  # Old statements may break newer rules, and that isn't this rewrite's fault.
    return sorted(new)[0] if new else None


def answer_ok(p, value):
    return is_proof(p) or (bool(str(value).strip()) and answers.answer_hash(p["id"], answers.tidy(str(value).strip().strip("$ "))) == p["answer_hash"])


def rubric_block(p):
    return f"\n<rubric>\n{json.dumps(p['rubric'], ensure_ascii=False, indent=1)}\n</rubric>\n" if is_proof(p) else ""


def rewrite_once(p, backend, usage, failure=""):
    figures = p.get("solution_figures") or []
    alt = "; ".join(f"figure {i + 1}: {f['alt']}" for i, f in enumerate(figures))
    prompt = REWRITE.format(
        kyu=p["kyu"], style=prompts.SOLUTION_STYLE, length=prompts.length_guide(p["kyu"]), statement=p["statement"], old=with_markers(p), rubric=rubric_block(p),
        figure_note=" and any figure" if figures else "",
        figure_rule=f" Keep each [FIGURE n] marker on its own line, at the point in the argument it illustrates, and keep every length and point the figure labels in the text ({alt})." if figures else "",
        rubric_rule=" The rubric stays as it is, so the proof must still reach each of its milestones." if is_proof(p) else "",
        failure=f"\nAN AUDITOR REJECTED YOUR LAST VERSION\n{failure}\nFix the cause.\n" if failure else "",
        answer_format="Nothing: this is a proof." if is_proof(p) else "The final answer, as a plain value with no words.")
    model = SONNET if p["kyu"] >= 6 else OPUS
    r = backend.call(model, "You write up maths solutions as a strong olympiad student does. You have no tools. Think briefly. Output only what the format asks for.", prompt, "medium", CAP[p["kyu"]], role="rewrite", draft_id=p["id"])
    usage.add(r)
    if r.truncated:
        raise ValueError("the reply was cut off")
    new, answer = prompts._tag(r.text, "solution"), prompts._tag(r.text, "answer")
    if not new:
        raise ValueError("no solution in the reply")
    solution, places = place_figures(p, drafts.tidy_latex(new))
    if not answer_ok(p, answer):
        raise ValueError(f"the stated answer {answer[:40]!r} doesn't match the stored hash")
    return solution, places


def audit(p, solution, backend, usage):
    prompt = AUDIT.format(statement=p["statement"], solution=solution, rubric=rubric_block(p), rubric_field=',"rubric_matches":true|false' if is_proof(p) else "")
    model = SONNET if p["kyu"] >= 6 else OPUS
    r = backend.call(model, "You audit maths solutions strictly. You have no tools.", prompt, "medium", CAP[p["kyu"]], role="rewrite_audit", draft_id=p["id"])
    usage.add(r)
    a = last_json(r.text)
    if a is None:
        return "the audit reply was unreadable", {}
    if not a.get("correct") or not a.get("complete") or a.get("issues"):
        return "; ".join(map(str, a.get("issues") or ["the audit says it is incorrect or incomplete"]))[:500], a
    if is_proof(p) and not a.get("rubric_matches"):
        return "the proof no longer matches its rubric", a
    if not answer_ok(p, a.get("final_answer", "")):
        return f"the auditor reads the final answer as {str(a.get('final_answer'))[:40]}, which doesn't match the stored hash", a
    return None, a


def apply(p, solution, places):
    d = dict(p, solution=solution)
    if places:
        d["solution_figures"] = [dict(f, after_paragraph=n) for f, n in zip(p["solution_figures"], places)]
    return d


def save(d):
    (BANK_DIR / f"{d['id']}.json").write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def one(p, backend):
    usage = Usage()
    row = dict(id=p["id"], kyu=p["kyu"], words_before=len(strip_why(p["solution"]).split()), attempts=[])
    failure = ""
    for attempt in range(2):
        try:
            solution, places = rewrite_once(p, backend, usage, failure)
            d = apply(p, solution, places)
            problem = mechanical(p, d)
            if problem:
                raise ValueError(problem)
        except ValueError as e:
            failure = str(e)
            row["attempts"].append(dict(step="rewrite", reason=failure[:300]))
            continue
        failure, _ = audit(p, solution, backend, usage)
        if not failure:
            save(d)
            row.update(outcome="rewritten", words_after=len(solution.split()), usd=round(usage.fresh_usd, 4))
            return row
        row["attempts"].append(dict(step="audit", reason=failure[:300]))
    save(dict(p, solution=strip_why(p["solution"])))
    row.update(outcome="kept_original", reason=failure[:300], usd=round(usage.fresh_usd, 4))
    return row


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--kyus", default="87654321")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--stop-file")
    a = ap.parse_args()
    LOG.parent.mkdir(parents=True, exist_ok=True)
    done = {json.loads(x)["id"] for x in LOG.read_text(encoding="utf-8").splitlines() if x.strip()} if LOG.exists() else set()
    only = set(filter(None, a.only.split(",")))
    problems = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(BANK_DIR.glob("*.json"))]
    # Easy first, because they're cheap and show the style soonest.
    items = sorted((p for p in problems if p["id"] not in done and str(p["kyu"]) in a.kyus and (not only or p["id"] in only)), key=lambda p: -p["kyu"])[:a.limit]
    backend = make_backend("cli", a.concurrency * 2)
    stop = Path(a.stop_file) if a.stop_file else None
    halted = []

    def work(p):
        if halted or (stop and stop.exists()):
            return
        try:
            row = one(p, backend)
        except (PlanLimit, ModelError) as e:
            halted.append(str(e))
            print(f"{p['id']}: stopped: {str(e)[:160]}", flush=True)
            return
        with _write:
            with LOG.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"{row['id']}: {row['outcome']} {row['words_before']}->{row.get('words_after', '-')} usd={row['usd']} {row.get('reason', '')[:140]}", flush=True)

    with ThreadPoolExecutor(a.concurrency) as pool:
        list(pool.map(work, items))
    return 2 if halted else 0


if __name__ == "__main__":
    sys.exit(main())
