"""Makes problems: ideas, pick, write up, verify, repair, save. Each input logs one line, so a re-run resumes."""
import json
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from ..verify import difficulty, gate, originality
from ..verify.backend import ModelError, PlanLimit, Usage
from . import drafts, prompts, recipes
from .config import GATE_ERROR_RETRIES, HELD, PENDING, REPAIRS, private_dir

_write = threading.Lock()


def run_dir(run):
    return private_dir() / "runs" / run


def _append(path, row):
    with _write:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def classify(report):
    """accept: into the queue. hold: for Kevin, not counted as a pass. repair: send the reason back. error: not a judgement."""
    checks = report["checks"]
    if any(c["status"] == "error" for c in checks):
        return "error", report["verdict"]
    failed = [c for c in checks if c["status"] == "fail"]
    if failed:
        return "repair", report["verdict"]
    flagged = [c for c in checks if c["status"] == "investigate"]
    for c in flagged:
        if c["check"] == "difficulty" or (c["check"] == "blind_solves" and c["reason"].startswith("too easy")):
            continue  # The ruler is provisional, so a disagreement with it is data for a reviewer.
        if c["check"] == "blind_solves" and "no majority" in c["reason"] and c["evidence"].get("right", 0) >= 2:
            return "hold", c["reason"]  # The program and at least two solvers reach the key, so this may just be hard.
        return "repair", f"{c['check']}: {c['reason']}"
    return "accept", report["verdict"]


def far_too_hard(report, kyu):
    """At 8 and 7 kyu a draft the ruler puts 3 or more kyus harder doesn't join the queue. Kevin asked for this after seeing AIME-rated 8 kyu drafts."""
    estimate = next((c["evidence"].get("estimated_kyu") for c in report["checks"] if c["check"] == "difficulty"), None)
    return kyu >= 7 and estimate is not None and kyu - estimate >= 3


def _save(d, report, folder):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{d['id']}.json").write_text(json.dumps(dict(draft=d, report=report), indent=2, ensure_ascii=False), encoding="utf-8")


def _record_map(d, inp, run, outcome):
    _append(private_dir() / "generated_map.jsonl", dict(id=d["id"], inspired_by=inp.id, variation_recipe=d["variation_recipe"], kyu=d["kyu"], topic=d["topic"], run=run, outcome=outcome, at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())))


def _checks_for_log(report):
    return [dict(check=c["check"], status=c["status"], reason=c["reason"], estimated_kyu=c["evidence"].get("estimated_kyu"), right=c["evidence"].get("right")) for c in report["checks"]]


# A gate failure in one of these is the write-up's fault, so the statement and program are kept.
WRITE_UP_FAULTS = ("solution_audit", "standard", "figure", "figure_critic")


def _write_up_text(write):
    """What a repair sees of its earlier attempt."""
    return "\n\n".join([write["solution"], *(f"<figure>{f}</figure>" for f in write.get("figures") or [])])


def _call(ctx, usage, entry, stage, system, prompt, cap, draft_id):
    """The prompt may hold contest text, so it must never reach the cache."""
    profile = ctx["profile"]
    started = time.time()
    reply = ctx["backend"].call(profile.model, system, prompt, profile.effort, cap, cacheable=False, role=stage, draft_id=draft_id)
    usage.add(reply)
    entry[stage] = dict(seconds=round(time.time() - started, 1), output_tokens=reply.output, truncated=reply.truncated, usd=round(reply.usd, 4))
    return reply


def _choose_idea(inp, ctx, usage, entry, chosen_recipes, partner, previous, failure):
    """One ideas call and the free checks. Returns (idea, key, None), or (top idea, None, reason) if none is clean."""
    profile, kyu = ctx["profile"], inp.record["kyu"]
    if previous is None:
        prompt = prompts.ideas(inp, kyu, chosen_recipes, partner, ctx["digest"])
    else:
        prompt = prompts.idea_repair(inp, kyu, previous, failure, ctx["digest"])
    reply = _call(ctx, usage, entry, "ideas", prompts.SYSTEM, prompt, profile.idea_max_tokens, inp.id)
    parsed = prompts.parse_ideas(reply.text)
    if not parsed:
        return previous, None, "the reply had no complete candidate"
    checked = []
    for c in parsed:
        c["statement"] = drafts.tidy_latex(c["statement"])
        if c["recipe"] not in recipes.RECIPES:
            c["recipe"] = previous["recipe"] if previous else chosen_recipes[0]
        step, reason, key = drafts.idea_checks(c, inp, ctx["index"], ctx["threshold"])
        entry["candidates"].append(dict(title=c["title"], recipe=c["recipe"], interest=c["interest"], interest_reason=c["interest_reason"], key=key, free_fail=step and dict(step=step, reason=reason)))
        checked.append((c, key, step, reason))
    clean = [x for x in checked if not x[2]]
    c, key, step, reason = max(clean or checked, key=lambda x: x[0]["interest"])
    entry["chosen"] = c["title"]
    return (c, key, None) if not step else (c, None, f"{step}: {reason}")


