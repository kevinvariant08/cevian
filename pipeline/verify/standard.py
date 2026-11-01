"""Check 8: the automatable rules from Appendix A of docs/problem-standard.md. Rule numbers are the standard's.

Rules that need judgement are in the critics' prompts instead. M3 stays a warning, because a key like 25/4 can
appear as $\\dfrac{25}{4}$. The literal check in H4 skips one-digit answers, which turn up innocently in hints;
the solution audit judges those. M5 and the ID half of M4 run only where data/taxonomy.json exists.
"""
import json
import re
from fractions import Fraction

from . import answers
from .config import ROOT

TAXONOMY = ROOT / "data" / "taxonomy.json"
US_TO_UK = {"color": "colour", "colored": "coloured", "coloring": "colouring", "colorings": "colourings", "colors": "colours", "neighbor": "neighbour", "neighbors": "neighbours",
            "neighboring": "neighbouring", "center": "centre", "centers": "centres", "centered": "centred", "favorite": "favourite", "gray": "grey",
            "incenter": "incentre", "incenters": "incentres", "circumcenter": "circumcentre", "circumcenters": "circumcentres", "orthocenter": "orthocentre",
            "orthocenters": "orthocentres", "excenter": "excentre", "excenters": "excentres",
            "analyze": "analyse", "behavior": "behaviour", "labeled": "labelled", "meter": "metre", "meters": "metres", "liter": "litre", "liters": "litres",
            "centimeter": "centimetre", "centimeters": "centimetres", "kilometer": "kilometre", "kilometers": "kilometres", "millimeter": "millimetre",
            "honor": "honour", "rumor": "rumour", "theater": "theatre", "catalog": "catalogue", "traveling": "travelling", "canceled": "cancelled",
            "factorize": "factorise", "minimize": "minimise", "maximize": "maximise", "organize": "organise", "recognize": "recognise"}
CONTESTS = r"\b(AIME|AMC|USAMO|USAJMO|UKMT|BMO|IMO|ISL|EGMO|CGMO|APMO|RMM|HMMT|ARML|PUMaC|CMIMC|SMT)\b"
THEOREMS = ["am-gm", "am-hm", "apollonius", "bezout", "brahmagupta", "burnside", "catalan", "cauchy", "ceva", "chinese remainder", "crt", "euler", "fermat", "fibonacci", "heron",
            "inclusion-exclusion", "jensen", "lagrange", "legendre", "lucas", "menelaus", "muirhead", "nesbitt", "pascal", "pick", "pigeonhole", "power of a point", "ptolemy",
            "pythagoras", "pythagorean", "schur", "stewart", "vieta", "wilson"]
WHY_LINE = re.compile(r"^<b>Why this works\.</b> <code>[a-z0-9-]+</code>(, <code>[a-z0-9-]+</code>)*: \S.*$", re.S)


def load_taxonomy(path=TAXONOMY):
    """Returns {id: status}, or None until the taxonomy exists."""
    if not path.exists():
        return None
    t = json.loads(path.read_text(encoding="utf-8"))
    rows = [*t.get("techniques", []), *t.get("configurations", [])]
    return {(x if isinstance(x, str) else x["id"]): ("" if isinstance(x, str) else x.get("status", "")) for x in rows}


def _prose(text, taxonomy=None):
    """The words a reader sees as English: no maths, no <code>, no taxonomy IDs and no title of the book."""
    t = re.sub(r"\$\$.*?\$\$|\$[^$]*\$", " ", text, flags=re.S)
    t = re.sub(r"<code>.*?</code>", " ", t, flags=re.S)
    t = re.sub(r"Beyond the Incenter", " ", t)
    if taxonomy:
        t = re.sub(r"\b[a-z0-9]+(?:-[a-z0-9]+)+\b", lambda m: " " if m.group() in taxonomy else m.group(), t)
    return t


