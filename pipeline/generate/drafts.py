"""Turns a candidate into a gate draft, and runs the free checks that keep a bad one from costing anything."""
import json
import re
import threading
from collections import Counter

from ..figures.build import build_source
from ..figures.source import Figure, FigureError
from ..verify import answers, figure_check, originality, sandbox, schema_check, standard
from ..verify.config import BANK_DIR
from .config import AUTHOR, HELD, PENDING, TAXONOMY

PICTURE = re.compile(r"\b(diagram|picture|the figure|sketch)\b", re.I)
LEAK_WORDS = 8
LEAK_REAL_WORDS = 4
_taken = set()
_lock = threading.Lock()


def slug(title):
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:56].strip("-")
    return s or "untitled"


def allocate_id(title, owner):
    """IDs are permanent and public, so they come from the title. owner lets a repair keep its own ID."""
    base = slug(title)
    with _lock:
        n = 1
        while True:
            pid = base if n == 1 else f"{base}-{n}"
            taken = (pid, owner) not in _taken and any(p == pid for p, _ in _taken)
            on_disk = any((d / f"{pid}.json").exists() for d in (BANK_DIR, PENDING, HELD))
            if not taken and not on_disk:
                _taken.add((pid, owner))
                return pid
            n += 1


def tidy_latex(text):
    """S9's mechanical parts. Nobody should lose a good problem over the wrong fraction command."""
    text = re.sub(r"\\leq\b", r"\\le", re.sub(r"\\geq\b", r"\\ge", text))
    parts = re.split(r"(\$\$.*?\$\$)", text, flags=re.S)
    return "".join(x.replace("\\frac", "\\dfrac") if x.startswith("$$") else x.replace("\\dfrac", "\\frac") for x in parts)


def build(idea, write, key, inp, kyu, profile, run):
    pid = allocate_id(idea["title"], inp.id)
    write = {**write, "solution": tidy_latex(write["solution"]), "hints": [tidy_latex(h) for h in write["hints"]]}
    return dict(
        id=pid, title=idea["title"], kyu=kyu, topic=inp.record["topic"], subtopics=write["subtopics"],
        type=profile.type, status="draft", statement=idea["statement"], answer_format=profile.answer_format,
        answer_hash=answers.answer_hash(pid, key), hints=write["hints"], solution=write["solution"],
        provenance=dict(kind="original", author=AUTHOR, pipeline_run=run), stats=dict(solves=0, attempts=0, liked=0),
        answer=key, check_program=idea["check_program"], inspired_by=inp.id, variation_recipe=idea["recipe"],
    )


def attach_figures(d, write):
    """Builds the write-up's figures into the draft. Returns the first problem, or None. A missing TeX install raises."""
    d.pop("solution_figures", None)
    d.pop("figure_sources", None)
    d.pop("figure_exempt", None)
    if write.get("no_figure"):
        d["figure_exempt"] = write["no_figure"]
    figures, sources = [], []
    texts = write.get("figures") or []
    for i, tex in enumerate(texts):
        name = f"{d['id']}-solution" + (f"-{i + 1}" if len(texts) > 1 and i else "")
        try:
            synced = Figure(name, tex).synced_tex()
            built = build_source(name, synced)
        except FigureError as e:
            return f"figure {i + 1}: {e}"
        if built.layout:
            return f"figure {i + 1}: {built.layout[0]}"
        figures.append(dict(src=built.src, alt=built.alt, after_paragraph=built.after_paragraph))
        sources.append(dict(name=name, tex=synced, svg=built.svg))
    if figures:
        d["solution_figures"], d["figure_sources"] = figures, sources
    elif figure_check.needs_figure(d):
        return figure_check.needs_figure(d)
    return None


def taxonomy_ids():
    t = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    return {x["id"] for x in t["techniques"] + t["configurations"] if x.get("status") != "legacy"}


WHY = re.compile(r"^<b>Why this works\.</b> <code>[a-z0-9-]+</code>(, <code>[a-z0-9-]+</code>)*: .+$", re.S)


def _lint_text(text):
    if re.search(r"\*\*|`|^\s*[-*] ", text, re.M):
        return "Markdown isn't rendered: use <b> and <code>, and no lists (S10)"
    for tex, _ in schema_check.split_math(text)[0]:
        if "*" in tex or re.search(r"\\leq\b|\\geq\b|\\frac\d", tex):
            return f"LaTeX convention (S9): no *, \\leq, \\geq or \\frac12, found in ${tex[:40]}$"
    return None


def lint_idea(idea):
    """Rules on the statement and title that the standard makes automatic and the gate doesn't yet check."""
    problem = _lint_text(idea["statement"])
    if problem:
        return problem
    if re.search(r"\([a-c]\)\s", standard._prose(idea["statement"])) or idea["statement"].count("?") > 1:
        return "a statement asks exactly one thing (S1)"
    if re.search(standard.CONTESTS, idea["title"]) or slug(idea["title"]) in taxonomy_ids():
        return "the title gives away a contest or a technique (S12, S13)"
    return None


def lint_key(idea, key):
    """A1 and A6, on what the program printed."""
    try:
        value = int(key)
    except ValueError:
        return f"the key must be a plain integer from 2 to 999 (A1), but the program printed {key or 'nothing'}"
    if not 0 <= value <= 999:
        return f"the key must be from 2 to 999 (A1), but the program printed {value}: change the parameters or ask for a remainder modulo $1000$"
    if value in (0, 1):
        return f"a key of {value} is guessable (A6)"
    if re.search(rf"(?<![\d.]){value}(?![\d.])", re.sub(r"[\\{}^_]", " ", idea["statement"])):
        return f"the key {value} appears in the statement (A6)"
    return None