def make_one(inp, ctx, seed):
    """One input: at most one generation and REPAIRS repairs. Raises PlanLimit so the batch can stop cleanly."""
    profile, run_name = ctx["profile"], ctx["run"]
    kyu = inp.record["kyu"]
    rng = random.Random(f"{seed}:{inp.key}")
    chosen_recipes = recipes.pick(inp.record, rng, profile.candidates)
    partner = recipes.rare_partner(inp.record, ctx["records"], rng) if "combine" in chosen_recipes else None
    log = dict(input=inp.key, source=inp.id, kyu=kyu, topic=inp.record["topic"], recipes_offered=chosen_recipes, partner=partner, attempts=[], outcome=None, model=profile.model, effort=profile.effort)
    usage = Usage()
    idea, key, failure, earlier_write = None, None, None, None

    for attempt in range(REPAIRS + 1):
        entry = dict(attempt=attempt, candidates=[])
        log["attempts"].append(entry)
        if key is None:
            entry["kind"] = "ideas" if idea is None else "idea_repair"
            idea, key, reason = _choose_idea(inp, ctx, usage, entry, chosen_recipes, partner, idea, failure)
            if reason:
                entry["step"], failure = "ideas", reason
                continue
        else:
            entry["kind"] = "write_repair"
        entry["recipe"] = idea["recipe"]

        prompt = prompts.write_up(idea, kyu, key, inp.record, earlier_write, failure if earlier_write else None)
        reply = _call(ctx, usage, entry, "write", prompts.WRITE_SYSTEM, prompt, profile.write_max_tokens, inp.id)
        write = prompts.parse_write_up(reply.text)
        if write is None:
            entry["step"], failure = "write_unreadable", "the write-up was incomplete"
            continue
        if write.get("disagree"):
            # The writer found a fault before the gate had to: back to the idea.
            entry["step"], failure, key, earlier_write = "disagree", f"the solution writer found this fault: {write['disagree']}", None, None
            continue
        d = drafts.build(idea, write, key, inp, kyu, profile, run_name)
        entry["draft"] = d
        figure_problem = drafts.attach_figures(d, write)
        if figure_problem:
            entry["step"] = "figure"
            failure, earlier_write = f"figure: {figure_problem}", _write_up_text(write)
            continue
        problem = drafts.write_checks(d, inp)
        if problem:
            entry["step"] = problem[0]
            failure, earlier_write = f"{problem[0]}: {problem[1]}", _write_up_text(write)
            if drafts.blames_the_idea(problem[1]):
                key, earlier_write = None, None
            continue

        report = None
        for _ in range(GATE_ERROR_RETRIES + 1):
            report = gate.verify(d, ctx["backend"], thresholds=ctx["thresholds"], index=ctx["index"], has_corpus=True, auto_fail=ctx["threshold"])
            if report.get("plan_limit"):
                entry["step"] = "plan_limit"
                raise PlanLimit(report["verdict"])
            if not any(x["status"] == "error" for x in report["checks"]):
                break
        decision, reason = classify(report)
        entry.update(step="gate", verdict=report["verdict"], decision=decision, checks=_checks_for_log(report), gate_usage=report["usage"])
        if decision == "error":
            log["outcome"], log["reason"] = "error", reason
            break
        if decision == "accept" and far_too_hard(report, kyu):
            log["outcome"], log["reason"] = "discard", f"too hard for {kyu} kyu: {report['verdict'][:120]}"
            break
        if decision in ("accept", "hold"):
            _save(d, report, PENDING if decision == "accept" else HELD)
            _record_map(d, inp, run_name, decision)
            log.update(outcome=decision, id=d["id"], recipe=d["variation_recipe"], verdict=report["verdict"], attempts_used=attempt + 1)
            break
        failure = reason
        failed_check = next((c["check"] for c in report["checks"] if c["status"] == "fail"), "")
        if failed_check in WRITE_UP_FAULTS:
            earlier_write = _write_up_text(write)
        else:
            key, earlier_write = None, None
    else:
        log.update(outcome="discard", reason=failure)
    log["generate_usage"] = usage.summary()
    gate_usd = sum((a.get("gate_usage") or {}).get("api_equivalent_usd_this_run", 0) for a in log["attempts"])
    log["usd"] = round(usage.fresh_usd + gate_usd, 4)
    return log


def done_inputs(run):
    path = run_dir(run) / "log.jsonl"
    if not path.exists():
        return set()
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    return {r["input"] for r in rows if r.get("outcome") in ("accept", "hold", "discard")}


def run_inputs(items, ctx, seed, concurrency, stop_file=None):
    """items are Inputs. Stops starting new ones if the plan limit is hit or stop_file appears; a re-run picks up the rest."""
    stopped = []
    log_path = run_dir(ctx["run"]) / "log.jsonl"

    def one(item):
        if stopped or (stop_file and stop_file.exists()):
            return None
        try:
            row = make_one(item, ctx, seed)
        except PlanLimit as e:
            stopped.append(str(e))
            row = dict(input=item.key, outcome="plan_limit", reason=str(e)[:200])
        except ModelError as e:
            row = dict(input=item.key, outcome="error", reason=str(e)[:200])
        _append(log_path, row)
        print(f"{row['input']}: {row['outcome']} {row.get('id', '')} {row.get('verdict', row.get('reason', ''))[:160]} usd={row.get('usd', 0)}", flush=True)
        return row

    with ThreadPoolExecutor(concurrency) as pool:
        rows = [r for r in pool.map(one, items) if r]
    return rows, bool(stopped)


def context(profile, backend, run, records, index, digest=""):
    drafts.learn_stock_phrases(r["text"] for r in index.records if r["source"] == "corpus")
    return dict(profile=profile, backend=backend, run=run, records=records, index=index, digest=digest,
                thresholds=difficulty.load(), threshold=originality.load_threshold())
