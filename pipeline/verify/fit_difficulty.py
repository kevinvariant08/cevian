"""Fits the difficulty ruler: blind solves on corpus problems of known kyu.

    python -m pipeline.verify.fit_difficulty --per-kyu 5      a pilot: writes thresholds.json, marked provisional
    python -m pipeline.verify.fit_difficulty --per-kyu 10 --final     the full fit the brief asks for (about 420 calls)

Until task 03 records a kyu per problem, the kyu comes from its contest position table (AMC 8, AMC 10, AIME).
Only numbers and corpus IDs are stored. Replies aren't cached, because their prompts hold corpus text.
AMC problems are multiple choice; only those whose keyed choice is a plain number are used.
Models have probably seen these contests, which makes them look easier than a fresh problem. Expect the
ruler to read fresh problems as a little harder, and refit once real solve data exists (task 18).
"""
import argparse
import json
import random
from concurrent.futures import ThreadPoolExecutor
from statistics import median

from . import answers, blind, difficulty, originality
from .backend import Usage, make_backend
from .config import OUT, corpus_path


def position_kyu(rec_id, position):
    """The table in tasks/03-corpus-analysis.md."""
    if rec_id.startswith("AMC8"):
        return 8 if position <= 10 else 7 if position <= 20 else 6
    if rec_id.startswith(("AMC10", "AMC12")):
        return 7 if position <= 10 else 6 if position <= 20 else 5
    if rec_id.startswith("AIME"):
        return 5 if position <= 5 else 4 if position <= 10 else 3
    return None


def sample(per_kyu, seed=5):
    """Recent years only, without figures, because blind solvers get text alone."""
    rows = []
    for f in sorted(corpus_path().glob("*.jsonl")):
        if f.stem.endswith("_analysis"):
            continue
        for line in f.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            pos = (r.get("difficulty") or {}).get("position")
            kyu = position_kyu(r["id"], pos) if pos else None
            value = str(r.get("answer_value") or "").strip("$ ")
            if kyu and not r.get("has_figure") and r.get("statement_md") and r.get("year", 0) >= 2000 and answers.canon(answers.tidy(value)) is not None:
                rows.append(dict(id=r["id"], kyu=kyu, statement=r["statement_md"], answer=answers.tidy(value)))
    rng = random.Random(seed)
    chosen = []
    for kyu in range(8, 2, -1):
        group = [r for r in rows if r["kyu"] == kyu]
        chosen += rng.sample(group, min(per_kyu, len(group)))
    return chosen


def fit_cuts(points):
    """Cuts halfway between the median scores of neighbouring kyus, forced to rise as kyu falls."""
    by_kyu = {}
    for kyu, s in points:
        by_kyu.setdefault(kyu, []).append(s)
    kyus = sorted(by_kyu, reverse=True)
    med = [median(by_kyu[k]) for k in kyus]
    for i in range(1, len(med)):
        med[i] = max(med[i], med[i - 1] + 0.1)
    return [dict(kyu=k, max_score=round((m + n) / 2, 2)) for k, m, n in zip(kyus, med, med[1:])] + [dict(kyu=kyus[-1], max_score=round(med[-1] + 2, 2))], dict(zip(map(str, kyus), [round(m, 2) for m in med]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-kyu", type=int, default=5)
    ap.add_argument("--final", action="store_true", help="a real fit, not provisional")
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--refit", action="store_true", help="refit from out/difficulty_fit.json with no model calls")
    args = ap.parse_args()
    if not corpus_path() and not args.refit:
        raise SystemExit("Set CEVIAN_CORPUS to the private corpus.")
    OUT.mkdir(exist_ok=True)
    saved = OUT / "difficulty_fit.json"
    if args.refit:
        fit = json.loads(saved.read_text(encoding="utf-8"))
        results, usage = fit["results"], fit["usage"]
    else:
        results, usage = run_solves(args)
        saved.write_text(json.dumps(dict(results=results, usage=usage), indent=2), encoding="utf-8")
    cuts, medians = fit_cuts([(r["kyu"], r["score"]) for r in results])
    # Too easy means a warm-up's effort: the upper quartile of tokens on 8 and 7 kyu problems nobody missed.
    easy = sorted(r["tokens"] for r in results if r["kyu"] >= 7 and r["right"] == r["total"]) or [400]
    out = dict(provisional=not args.final, fitted_on=f"{len(results)} corpus problems ({args.per_kyu} per kyu from 8 to 3), kyu from contest position",
               too_easy_tokens=round(easy[int(0.75 * len(easy))]), medians_by_kyu=medians, cuts=cuts)
    difficulty.THRESHOLDS.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(dict(thresholds=out, usage=usage), indent=2))


def run_solves(args):
    backend = make_backend("cli", args.concurrency)
    usage = Usage()
    results = []

    def one(r):
        solves = blind.solve_all(dict(id=r["id"], statement=r["statement"]), backend, usage, cacheable=False)
        _, _, ev = blind.analyse(dict(answer=r["answer"], kyu=r["kyu"]), solves, -1)
        res = dict(id=r["id"], kyu=r["kyu"], right=ev["right"], total=ev["total"], tokens=ev["median_sonnet_tokens"], score=round(difficulty.score(ev["right"], ev["total"], ev["median_sonnet_tokens"]), 2))
        print(json.dumps(res), flush=True)
        results.append(res)

    with ThreadPoolExecutor(max(1, args.concurrency // 2)) as pool:
        list(pool.map(one, sample(args.per_kyu)))
    return results, usage.summary()


if __name__ == "__main__":
    main()