def _names_in(text, names):
    """The names that occur in text as whole words, with hyphens and spaces treated alike."""
    t = " " + re.sub(r"[^a-z0-9]+", " ", text.lower()) + " "
    return [n for n in names if " " + re.sub(r"[^a-z0-9]+", " ", n.lower()).strip() + " " in t]


def _has_number(text, literal):
    return re.search(rf"(?<![\d./]){re.escape(str(literal))}(?![\d/]|\.\d)", text) is not None


def _public_fields(d):
    """(name, text) for everything shown to the public."""
    yield "title", d["title"]
    yield "statement", d["statement"]
    yield "solution", d["solution"]
    for h in d["hints"]:
        yield "hint", h
    for r in d.get("rubric", []):
        yield "rubric", r["criterion"]
    if d.get("figure_alt"):
        yield "figure_alt", d["figure_alt"]


def _answer_rules(d, fails, warns):
    kyu, fmt, key = d["kyu"], d.get("answer_format"), str(d["answer"])
    if fmt == "expression":
        fails.append("A2: answer_format expression isn't allowed, because the checker can't compare expressions")
    a = answers.canon(key)
    if a is None:
        return
    value = float(a)
    whole = value == int(value)
    if kyu in (5, 4, 3):
        if fmt != "integer_0_999":
            fails.append(f"A1: {kyu} kyu problems use integer_0_999, not {fmt}")
        if not (whole and 0 <= value <= 999):
            fails.append(f"A1: answer range: {kyu} kyu answers are integers from 0 to 999, got {key}")
    elif fmt not in ("integer", "integer_0_999", "rational"):
        fails.append(f"A1: {kyu} kyu problems use integer, integer_0_999 or rational, not {fmt}")
    if abs(value) >= 1e9:
        fails.append(f"A1: the answer {key} is not below 10^9")
    if fmt == "integer_0_999" and not (whole and 0 <= value <= 999):
        fails.append(f"A1: answer format: integer_0_999 but the answer is {key}")
    if fmt == "integer" and not whole:
        fails.append(f"A1: answer format: integer but the answer is {key}")
    if "." in key:
        fails.append(f"A3: decimals aren't used as keys, got {key}")
    elif "/" in key:
        top, bottom = key.replace(" ", "").split("/")
        f = Fraction(int(top), int(bottom))
        if f.numerator != int(top) or f.denominator != int(bottom):
            fails.append(f"A3: {key} isn't in lowest terms")
        if len(top.lstrip("-")) > 3 or len(bottom) > 3:
            fails.append(f"A3: {key} has more than three digits in a part")
    if fmt == "rational" and not re.search(r"fraction|lowest terms|decimal", d["statement"], re.I):
        fails.append("S3: a rational answer needs a sentence in the statement giving its format")
    if value in (0, 1):
        fails.append(f"A6: the answer {key} is guessable")
    if _has_number(d["statement"], key):
        fails.append(f"A6: the answer {key} appears in the statement")
    if not _has_number(d["solution"], key):
        warns.append("M3: the solution never states the answer in that form")
    for i, h in enumerate(d["hints"]):
        if len(key) >= 2 and _has_number(h, key):
            fails.append(f"H4: hint {i + 1} gives away the answer")
    if len(key) and _has_number(re.sub(r"[^0-9/.]+", " ", d["title"]), key):
        fails.append(f"S13: the title gives away the answer {key}")


def _latex_and_markup(name, text, fails):
    maths = re.findall(r"\$\$.*?\$\$|\$[^$]*\$", text, flags=re.S)
    for m in maths:
        if "*" in m:
            fails.append(f"S9: {name} uses * in maths; use \\cdot")
        if re.search(r"\\[dt]?frac(?!\s*\{)", m):
            fails.append(f"S9: {name} has a fraction without braces")
        if m.startswith("$$") and re.search(r"\\frac", m):
            fails.append(f"S9: {name} uses \\frac in display maths; use \\dfrac")
        if re.search(r"\\[lg]eq\b", m):
            fails.append(f"S9: {name} uses \\leq or \\geq; use \\le or \\ge")
    plain = re.sub(r"\$\$.*?\$\$|\$[^$]*\$", " ", text, flags=re.S)
    if re.search(r"\*\*|`|^\s*(?:[-*]|\d+\.)\s", plain, flags=re.M):
        fails.append(f"S10: {name} uses Markdown, which the site doesn't render")


