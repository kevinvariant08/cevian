"""Chooses inputs across idea families, so a family with 40 problems doesn't produce 40 near-siblings.

Records carry their family from the task 03 synthesis. Without one, the first listed technique stands in.
"""
import math
import random
import re
from collections import defaultdict

TOPICS = "ACGN"


def eligible(r, kyus):
    return r.get("kyu") in kyus and r.get("generation_potential") != "low" and not r.get("figure_needed") and not r.get("source_defect") and not (r.get("analysis_meta") or {}).get("source_defect")


def family(r):
    return r.get("family") or (r["techniques"][0] if r.get("techniques") else r["id"])


def needs_a_figure(r, geometry_ids):
    """Task 10's diagrams aren't in yet. Geometry, and anything whose solution argues from a picture, waits for them."""
    if r["topic"] == "G" or r.get("configurations") or set(r.get("techniques") or []) & geometry_ids:
        return True
    return bool(re.search(r"diagram|picture|figure|draw a|sketch", f"{r.get('core_idea', '')} {r.get('crux', '')}", re.I))


def full(records, geometry_ids, have, used, topics="ACN", kyus=(5, 4, 3), per_cell=25, expected_pass=0.93, seed=6):
    """Enough inputs to bring each kyu and topic cell to per_cell, counting the problems it already has (have).

    Within a cell, each family gives one input before any gives two. If a cell runs out of sources, sources go
    round again with a #2 key, and so a new set of recipes. Cells take turns, so a stop leaves them level.
    """
    rng = random.Random(seed)
    cells = {}
    for kyu in kyus:
        for topic in topics:
            pool = [r for r in records if r.get("kyu") == kyu and r["topic"] == topic and eligible(r, kyus) and r["id"] not in used
                    and (topic == "G" or not needs_a_figure(r, geometry_ids))]
            by_family = defaultdict(list)
            for r in sorted(pool, key=lambda r: (r["generation_potential"] != "high", rng.random())):
                by_family[family(r)].append(r)
            families = sorted(by_family)
            rng.shuffle(families)
            order = [by_family[f][i] for i in range(max(map(len, by_family.values()), default=0)) for f in families if i < len(by_family[f])]
            need = math.ceil(max(per_cell - have.get((kyu, topic), 0), 0) / expected_pass)
            cells[(kyu, topic)] = [dict(id=r["id"], key=r["id"] if i < len(order) else f"{r['id']}#{i // len(order) + 1}", kyu=kyu, topic=topic, family=family(r))
                                   for i, r in ((i, order[i % len(order)]) for i in range(need))] if order else []
    chosen = [c[i] for i in range(max(map(len, cells.values()), default=0)) for c in cells.values() if i < len(c)]
    return dict(seed=seed, kyus=list(kyus), topics=topics, per_cell=per_cell, family_rule="task 03 idea family", inputs=chosen, cells={f"{k}{t}": len(v) for (k, t), v in cells.items()})


def sample(records, kyus=(5, 4, 3), per_kyu=10, seed=6):
    """Each kyu gets every topic, with the odd extras rotating, and no family repeats while another is free."""
    rng = random.Random(seed)
    used, chosen = set(), []
    for k_i, kyu in enumerate(kyus):
        pool = defaultdict(list)
        for r in records:
            if eligible(r, kyus) and r["kyu"] == kyu:
                pool[r["topic"]].append(r)
        order = TOPICS[k_i:] + TOPICS[:k_i]
        quota = {t: per_kyu // 4 + (i < per_kyu % 4) for i, t in enumerate(order)}
        for t in order:
            # "high" potential first, then shuffled, so the sample isn't one kind of problem.
            rows = sorted(pool[t], key=lambda r: (r["generation_potential"] != "high", rng.random()))
            taken = 0
            for repeat_ok in (False, True):
                for r in rows:
                    fam = family(r)
                    if taken < quota[t] and r["id"] not in {c["id"] for c in chosen} and (repeat_ok or fam not in used):
                        used.add(fam)
                        chosen.append(dict(id=r["id"], kyu=kyu, topic=t, family=fam))
                        taken += 1
    return dict(seed=seed, kyus=list(kyus), per_kyu=per_kyu, family_rule="first listed technique", inputs=chosen)
