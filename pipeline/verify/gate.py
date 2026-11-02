"""Runs the checks and turns their results into a report and a one-line verdict.

The brief's order is 1-8, with task 10's figure check after the schema. Standard rules and the lexical half of originality cost nothing, so they run
right after schema and computation to avoid spending on a draft they would fail anyway. A report still
lists checks in the order they ran. With keep_going the gate runs everything it can and doesn't stop at
a failure, which is what the seed run wants; the verdict then names the first failure in the brief's order.
"""
import json
import tempfile
import time

from . import blind, computational, critics, difficulty, figure_check, originality, schema_check, standard
from .backend import ModelError, PlanLimit, Usage

BRIEF_ORDER = ["schema", "figure", "computational", "program_judge", "blind_solves", "well_posedness", "solution_audit", "difficulty", "originality", "standard"]


class Stop(Exception):
    pass


def verify(draft, backend, keep_going=False, sandbox_seconds=None, thresholds=None, index=None, has_corpus=None, auto_fail=None):
    """Returns the report for one draft. A check failing is a verdict; a model call failing is an ERROR."""
    usage = Usage()
    started = time.time()
    report = dict(id=draft.get("id", "?"), backend=backend.name, checks=[], notes=[])
    th = thresholds or difficulty.load()

    def record(name, result, stop_on_fail=True):
        status, reason, evidence = result
        report["checks"].append(dict(check=name, status=status, reason=reason, evidence=evidence))
        if status == "fail" and stop_on_fail and not keep_going:
            raise Stop

    def skip(name, why):
        report["checks"].append(dict(check=name, status="skip", reason=why, evidence={}))

    plan_limit = False
    cleanup = []
    try:
        # A draft that fails its schema has nothing reliable to run the rest on, even with keep_going.
        status, reason, ev = schema_check.run(draft)
        report["checks"].append(dict(check="schema", status=status, reason=reason, evidence=ev))
        if status == "fail":
            raise Stop

        record("standard", standard.run(draft))

        renders = tempfile.TemporaryDirectory(prefix="cevian-renders-")
        cleanup.append(renders.cleanup)
        status, reason, figure_ev = figure_check.run(draft, renders.name)
        report["checks"].append(dict(check="figure", status=status, reason=reason, evidence={k: v for k, v in figure_ev.items() if k != "renders"}))
        if status == "error" or (status == "fail" and not keep_going):
            raise Stop

        if index is None:
            index, has_corpus = originality.default_index()
        limit = originality.load_threshold() if auto_fail is None else auto_fail
        rule = originality.classical_rule(draft)
        if rule:
            record("originality", rule)
        else:
            record("originality_lexical", originality.lexical(draft, index, limit))

        is_answer = draft["type"] == "answer"
        if is_answer:
            record("computational", computational.run_program_check(draft, sandbox_seconds))
            record("program_judge", computational.judge(draft, backend, usage))
            statement_only = {k: draft[k] for k in ("id", "statement", "figure_alt") if k in draft}
            solves = blind.solve_all(statement_only, backend, usage)
            status, reason, blind_ev = blind.analyse(draft, solves, th["too_easy_tokens"], th.get("provisional", False))
            record("blind_solves", (status, reason, blind_ev))
        else:
            report["notes"].append("Proof problem: no computation or blind solves (task 09 adds its own checks).")
            for name in ("computational", "blind_solves", "difficulty"):
                skip(name, "proof problem")

        record("well_posedness", critics.well_posedness(draft, backend, usage))
        record("solution_audit", critics.solution_audit(draft, backend, usage))
        if figure_ev["renders"]:
            record("figure_critic", critics.figure_critic(draft, figure_ev["renders"], backend, usage))
        if is_answer:
            record("difficulty", difficulty.run(draft, blind_ev, th))
        if not rule:
            record("originality", originality.judge(draft, index, backend, usage, has_corpus))
    except Stop:
        pass
    except PlanLimit as e:
        plan_limit = True
        report["checks"].append(dict(check="backend", status="error", reason=f"plan limit: {e}", evidence={}))
    except ModelError as e:
        report["checks"].append(dict(check="backend", status="error", reason=str(e)[:300], evidence={}))

    finally:
        for clean in cleanup:
            clean()

    report["verdict"] = verdict_line(report["checks"])
    report["plan_limit"] = plan_limit
    report["usage"] = usage.summary()
    report["seconds"] = round(time.time() - started, 1)
    return report


def _rank(check):
    name = "originality" if check["check"] == "originality_lexical" else check["check"]
    return BRIEF_ORDER.index(name) if name in BRIEF_ORDER else len(BRIEF_ORDER)


def verdict_line(checks):
    errors = [c for c in checks if c["status"] == "error"]
    if errors:
        return f"ERROR {errors[0]['check']}: {errors[0]['reason']}"
    fails = sorted((c for c in checks if c["status"] == "fail"), key=_rank)
    if fails:
        name = "originality" if fails[0]["check"] == "originality_lexical" else fails[0]["check"]
        return f"FAIL {name}: {fails[0]['reason']}"
    flagged = [c for c in checks if c["status"] == "investigate"]
    if flagged:
        return f"INVESTIGATE {flagged[0]['check']}: {flagged[0]['reason']}"
    return "PASS"


def write_report(report, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
