"""Paths, limits and the profile that tasks 08 and 09 replace to reuse this pipeline."""
import os
from dataclasses import dataclass
from pathlib import Path

from ..verify.config import OPUS, OUT, ROOT

PENDING = ROOT / "review" / "pending"
HELD = ROOT / "review" / "held"
STANDARD = ROOT / "docs" / "problem-standard.md"
TAXONOMY = ROOT / "data" / "taxonomy.json"

REPAIRS = 2
GATE_ERROR_RETRIES = 1
AUTHOR = "kyuclid"


@dataclass(frozen=True)
class Profile:
    """What changes between 5-3 kyu answers (06), 8-6 kyu answers (08) and proofs (09)."""
    name: str
    kyus: tuple
    type: str
    answer_format: str
    model: str = OPUS
    effort: str = "medium"
    # The caps include thinking, and the CLI's budget flag stops a call a little before them.
    idea_max_tokens: int = 24000
    write_max_tokens: int = 16000
    candidates: int = 3


ANSWER_5_3 = Profile(name="answer-5-3", kyus=(5, 4, 3), type="answer", answer_format="integer_0_999")
ANSWER_8_6 = Profile(name="answer-8-6", kyus=(8, 7, 6), type="answer", answer_format="integer", idea_max_tokens=12000, write_max_tokens=16000, candidates=2)
PROFILES = {p.name: p for p in (ANSWER_5_3, ANSWER_8_6)}


def analysis_path():
    """Analysis records: a folder of batch_*.jsonl, or one jsonl file. Required, and always private."""
    raw = os.environ.get("KYUCLID_ANALYSIS")
    return Path(raw) if raw else None


def private_dir():
    """Where the private mapping and run logs go: a checkout of the private corpus, or gitignored out/."""
    raw = os.environ.get("KYUCLID_GENERATED")
    return Path(raw) if raw else OUT / "generate"
