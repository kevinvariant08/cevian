"""Cheap records for a sample of AMC problems, for 8-6 kyu. No full analysis of these exams exists, or is paid for here.

python -m pipeline.generate.sample_low OUT_DIR [--per-kyu 24] [--seed 8] [--dry-run]

Position decides the starting kyu, from Kevin's ladder in js/lib/ranks.js. Records hold private IDs, so OUT_DIR must be private.
"""
import argparse
import json
import random
import re
from pathlib import Path

from ..verify.backend import make_backend
from ..verify.config import SONNET, corpus_path
from .prompts import taxonomy_ids

BATCH = 12
OPTION_BOUND = re.compile(r"which of the following|following (is|are|could|must)|of these|the graph|shown|pictured|figure|diagram", re.I)
SYSTEM = "You analyse maths contest problems for a private index. Output only JSON lines, one per problem, with no fence. Never quote a problem."
FORMAT = """For each problem write one JSON object on its own line:
{"id": "<as given>", "topic": "A|C|G|N", "techniques": ["<taxonomy IDs, the main one first>"], "core_idea": "<one abstract sentence>", "crux": "<the one thing to notice, or none>", "solution_paths": [{"name": "<route>", "difficulty_of_path": "easy", "key_steps": ["<short>"]}], "traps": ["<short>"], "generation_potential": "high|medium|low", "generation_note": "<short>"}
Topic: A algebra, C combinatorics or probability, G geometry, N number theory.
generation_potential is low if the problem is only arithmetic, one formula, or a one-step word problem: nothing to notice, so it could not inspire a good problem. Be strict."""


def start_kyu(exam, number):
    if exam == "AMC8":
        return 8 if number <= 18 else 7
    if number <= 10:
        return 7 if exam == "AMC10" else None
    return 6 if number <= 20 else None


def pool():
    rows = []
    for exam in ("amc8", "amc10", "amc12"):
        for x in (corpus_path() / f"{exam}.jsonl").read_text(encoding="utf-8").splitlines():
            r = json.loads(x)
            try:
                kyu = start_kyu(r["exam"], int(r["number"]))
            except ValueError:
                continue
            text = r.get("statement_md") or ""
            if kyu and r["year"] >= 2000 and not r["has_figure"] and len(text) >= 70 and not OPTION_BOUND.search(text):
                rows.append(dict(id=r["id"], exam=r["exam"], year=r["year"], kyu=kyu, text=text))
    return rows


def sample(rows, per_kyu, seed):
    """Takes turns across exams, each shuffled, so the sample isn't one era of one paper."""
    rng = random.Random(seed)
    chosen = []
    for kyu in (8, 7, 6):
        by_exam = {}
        for r in rows:
            if r["kyu"] == kyu:
                by_exam.setdefault(r["exam"], []).append(r)
        lists = list(by_exam.values())
        for group in lists:
            rng.shuffle(group)
        chosen += [lists[i % len(lists)][i // len(lists)] for i in range(per_kyu)]
    return chosen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--per-kyu", type=int, default=24)
    ap.add_argument("--seed", type=int, default=8)
    ap.add_argument("--kyus", default="876", help="only these kyus, such as 87")
    a = ap.parse_args()
    chosen = [r for r in sample(pool(), a.per_kyu, a.seed) if str(r["kyu"]) in a.kyus]
    backend = make_backend("cli", 4)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    kyu_of = {r["id"]: r["kyu"] for r in chosen}
    total = 0.0
    for i in range(0, len(chosen), BATCH):
        part = chosen[i:i + BATCH]
        prompt = "\n\n".join([FORMAT, f"TAXONOMY IDS, the only tags allowed\n{taxonomy_ids()}", *(f"<<< {r['id']}\n{r['text']}\n>>>" for r in part)])
        reply = backend.call(SONNET, SYSTEM, prompt, "low", 8000, cacheable=False, role="sample_low", draft_id=f"batch-{i}")
        total += reply.usd
        rows, decoder = [], json.JSONDecoder()
        for m in re.finditer(r'\{\s*"id"', reply.text):
            try:
                r = decoder.raw_decode(reply.text[m.start():])[0]
            except ValueError:
                continue
            if r.get("id") in kyu_of:
                rows.append(dict(r, kyu=kyu_of[r["id"]], figure_needed=False, analysis_meta=dict(method="sample_low", model=SONNET)))
        (out / f"batch_s{a.seed}_{i // BATCH:02d}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        print(f"batch {i // BATCH}: {len(rows)} of {len(part)} usd={reply.usd:.3f} truncated={reply.truncated}", flush=True)
    print(f"total usd={total:.3f}")


if __name__ == "__main__":
    main()
