"""python -m pipeline.generate --from AIME-2019-I-07 [--n 2]
python -m pipeline.generate --plan plan.json [--limit 5]
python -m pipeline.generate --make-plan plan.json [--per-kyu 10] [--seed 6]
python -m pipeline.generate --make-full-plan plan.json --topics ACN [--per-cell 25]
python -m pipeline.generate --report RUN

Exit code: 0 when finished, 2 if stopped early by the plan limit or the stop file, 3 on a backend failure.
"""
import argparse
import dataclasses
import json
import sys
import time
from collections import Counter
from pathlib import Path

from ..verify.backend import ModelError, make_backend
from ..verify.config import BANK_DIR
from . import inputs, plan, report, run
from .config import HELD, PENDING, PROFILES, TAXONOMY, private_dir


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="python -m pipeline.generate")
    ap.add_argument("--from", dest="source", help="one corpus ID")
    ap.add_argument("--n", type=int, default=1, help="with --from: how many problems to attempt from it")
    ap.add_argument("--plan", help="a plan JSON made by --make-plan")
    ap.add_argument("--make-plan", help="write a sampled plan here and stop")
    ap.add_argument("--per-kyu", type=int, default=10)
    ap.add_argument("--make-full-plan", help="write a plan that fills each kyu and topic cell, and stop")
    ap.add_argument("--topics", default="ACN")
    ap.add_argument("--per-cell", type=int, default=25)
    ap.add_argument("--seed", type=int, default=6)
    ap.add_argument("--limit", type=int, help="with --plan: start at most this many unfinished inputs")
    ap.add_argument("--report", help="print the summary of a run and stop")
    ap.add_argument("--run", help="run name, which a re-run reuses to resume (default: a timestamp)")
    ap.add_argument("--profile", choices=sorted(PROFILES), default="answer-5-3")
    ap.add_argument("--analysis", help="analysis records (default KYUCLID_ANALYSIS)")
    ap.add_argument("--digest", help="a rejection digest from task 07 to include in the prompt")
    ap.add_argument("--concurrency", type=int, default=3, help="inputs at once")
    ap.add_argument("--model-slots", type=int, default=8, help="model calls at once")
    ap.add_argument("--backend", choices=["cli", "api"], default="cli", help="cli uses the plan; api needs ANTHROPIC_API_KEY and costs money")
    ap.add_argument("--stop-file", help="start no more inputs once this file exists")
    args = ap.parse_args()

    if args.report:
        print(json.dumps(report.summary(report.load(args.report)), indent=2))
        return 0

    profile = PROFILES[args.profile]
    records = inputs.load_analysis(args.analysis)
    if args.make_plan:
        Path(args.make_plan).write_text(json.dumps(plan.sample(records, profile.kyus, args.per_kyu, args.seed), indent=2), encoding="utf-8")
        return 0
    if args.make_full_plan:
        taxonomy = json.loads(TAXONOMY.read_text(encoding="utf-8"))
        geometry = {t["id"] for t in taxonomy["techniques"] if t.get("topic") == "G"}
        queue = [json.loads(f.read_text(encoding="utf-8"))["draft"] for folder in (PENDING, HELD) if folder.exists() for f in folder.glob("*.json")]
        bank = [d for d in map(lambda f: json.loads(f.read_text(encoding="utf-8")), BANK_DIR.glob("*.json")) if d.get("provenance", {}).get("pipeline_run")]
        have = Counter((d["kyu"], d["topic"]) for d in bank + [d for d in queue if d["id"] not in {b["id"] for b in bank}])
        # The review server empties the queue, so the private map is what remembers which sources were used.
        mapped = private_dir() / "generated_map.jsonl"
        used = {json.loads(x)["inspired_by"] for x in mapped.read_text(encoding="utf-8").splitlines() if x.strip()} if mapped.exists() else set()
        Path(args.make_full_plan).write_text(json.dumps(plan.full(records, geometry, have, used, args.topics, profile.kyus, args.per_cell, seed=args.seed), indent=2), encoding="utf-8")
        return 0
    if bool(args.source) == bool(args.plan):
        ap.error("give one of --from, --plan, --make-plan or --report")

    try:
        backend = make_backend(args.backend, args.model_slots)
    except ModelError as e:
        print(f"ERROR backend: {e}", file=sys.stderr)
        return 3

    by_id = inputs.load_inputs(records)
    if args.source:
        if args.source not in by_id:
            print(f"ERROR no analysis record or statement for {args.source}", file=sys.stderr)
            return 3
        ids, seed = [args.source] * args.n, args.seed
    else:
        p = json.loads(Path(args.plan).read_text(encoding="utf-8"))
        keys = {x.get("key", x["id"]): x["id"] for x in p["inputs"]}
        ids, seed = list(keys), p.get("seed", args.seed)

    name = args.run or time.strftime("run-%Y%m%d-%H%M%S", time.gmtime())
    if args.plan:
        done = run.done_inputs(name)
        ids = [i for i in ids if i not in done]
        if args.limit is not None:
            ids = ids[:args.limit]

    # Earlier drafts join the index, so the bank isn't filled with siblings of what's already pending.
    earlier = []
    for folder in (PENDING, HELD):
        for f in sorted(folder.glob("*.json")) if folder.exists() else []:
            d = json.loads(f.read_text(encoding="utf-8"))["draft"]
            earlier.append(dict(id=d["id"], text=d["statement"], source="bank"))
    index = inputs.build_index(records, earlier)
    digest = Path(args.digest).read_text(encoding="utf-8") if args.digest else ""
    ctx = run.context(profile, backend, name, records, index, digest)
    # --from repeats one source, so its keys get numbered in the same way a plan's do.
    if args.source:
        keys = {f"{args.source}#{i + 1}" if i else args.source: args.source for i in range(args.n)}
        ids = list(keys)
    items = [dataclasses.replace(by_id[keys[i]], key=i) for i in ids]
    _, stopped = run.run_inputs(items, ctx, seed, args.concurrency, Path(args.stop_file) if args.stop_file else None)
    print(json.dumps(report.summary(report.load(name)), indent=2))
    return 2 if stopped else 0


if __name__ == "__main__":
    sys.exit(main())
