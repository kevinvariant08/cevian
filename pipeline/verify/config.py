"""Models, limits and paths. Change model choices here, not in the checks."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "out"
SCHEMA = ROOT / "schema" / "problem.schema.json"
BANK_DIR = ROOT / "data" / "problems"

HAIKU, SONNET, OPUS = "claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5"

# API list prices per million tokens: (input, cache read, cache write, output). The API backend uses
# them for its cost figure. The CLI reports its own API-equivalent figure.
PRICES = {HAIKU: (0.10, 0.01, 0.125, 0.50), SONNET: (2.0, 0.20, 2.5, 10.0), OPUS: (4.0, 0.20, 5.0, 20.0)}

# Only Claude is available, so independence comes from different Claude models, not a different family.
SOLVERS = [SONNET] * 5 + [HAIKU, OPUS]
PASS_SOLVES = 4

# role: (model, effort, max output tokens). The cap includes thinking.
ROLES = {
    "solve": (None, "medium", 16000),
    "program_judge": (SONNET, "medium", 4000),
    "well_posedness": (OPUS, "medium", 6000),
    "solution_audit": (OPUS, "medium", 6000),
    "originality": (OPUS, "medium", 6000),
    "figure_critic": (OPUS, "medium", 6000),
    "abstract": (HAIKU, "low", 600),
}

SANDBOX_SECONDS = float(os.environ.get("CEVIAN_SANDBOX_SECONDS") or os.environ.get("KYUCLID_SANDBOX_SECONDS") or "60")
SANDBOX_MEMORY_MB = 2048
MODEL_TIMEOUT = 600

# Fields a draft carries for the gate only. They are removed before validating against the site's schema.
GATE_FIELDS = ("answer", "check_program", "inspired_by", "core_idea", "variation_recipe", "figure_sources", "figure_exempt")


def corpus_path():
    """The private corpus. CEVIAN_CORPUS, then the older KYUCLID_CORPUS and MATHWARS_CORPUS."""
    raw = os.environ.get("CEVIAN_CORPUS") or os.environ.get("KYUCLID_CORPUS") or os.environ.get("MATHWARS_CORPUS")
    if not raw:
        return None
    p = Path(raw)
    return p / "corpus" if (p / "corpus").is_dir() else p