def lint(d):
    """Rules on the write-up. Returns the first problem, or None."""
    known = taxonomy_ids()
    bad = [s for s in d["subtopics"] if s not in known]
    if bad:
        return f"subtopics not in the taxonomy (M5): {', '.join(bad[:4])}"
    paras = [p.strip() for p in d["solution"].split("\n\n") if p.strip()]
    if not WHY.match(paras[-1]):
        return 'the last paragraph must be exactly the "Why this works" line (M4): <b>Why this works.</b> <code>id-one</code>, <code>id-two</code>: one clause'
    missing = [u for u in re.findall(r"<code>([a-z0-9-]+)</code>", paras[-1]) if u not in d["subtopics"]]
    if missing:
        return f"the Why this works line uses IDs not in subtopics (M4): {', '.join(missing)}"
    if not re.search(rf"(?<![\d.]){re.escape(d['answer'])}(?![\d.])", "\n\n".join(paras[-3:-1])):
        return "the solution must state the final answer just before the Why this works line (M3)"
    for text in [d["solution"], *d["hints"]]:
        problem = _lint_text(text)
        if problem:
            return problem
    return None


def _ngrams(text, n=LEAK_WORDS):
    """Letters and digits are masked, so "when N is divided by" matches "when M is divided by"."""
    w = ["0" if x.isdigit() else "x" if len(x) == 1 else x for x in re.findall(r"\w+", text.lower())]
    grams = (tuple(w[i:i + n]) for i in range(len(w) - n + 1))
    # A run that is mostly symbols is a formula, and short formulas coincide without any copying.
    return {g for g in grams if sum(len(x) >= 3 for x in g) >= LEAK_REAL_WORDS}


_stock = set()


def learn_stock_phrases(texts, min_docs=3):
    """A run of words in several contest problems is a stock phrase ("find the remainder when n is divided by"), not a copy."""
    counts = Counter(g for t in texts for g in _ngrams(t))
    _stock.clear()
    _stock.update(g for g, c in counts.items() if c >= min_docs)


def leak(d, inp):
    """No public field may share wording or numbers with the source. The gate reads only the statement."""
    source = _ngrams(inp.statement) - _stock
    for name in ("title", "statement", "sketch", "solution"):
        if _ngrams(d.get(name, "")) & source:
            return f"the {name} repeats wording from the source problem"
    if any(_ngrams(h) & source for h in d.get("hints", [])):
        return "a hint repeats wording from the source problem"
    nums = lambda t: set(re.findall(r"(?<![\d.])\d{2,}(?![\d.])", t)) - {"10", "100", "1000"}
    src, new = nums(inp.statement), nums(d["statement"])
    if len(src & new) >= 2 and len(src & new) * 2 >= len(src):
        return "the statement reuses the source problem's numbers"
    return None


def run_program(src):
    """What the program prints, for free: returns (key, None) or (None, reason)."""
    reason, hard_coded = sandbox.static_check(src)
    if reason:
        return None, f"check_program rejected: {reason}"
    if hard_coded:
        return None, "check_program hard-codes its answer: it computes nothing"
    result = sandbox.run_program(src)
    if not result.ok:
        return None, f"check_program didn't finish: {result.error}"
    lines = [x for x in result.stdout.strip().splitlines() if x.strip()]
    return (answers.tidy(lines[-1].strip()) if lines else ""), None


def idea_checks(idea, inp, index, threshold):
    """Everything free about an idea, so a bad one costs nothing. Returns (step, reason, key)."""
    if idea["topic"] != inp.record["topic"]:
        return "topic", f"the problem must be topic {inp.record['topic']}, and this one is labelled {idea['topic']}", None
    problem = lint_idea(idea)
    if problem:
        return "idea_lint", problem, None
    problem = leak(idea, inp)
    if problem:
        return "leak", problem, None
    status, reason, _ = originality.lexical(dict(id="?", statement=idea["statement"]), index, threshold)
    if status == "fail":
        return "originality_lexical", reason, None
    key, reason = run_program(idea["check_program"])
    if reason:
        return "program", reason, None
    problem = lint_key(idea, key)
    if problem:
        return "key", problem, key
    if inp.answer and answers.canon(inp.answer) == answers.canon(key):
        return "key", "the key equals the source problem's answer", key
    return None, None, key


def blames_the_idea(reason):
    """A standard failure in the statement or title can't be fixed by rewriting the solution."""
    return bool(re.search(r"\b(statement|title)\b", reason))


def write_checks(d, inp):
    """The free checks on a finished draft. The gate repeats the ones it owns. Returns (step, reason) or None."""
    status, reason, _ = schema_check.run(d)
    if status == "fail":
        return "schema", reason
    status, reason, _ = standard.run(d)
    if status == "fail":
        return "standard", reason
    problem = lint(d)
    if problem:
        return "lint", problem
    if d["topic"] != "G" and PICTURE.search(standard._prose(d["solution"] + " " + " ".join(d["hints"]))):
        return "lint", "the solution argues from a picture or refers to a figure, which this problem must not do"
    problem = leak(d, inp)
    if problem:
        return "leak", problem
    return None
