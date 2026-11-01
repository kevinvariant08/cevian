"""Loads analysis records and joins each to its private statement. Nothing here is ever written to this repo."""
import json
from dataclasses import dataclass
from pathlib import Path

from ..verify import originality
from ..verify.config import corpus_path
from .config import analysis_path


@dataclass
class Input:
    id: str
    record: dict
    statement: str
    answer: str
    key: str = ""  # Set when one source feeds more than one problem. The run log and the recipe seed use it.

    def __post_init__(self):
        self.key = self.key or self.id


def load_analysis(path=None):
    path = Path(path) if path else analysis_path()
    if not path:
        raise SystemExit("set KYUCLID_ANALYSIS to the analysis records (a folder of batch_*.jsonl or one jsonl file)")
    files = sorted(path.glob("batch_*.jsonl")) if path.is_dir() else [path]
    if not files:
        raise SystemExit(f"no analysis records in {path}")
    return [json.loads(x) for f in files for x in f.read_text(encoding="utf-8").splitlines() if x.strip()]


def load_statements():
    path = corpus_path()
    if not path or not path.is_dir():
        raise SystemExit("set KYUCLID_CORPUS to the private corpus: originality means nothing without it")
    return {r["id"]: r for r in originality.load_corpus(path)}


def load_inputs(records):
    statements = load_statements()
    return {r["id"]: Input(r["id"], r, statements[r["id"]]["text"], str(statements[r["id"]].get("answer") or "")) for r in records if r["id"] in statements}


def build_index(records, extra=()):
    """The gate's index, with core ideas from the analysis so retrieval can find reskins in a new setting."""
    ideas = {r["id"]: r.get("core_idea") for r in records}
    path = corpus_path()
    corpus = originality.load_corpus(path)
    for c in corpus:
        c["core_idea"] = c.get("core_idea") or ideas.get(c["id"])
    return originality.Index(originality.load_bank() + corpus + list(extra))
