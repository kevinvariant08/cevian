"""Adds up a run log: pass rate at each step, cost per passing problem, and difficulty disagreements. IDs stay out of it."""
import json
from collections import Counter, defaultdict

from .run import run_dir

IDEA_STEPS = ["topic", "idea_lint", "leak", "originality_lexical", "program", "key"]
WRITE_STEPS = ["disagree", "schema", "standard", "lint", "leak_write"]
GATE_STEPS = ["program_judge", "blind_solves", "well_posedness", "solution_audit", "difficulty", "originality"]


def load(run):
    rows = [json.loads(x) for x in (run_dir(run) / "log.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    latest = {}
    for r in rows:
        latest[r["input"]] = r  # A re-run's line replaces an earlier error or plan-limit line.
    return list(latest.values())


def steps(rows):
    """For each step: how many drafts reached it and how many went through. A candidate rejected for free counts too."""
    seen, passed, flagged = Counter(), Counter(), Counter()
    for r in rows:
        for a in r.get("attempts", []):
            for c in a.get("candidates", []):
                fail = (c.get("free_fail") or {}).get("step")
                for s in IDEA_STEPS:
                    seen[s] += 1
                    if s == fail:
                        break
                    passed[s] += 1
            if a.get("write"):
                fail = "leak_write" if a.get("step") == "leak" else a.get("step")
                for s in WRITE_STEPS:
                    seen[s] += 1
                    if s == fail:
                        break
                    passed[s] += 1
            for c in a.get("checks") or []:
                if c["check"] in GATE_STEPS:
                    seen[c["check"]] += 1
                    passed[c["check"]] += c["status"] == "pass"
                    flagged[c["check"]] += c["status"] == "investigate"
    return {s: dict(reached=seen[s], passed=passed[s], investigate=flagged[s]) for s in IDEA_STEPS + WRITE_STEPS + GATE_STEPS if seen[s]}


def summary(rows):
    by = defaultdict(lambda: Counter())
    usd_by_kyu = Counter()
    for r in rows:
        k = r.get("kyu", "?")
        by[k][r["outcome"]] += 1
        usd_by_kyu[k] += r.get("usd", 0)
    total = sum(r.get("usd", 0) for r in rows)
    passing = sum(r["outcome"] == "accept" for r in rows)
    disagreement = Counter()
    for r in rows:
        if r["outcome"] == "accept":
            last = next(a for a in reversed(r["attempts"]) if a.get("checks"))
            est = next((c["estimated_kyu"] for c in last["checks"] if c["check"] == "difficulty"), None)
            if est is not None:
                disagreement[f"{r['kyu']} kyu target, {est} kyu estimated"] += 1
    reasons = Counter()
    for r in rows:
        if r["outcome"] == "discard":
            reasons[(r.get("reason") or "").split(":")[0][:40]] += 1
    recipes = Counter(r.get("recipe") for r in rows if r["outcome"] == "accept")
    attempts = Counter(r.get("attempts_used") for r in rows if r["outcome"] == "accept")
    calls = [a[k] for r in rows for a in r.get("attempts", []) for k in ("ideas", "write") if a.get(k)]
    return dict(
        inputs=len(rows), outcomes=dict(Counter(r["outcome"] for r in rows)), by_kyu={str(k): dict(v) for k, v in sorted(by.items(), key=str)},
        steps=steps(rows), api_equivalent_usd=round(total, 2), generation_usd=round(sum(c["usd"] for c in calls), 2),
        generation_output_tokens=sum(c["output_tokens"] for c in calls), generation_calls=len(calls), generation_truncated=sum(c["truncated"] for c in calls),
        usd_per_passing=round(total / passing, 2) if passing else None, usd_by_kyu={str(k): round(v, 2) for k, v in usd_by_kyu.items()},
        recipes_of_passes=dict(recipes), attempts_of_passes={str(k): v for k, v in attempts.items()}, discard_reasons=dict(reasons), difficulty_estimates=dict(sorted(disagreement.items())),
    )