def run(draft, taxonomy=None):
    d = draft
    taxonomy = load_taxonomy() if taxonomy is None else taxonomy
    fails, warns = [], []

    if d["type"] == "proof" and d["kyu"] > 3:
        fails.append(f"K4: proofs are 3 to 1 kyu only, and this is {d['kyu']} kyu")
    if d["type"] == "answer" and d["kyu"] < 3:
        fails.append(f"K4: answer problems are 8 to 3 kyu only, and this is {d['kyu']} kyu")
    if not 2 <= len(d["hints"]) <= 3:
        fails.append(f"H1: hint count: {len(d['hints'])}, the standard asks for two or three")
    if d["type"] == "answer":
        _answer_rules(d, fails, warns)
    if len(d["hints"]) > 1 and len(d["hints"][-1]) < len(d["hints"][0]) * 0.5:
        warns.append("hint order: the last hint is much shorter than the first, so check they get stronger")

    statement = re.sub(r"\$\$.*?\$\$|\$[^$]*\$", " ", d["statement"], flags=re.S)
    if d["type"] == "answer" and (statement.count("?") > 1 or (re.search(r"\(a\)", statement) and re.search(r"\(b\)", statement))):
        fails.append("S1: the statement asks more than one thing")

    public = list(_public_fields(d))
    for name, text in public:
        for w in re.findall(r"[A-Za-z]+", _prose(text, taxonomy)):
            uk = US_TO_UK.get(w.lower())
            if uk:
                fails.append(f'S8: UK spelling: {name} has "{w}", which should be "{uk}"')
        _latex_and_markup(name, text, fails)

    if d.get("provenance", {}).get("kind") == "original":
        for name, text in public:
            m = re.search(CONTESTS, re.sub(r"\$\$.*?\$\$|\$[^$]*\$", " ", text, flags=re.S))
            if m:
                fails.append(f"S12: an original problem names the contest {m.group(1)} in its {name}")
        names = THEOREMS + list(taxonomy or ())
        for name, text in (("title", d["title"]), ("id", d["id"])):
            found = _names_in(text, names)
            if found:
                fails.append(f'S13: the {name} gives away the technique "{found[0]}"')
    if d.get("inspired_by") and any(d["inspired_by"] in t for _, t in public):
        fails.append("O5: the public text mentions its private inspired_by ID")
    if d["type"] == "answer" and d.get("provenance", {}).get("pipeline_run") and not d.get("inspired_by"):
        fails.append("O4: a generated draft must set inspired_by")

    last = re.split(r"\n\s*\n", d["solution"].strip())[-1].strip()
    if not WHY_LINE.match(last):
        fails.append('M4: the solution\'s last paragraph must be the "Why this works" line')
    else:
        ids = re.findall(r"<code>([a-z0-9-]+)</code>", last.split(":", 1)[0])
        for i in ids:
            if i not in d["subtopics"]:
                fails.append(f"M4: {i} is in the Why this works line but not in subtopics")
            if taxonomy is not None and i not in taxonomy:
                fails.append(f"M4: {i} isn't in data/taxonomy.json")
    if taxonomy is not None:
        for s in d["subtopics"]:
            if s not in taxonomy:
                fails.append(f"M5: subtopic {s} isn't in data/taxonomy.json")
            elif taxonomy[s] == "legacy":
                fails.append(f"M5: subtopic {s} is marked legacy")

    fails = list(dict.fromkeys(fails))
    ev = {"failures": fails, "warnings": warns}
    if fails:
        return "fail", fails[0] + (f" (and {len(fails) - 1} more)" if len(fails) > 1 else ""), ev
    return "pass", "automatable standard rules hold" + (f"; warnings: {'; '.join(warns)}" if warns else ""), ev
