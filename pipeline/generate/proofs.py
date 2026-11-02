"""Original proof problems for 3-1 kyu, with task 09's checks. Cheapest checks first, and any doubt discards.

python -m pipeline.generate.proofs --slots 3G,3N,2G --run NAME [--concurrency 2] [--stop-file path]

There is no olympiad corpus, so originality rests on two known-problem checks from memory. Nothing here reads
contest text except the gate's comparison with the AMC and AIME corpus, which never reaches a report.
"""
import argparse
import ast
import json
import random
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ..verify import gate, originality, sandbox
from ..verify.backend import ModelError, PlanLimit, Usage, last_json, make_backend
from ..verify.config import OPUS, SONNET
from . import drafts, prompts
from .config import AUTHOR, PENDING, private_dir

# Kevin's ladder in js/lib/ranks.js, which is one kyu harder than section 1.4 of the standard for proofs.
ANCHORS = {3: "an olympiad opener: a late BMO1 problem, a Balkan MO or Canadian MO first problem, or an easy USAJMO opener. Below IMO P1",
           2: "IMO P1/P4, USAMO P1/P4, USEMO P1/P4, or the middle of a Balkan MO or Canadian MO paper",
           1: "IMO P3/P6, the hardest USAMO and USEMO problems, or the last problem of a Canadian MO paper. Deep: nothing in the statement points at the crux"}
THEMES = {
    "G": ["a circle through two feet or midpoints, reached by one auxiliary point", "two circles and a common chord or tangent, with an equal-length conclusion", "a reflection of a triangle centre and a concyclicity", "a spiral similarity hidden in two intersecting circles",
          "isogonal lines and a point on the circumcircle", "an excircle configuration with a collinearity", "a moving point and a fixed point or fixed circle", "an inversion or a projective map that the statement does not suggest"],
    "N": ["orders modulo a prime and a divisibility for all n", "valuations in a sum or a product of consecutive terms", "a Diophantine equation closed by size and residues", "a sequence that must contain infinitely many primes or prime factors"],
    "A": ["an inequality with a natural equality case and no heavy machinery", "a functional equation over the reals or positive integers", "a polynomial whose values or roots are constrained", "a recursive sequence with a hidden invariant"],
    "C": ["an invariant or monovariant in a process", "a double count on a grid or a graph", "an extremal argument with a construction", "a two-player game with a pairing or a potential"],
}
THINK = {3: "about 1,500 words", 2: "about 2,500 words", 1: "about 3,500 words"}
BLIND_CAP = {3: 16000, 2: 24000, 1: 32000}
SLOT_BUDGET = {3: 3.0, 2: 4.0, 1: 5.0}  # API-equivalent. No new candidate starts past this, so one slot can't eat the week.
MIN_TESTS = 200
FLAWED_RANGES = {"stops_short": (1, 3), "missing_case": (4, 6)}
TOPICS = {"A": "algebra", "C": "combinatorics", "G": "geometry", "N": "number theory"}
_write = threading.Lock()

IDEA = """Write {n} candidate olympiad proof problems in {topic}, for {kyu} kyu on Cevian. The target is {anchor}.

The style is that of USAMO, USEMO, the Balkan MO, the Canadian MO and the IMO, adapted and never copied. A short natural statement that a solver wants to know the truth of, one claim, no bolted-on parts. Theme to start from: {theme}.

Rules:
- You must have an actual proof. The sketch is the real route in at most ten lines, with the crux named. Never state something you merely believe.
- If you recognise the statement, or something equivalent up to renaming, as a published contest problem or a named theorem or a well-known lemma, drop it and write another. A strict check compares it with everything you could remember, and it rejects restated configuration lemmas (excircle collinearities, tangent-length identities and so on). Do not use mixtilinear circles at all: every such attempt so far has been rejected. Standard lemmas may be steps, but the claim itself must need its own thought.
- Pick the difficulty from how hidden the crux is, not from length. A computation slog fails. So does anything ambiguous.
- Every point, set and domain is defined. Say whether points lie on sides or lines. Give only the conditions the proof needs, but exclude every degenerate case the statement would fail on.
- Use "Prove that" or "Determine all". For "Determine all" the answer must be unique and clear.
- UK spelling. $...$ and $$...$$ for maths, \\le and \\ge, \\cdot for products, no * and no custom macros. No Markdown. The statement must stand without a figure.
- The title gives nothing away: no technique, theorem or answer.

Already tried, so go elsewhere: {tried}

Output, repeated {n} times, with nothing around it:
<candidate>
<title>Title.</title>
<statement>The statement.</statement>
<sketch>The route, with the crux named.</sketch>
<interest>1 to 10, honestly.</interest>
</candidate>"""

SEARCH = """Write a Python program that tries to find a counterexample to this claim. You have only the claim.

<claim>
{statement}
</claim>

Test the claim itself, from its definitions, not any route to a proof. Number theory: exhaust parameters as far as 60 seconds allows, up to $10^6$ where that makes sense. Combinatorics and games: exhaust all small cases. Algebra: a dense grid plus pseudo-random points, with exact arithmetic where possible. Geometry: build at least 500 pseudo-random non-degenerate configurations with mpmath at 50 digits or Fractions, and test the conclusion to a tolerance of $10^{{-20}}$. "Determine all" claims: test that what is claimed works and search for anything else, using the sketch below only to know the claimed answer.

<claimed_answer>{sketch}</claimed_answer>

Allowed imports only: {imports}. The time and random modules are banned, so write a small linear congruential generator. It must finish well inside 60 seconds on a slow machine, and a timeout loses the problem, so choose small loop limits: aim for 15 seconds, with mpmath configurations costing about a millisecond per operation. Skip degenerate configurations and do not count them.
The last line printed must be exactly one of: TESTED <number of real cases checked> or COUNTEREXAMPLE <short data> or NOT_TESTABLE <reason>. Use NOT_TESTABLE only if no finite search touches the claim.
Output only the Python source, with no fence."""

KNOWN = """You guard a bank of olympiad problems against copies. There is no database to compare with, so your memory of contest problems is the only check. Search it hard: IMO, IMO Shortlist, USAMO, USAJMO, USEMO, USA TSTST and TST, Balkan MO and its shortlist, Canadian MO, China MO and CGMO, EGMO, APMO, RMM, BMO1 and BMO2, ELMO, Iberoamerican, Russian and All-Russian, Japan MO, Korea, Iran, Vietnam, and well-known lemmas and named theorems.

<problem>
{statement}
</problem>

Name the three closest things you can recall and how close each is, in your own words and never quoting. Reply with JSON only:
{{"closest":[{{"source":"<contest and year, or lemma name>","how_close":"same|same-up-to-setting|same-key-lemma|same-technique-only","note":"<max 20 words>"}}],"known":true|false,"unsure":true|false}}
known is true only if: any is "same" or "same-up-to-setting"; or the claim itself is a named theorem or a standard lemma; or a "same-key-lemma" match where a solver who knows that source would finish with no new thought. A standard lemma used as one step among others, with real work left, is not known. unsure is true only if you recall the statement itself but cannot place it, not for a general feeling about the area."""

DISPROVE = """Try to break this olympiad claim. Assume it is false and look for a counterexample: small cases, degenerate and extreme configurations, boundary values, and a configuration or order of points the author did not picture. Also look for ways the statement is ill-posed: an undefined object, a case where something doesn't exist, a condition that makes it vacuous.

<claim>
{statement}
</claim>

Think hard but stop after about 2,500 words. Reply with JSON only:
{{"refuted":true|false,"counterexample":"<explicit, or empty>","ill_posed":["<max 25 words each>"],"doubts":["<a specific reason to doubt it, max 25 words>"]}}
Do not list vague doubts. An empty list is a good result."""

WRITE = """A {kyu} kyu olympiad proof problem has been chosen. Write its model solution, hints and rubric.

THE CEVIAN STANDARD
{standard}

{figure_rules}

TAXONOMY IDS, the only tags allowed
{taxonomy}

THE PROBLEM
{statement}

THE AUTHOR'S SKETCH, which may be wrong
{sketch}

Rules on top of the standard, each enforced:
- The solution is a complete proof with every case, for a competent reader who needs no filling-in. If you find the claim false or the sketch unfixable, reply with only <disagree>one sentence</disagree>.
- {style}
- {length}
- If another route exists, a final <b>Remark.</b> gives it in a sentence or two.
- Use only <b> and <code> as markup. No Markdown, no lists. UK spelling. \\dfrac in display maths, \\frac inline, \\cdot, \\le, \\ge.
- Two or three hints. Hint 1 points at the object and doesn't name the technique. No hint finishes the proof.
- Rubric lines total exactly 7, the hardest idea gets the most, each line is an achievement seen in a script, worded so other routes can earn it. At most one "Deduct 1 if ..." per line, naming a common error. A correct answer alone earns at most 1 on a "Determine" problem. End with a line that says a complete proof by another route earns all marks, inside the last criterion.
- A program will mark scripts from this later, so each criterion must be checkable by itself. Where a real second route exists, give it as an <alternative> whose steps also total exactly 7. Do not invent a route you haven't checked: if none exists, leave it out. Give at least one <fatal>: a common error that invalidates a script, with the most marks such a script can earn (0 to 6).
{earlier}
Output with nothing around it:
<subtopics>Taxonomy IDs separated by commas, the main one first.</subtopics>
<hint>Hint 1.</hint>
<hint>Hint 2.</hint>
<hint>Hint 3 (optional).</hint>
<solution>The solution.</solution>
<rubric marks="3">One criterion. Repeat this tag for each line.</rubric>
<alternative name="The route's name"><step marks="4">One criterion.</step><step marks="3">Another.</step></alternative>
<fatal cap="2">A common fatal error. Repeat this tag for each.</fatal>
<figure>The tkz-euclide figure. Required for geometry.</figure>
<no_figure>Only if this isn't geometry and the proof doesn't use a picture: one sentence why.</no_figure>"""

LINE_AUDIT = """You are a strict olympiad marker auditing a model solution that someone else wrote. Go through it line by line. For each inference ask: does this actually follow, is every case and configuration covered, is any cited result correctly stated and applicable, does it depend on a picture? Check the rubric totals 7 and matches the proof.

<problem>
{statement}
</problem>

<solution>
{solution}
</solution>

<rubric>
{rubric}
</rubric>

Reply with JSON only: {{"proves_the_claim":true|false,"issues":[{{"severity":"material"|"cosmetic","where":"<short>","issue":"<max 30 words>"}}],"estimated_kyu":3|2|1|4,"crux_hidden":"open|near|hidden|deep"}}
estimated_kyu: 4 is below an olympiad opener; 3 an olympiad opener; 2 IMO P1/P4; 1 IMO P3/P6. An empty issues list is a good result, but only say so if you checked."""

BLIND = """Prove the following, or if it asks you to determine something, determine it and prove your answer. Write a complete rigorous proof, as for an olympiad script. If you cannot finish, say exactly where your proof stops, and do not paper over a gap. If you believe the claim is false, say so and give a counterexample.

{statement}"""

MARK = """You mark an olympiad script against a rubric. You did not write the script or the model solution. Be strict: a gap, an unjustified claim, a missed case or a false step costs marks, however good the rest looks. A complete proof by another route earns 7, so judge it on its own terms.

<problem>
{statement}
</problem>

<model_solution>
{solution}
</model_solution>

<rubric>
{rubric}
</rubric>

<script>
{script}
</script>

Reply with JSON only: {{"lines":[{{"line":1,"awarded":0,"why":"<max 20 words>"}}],"total":0,"complete":true|false,"errors":["<max 25 words>"],"says_claim_false":true|false}}
complete means a rigorous, gap-free proof that deserves 7."""

FLAWED = """You write deliberately flawed olympiad proofs, to test a marking rubric. Write two scripts for this problem, as a real student would, with no comment that they are flawed.

<problem>
{statement}
</problem>

<model_solution>
{solution}
</model_solution>

Script 1 makes real early progress, then stops short of the crux or asserts the crux with no argument. Script 2 is a proof with the crux in place and correct, but it silently omits one needed case or leaves one real gap near the end.

Output only:
<stops_short>Script 1.</stops_short>
<missing_case>Script 2.</missing_case>"""


def _tag(text, name):
    return prompts._tag(text, name)


def parse_candidates(text):
    out = []
    for block in re.findall(r"<candidate>(.*?)</candidate>", text, re.S):
        c = {k: _tag(block, k) for k in ("title", "statement", "sketch")}
        m = re.search(r"\d+(\.\d+)?", _tag(block, "interest"))
        c["interest"] = float(m.group()) if m else 0.0
        if all(c[k] for k in ("title", "statement", "sketch")):
            c["statement"] = drafts.tidy_latex(c["statement"])
            out.append(c)
    return out


def parse_rubric(text):
    return [dict(marks=int(m), criterion=c.strip()) for m, c in re.findall(r'<rubric marks="(\d+)">(.*?)</rubric>', text, re.S)]


def parse_marking(text):
    """The rubric as data for an AI marker later. Tags, because LaTeX breaks JSON escaping. The site reads rubric, built from the same milestones."""
    clean = drafts.tidy_latex
    return dict(
        milestones=[dict(id=f"m{i + 1}", marks=r["marks"], criterion=clean(r["criterion"])) for i, r in enumerate(parse_rubric(text))],
        alternative_routes=[dict(name=name, milestones=[dict(id=f"a{i + 1}", marks=int(m), criterion=clean(c.strip())) for i, (m, c) in enumerate(re.findall(r'<step marks="(\d+)">(.*?)</step>', block, re.S))])
                            for name, block in re.findall(r'<alternative name="(.*?)">(.*?)</alternative>', text, re.S)],
        fatal_errors=[dict(error=clean(e.strip()), cap=int(c)) for c, e in re.findall(r'<fatal cap="(\d+)">(.*?)</fatal>', text, re.S)])


def apply_marking(d, text):
    d["marking"] = parse_marking(text)
    d["rubric"] = [dict(marks=m["marks"], criterion=m["criterion"]) for m in d["marking"]["milestones"]]


def rubric_text(d):
    m = d["marking"]
    lines = [f"{i + 1}. [{r['marks']} marks] {r['criterion']}" for i, r in enumerate(d["rubric"])]
    for route in m["alternative_routes"]:
        lines += [f"Alternative route, {route['name']}:"] + [f"- [{s['marks']} marks] {s['criterion']}" for s in route["milestones"]]
    lines += [f"Fatal error, at most {f['cap']} marks: {f['error']}" for f in m["fatal_errors"]]
    return "\n".join(lines)


def in_range(kind, total):
    low, high = FLAWED_RANGES[kind]
    return low <= total <= high


def lint_proof(d):
    """The write-up rules that aren't in the gate."""
    if sum(r["marks"] for r in d["rubric"]) != 7:
        return "the rubric must total exactly 7 (P12)"
    m = d["marking"]
    if any(sum(s["marks"] for s in r["milestones"]) != 7 for r in m["alternative_routes"]):
        return "each <alternative> must have steps totalling exactly 7"
    if not m["fatal_errors"] or any(not 0 <= f["cap"] <= 6 for f in m["fatal_errors"]):
        return "give at least one <fatal>, each with a cap from 0 to 6"
    return drafts.lint(d) or next(filter(None, map(drafts._lint_text, [r["criterion"] for r in d["rubric"]])), None)


class Discard(Exception):
    """Carries the stage and reason. A discard is a result, not an error."""
    def __init__(self, stage, reason):
        super().__init__(reason)
        self.stage, self.reason = stage, reason


def extract_code(text):
    """The Python in a reply that may wrap it in prose or a fence: the longest fenced block, else from the first code-like line, dropping trailing prose until it parses."""
    fences = re.findall(r"```(?:python|py)?[ \t]*\n(.*?)```", text, re.S)
    if fences:
        return max(fences, key=len).strip()
    lines = text.strip().splitlines()
    start = next((i for i, x in enumerate(lines) if re.match(r"(import |from \w+ import |def |class |#|[A-Za-z_]\w*\s*=)", x)), 0)
    lines = lines[start:]
    while lines:
        try:
            ast.parse("\n".join(lines))
            break
        except SyntaxError:
            lines.pop()
    return "\n".join(lines).strip() or text.strip()


class Job:
    def __init__(self, backend, index, threshold, run):
        self.backend, self.index, self.threshold, self.run = backend, index, threshold, run

    def call(self, usage, model, system, prompt, cap, role, owner, effort="medium"):
        r = self.backend.call(model, system, prompt, effort, cap, cacheable=True, role=role, draft_id=owner)
        usage.add(r)
        return r

    # ---- Cheap checks, on the statement alone.
    def search(self, c, usage, topic):
        r = self.call(usage, SONNET, "You write careful search programs. You have no tools. Output only Python source.",
                      SEARCH.format(statement=c["statement"], sketch=c["sketch"][:400] if "etermine" in c["statement"] else "not needed: this is a Prove that claim", imports=", ".join(sorted(sandbox.ALLOWED_IMPORTS))), 8000, "proof_search", c["title"])
        src = extract_code(r.text)
        reason, _ = sandbox.static_check(src)
        result = None if reason else sandbox.run_program(src)
        lines = [x.strip() for x in (result.stdout if result and result.ok else "").splitlines() if x.strip()]
        last = lines[-1] if lines else ""
        ev = dict(model=r.model, program=src, last_line=last[:300], error=reason or (None if result and result.ok else (result.error if result else "")))
        if last.startswith("COUNTEREXAMPLE"):
            raise Discard("counterexample_search", last[:200])
        if last.startswith("TESTED"):
            n = int(re.search(r"\d+", last).group()) if re.search(r"\d+", last) else 0
            if n < MIN_TESTS and topic == "G":
                raise Discard("counterexample_search", f"only {n} configurations were tested")
            return ("pass", f"no counterexample in {n} cases", ev)
        if last.startswith("NOT_TESTABLE") and topic != "G":
            return ("skip", f"no finite search applies: {last[:160]}", ev)
        raise Discard("counterexample_search", f"the search didn't complete: {str(ev['error'])[:160] or last[:160]}")

    def known(self, c, usage):
        rows = []
        for model in (OPUS, SONNET):
            r = self.call(usage, model, "You have an excellent memory of olympiad problems. You have no tools. Never quote a problem.", KNOWN.format(statement=c["statement"]), 6000, "proof_known", c["title"])
            d = last_json(r.text)
            if d is None:
                raise Discard("known_problem", "the reply was unreadable")
            rows.append(dict(model=r.model, **d))
            near = (d.get("closest") or [{}])[0]
            line = f"{r.model}: {near.get('source', 'unnamed')}: {near.get('note', '')}"[:200]
            if model == OPUS and (d.get("known") or d.get("unsure")):
                raise Discard("known_problem", line)
            if model == SONNET and (d.get("known") or d.get("unsure")):
                # In the first 30 candidates Sonnet "recalled" nearly every statement with no contest or year, so a vague memory goes to Kevin. A placed one discards.
                if re.search(r"(19|20)\d\d", str(near.get("source"))) and near.get("how_close") in ("same", "same-up-to-setting"):
                    raise Discard("known_problem", line)
                return ("investigate", f"Opus recalls nothing, but Sonnet has an unplaced memory: {line}", dict(answers=rows, corpus_compared=False))
        return ("pass", "two independent models recall no matching problem. There is no olympiad corpus, so this rests on memory alone", dict(answers=rows, corpus_compared=False))

    def disprove(self, c, usage):
        r = self.call(usage, OPUS, "You break olympiad problems. You have no tools.", DISPROVE.format(statement=c["statement"] + (f"\n\nThe author's claimed answer and route: {c['sketch']}" if "etermine" in c["statement"] else "")), 12000, "proof_disprove", c["title"])
        d = last_json(r.text)
        if d is None:
            raise Discard("disprove", "the reply was unreadable")
        if d.get("refuted") or d.get("ill_posed") or d.get("doubts"):
            raise Discard("disprove", str(d.get("counterexample") or (d.get("ill_posed") or d.get("doubts"))[0])[:240])
        return ("pass", "a model trying to break it found nothing", dict(model=r.model, **d))

    # ---- The write-up, with the free checks and the gate.
    def write(self, c, kyu, topic, usage, earlier=""):
        text = prompts._standard()
        standard = "\n\n".join([prompts._section(text, "## 5. Hint rules", "## 6. What makes a problem bad"), prompts._section(text, "## 8. Proof problems", "### 8.5 Worked example"), prompts._section(text, "## 2. Statement rules", "## 3. Answer rules")])
        prompt = WRITE.format(kyu=kyu, standard=standard, figure_rules=prompts.FIGURE_RULES, taxonomy=prompts.taxonomy_ids(), statement=c["statement"], sketch=c["sketch"], earlier=earlier, style=prompts.SOLUTION_STYLE, length=prompts.length_guide(kyu))
        r = self.call(usage, OPUS, prompts.WRITE_SYSTEM.replace("about 1,500 words", THINK[kyu]), prompt, 24000, "proof_write", c["title"])
        return r.text

    def draft(self, c, kyu, topic, usage):
        """A draft that passes every free check, with up to two repairs."""
        earlier = ""
        for _ in range(3):
            text = self.write(c, kyu, topic, usage, earlier)
            w = prompts.parse_write_up(text)
            if w and w.get("disagree"):
                raise Discard("write_up", f"the writer found this fault: {w['disagree']}"[:240])
            rubric = parse_rubric(text)
            if not w or not rubric:
                earlier, problem = "", "the reply was incomplete"
                continue
            pid = drafts.allocate_id(c["title"], c["title"])
            d = dict(id=pid, title=c["title"], kyu=kyu, topic=topic, subtopics=w["subtopics"], type="proof", status="draft", statement=c["statement"],
                     hints=[drafts.tidy_latex(h) for h in w["hints"]], solution=drafts.tidy_latex(w["solution"]),
                     provenance=dict(kind="original", author=AUTHOR, pipeline_run=self.run), stats=dict(solves=0, attempts=0, liked=0), variation_recipe="olympiad-style")
            apply_marking(d, text)
            problem = drafts.attach_figures(d, w)
            if not problem:
                step = drafts.write_checks_proof(d)
                problem = step and f"{step[0]}: {step[1]}"
            if not problem:
                problem = lint_proof(d)
            if not problem:
                return d
            earlier = f"\nYOUR EARLIER ATTEMPT\n{text}\n\nWHY IT WAS REJECTED\n{problem}\n\nFix the cause and send every part again, including the whole figure.\n"
        raise Discard("write_up", f"free checks still failing after repairs: {problem}"[:240])

    def line_audit(self, d, usage):
        r = self.call(usage, OPUS, "You audit olympiad solutions. You have no tools.", LINE_AUDIT.format(statement=d["statement"], solution=d["solution"], rubric=rubric_text(d)), 12000, "proof_audit", d["id"])
        a = last_json(r.text)
        if a is None:
            raise Discard("line_audit", "the reply was unreadable")
        bad = [x for x in a.get("issues") or [] if isinstance(x, dict) and x.get("severity") == "material"]
        if bad or not a.get("proves_the_claim"):
            return ("fail", (bad[0]["issue"] if bad else "it does not prove the claim")[:240], dict(model=r.model, **a))
        return ("pass", f"line by line, no material issue; the critic rates it {a.get('estimated_kyu')} kyu with a {a.get('crux_hidden')} crux", dict(model=r.model, **a))

    # ---- Blind attempts and the marker.
    def mark(self, d, script, usage):
        r = self.call(usage, OPUS, "You mark olympiad scripts. You have no tools.", MARK.format(statement=d["statement"], solution=d["solution"], rubric=rubric_text(d), script=script), 8000, "proof_mark", d["id"])
        m = last_json(r.text)
        if m is None:
            raise Discard("marker", "the reply was unreadable")
        return dict(total=m.get("total", 0), complete=bool(m.get("complete")), errors=m.get("errors", []), lines=m.get("lines", []), says_claim_false=bool(m.get("says_claim_false")), model=r.model)

    def blind(self, d, usage):
        attempts = []
        statement = d["statement"] + (f"\n\nFigure: {d['figure_alt']}" if d.get("figure_alt") else "")
        for i, model in enumerate((OPUS, SONNET, SONNET)):
            r = self.backend.call(model, "You are a very strong olympiad contestant. You have no tools.", BLIND.format(statement=statement), "medium", BLIND_CAP[d["kyu"]], salt=f"attempt-{i}", cacheable=True, role="proof_blind", draft_id=d["id"])
            usage.add(r)
            attempts.append(dict(model=r.model, output_tokens=r.output, truncated=r.truncated, script=r.text, mark=self.mark(d, r.text, usage) if r.text.strip() and not r.truncated else None))
        if any(a["mark"] and a["mark"]["says_claim_false"] for a in attempts) or any(re.search(r"\b(the claim|statement) is false\b|counterexample:", a["script"], re.I) for a in attempts):
            raise Discard("blind_attempts", "a blind attempt says the claim is false, which needs a person, so it is discarded")
        good = [a for a in attempts if a["mark"] and a["mark"]["complete"] and a["mark"]["total"] == 7]
        scores = ", ".join(str(a["mark"]["total"]) if a["mark"] else "no script" for a in attempts)
        if not good:
            raise Discard("blind_attempts", f"no attempt was marked complete (scores {scores})")
        status = "investigate" if d["kyu"] < 3 and len(good) == 3 else "pass"
        reason = f"{len(good)} of 3 blind attempts marked complete (scores {scores})" + (". All three finished, so this may be easier than its kyu" if status == "investigate" else "")
        return (status, reason, dict(attempts=attempts))

    def rubric_test(self, d, usage):
        r = self.call(usage, SONNET, "You write realistic student scripts. You have no tools.", FLAWED.format(statement=d["statement"], solution=d["solution"]), 10000, "proof_flawed", d["id"])
        tests = []
        for kind in FLAWED_RANGES:
            script = _tag(r.text, kind)
            if not script:
                raise Discard("rubric_test", "the flawed scripts were incomplete")
            tests.append(dict(kind=kind, expected=FLAWED_RANGES[kind], script=script, mark=self.mark(d, script, usage)))
        wrong = [t for t in tests if not in_range(t["kind"], t["mark"]["total"])]
        ev = dict(attempts=tests)
        if wrong:
            return ("fail", f"{wrong[0]['kind']} scored {wrong[0]['mark']['total']}, expected {wrong[0]['expected']}", ev)
        return ("pass", "; ".join(f"{t['kind']} scored {t['mark']['total']}" for t in tests), ev)

    # ---- One candidate, then one slot.
    def candidate(self, c, kyu, topic, usage):
        early = []
        for name, step in (("counterexample_search", lambda: self.search(c, usage, topic)), ("known_problem", lambda: self.known(c, usage)), ("disprove", lambda: self.disprove(c, usage))):
            early.append((name, step()))
        d = self.draft(c, kyu, topic, usage)
        report = None
        for repair in range(2):
            report = gate.verify(d, self.backend, index=self.index, has_corpus=True, auto_fail=self.threshold)
            if report.get("plan_limit"):
                raise PlanLimit(report["verdict"])
            if report["verdict"].startswith("ERROR"):
                raise ModelError(report["verdict"][:200])
            failed = next((x for x in report["checks"] if x["status"] in ("fail", "investigate")), None)
            if not failed:
                break
            if failed["check"] not in ("solution_audit", "figure_critic") or repair:
                raise Discard(failed["check"], failed["reason"][:240])
            # One rewrite for a fault in the write-up. A fault in the statement or originality discards.
            earlier = f"\nYOUR EARLIER SOLUTION\n{d['solution']}\n\nA CRITIC SAYS\n{failed['reason']}\n\nFix it properly, or disagree if it can't be fixed. Send every part again.\n"
            text = self.write(c, kyu, topic, usage, earlier)
            w = prompts.parse_write_up(text)
            rubric = parse_rubric(text)
            if not w or w.get("disagree") or not rubric:
                raise Discard("write_up", f"the repair failed: {(w or {}).get('disagree', 'incomplete')}"[:240])
            d.update(subtopics=w["subtopics"], hints=[drafts.tidy_latex(h) for h in w["hints"]], solution=drafts.tidy_latex(w["solution"]))
            apply_marking(d, text)
            problem = drafts.attach_figures(d, w) or lint_proof(d)
            if problem:
                raise Discard("write_up", str(problem)[:240])
        for name, step in (("line_audit", lambda: self.line_audit(d, usage)), ("blind_attempts", lambda: self.blind(d, usage)), ("rubric_test", lambda: self.rubric_test(d, usage))):
            status, reason, ev = step()
            if status == "fail":
                raise Discard(name, reason)
            early.append((name, (status, reason, ev)))
        report["checks"] += [dict(check=name, status=s, reason=reason, evidence=ev) for name, (s, reason, ev) in early]
        report["notes"].append("Proof checks ran on this draft. No olympiad corpus exists, so originality against olympiads rests on the known_problem check from memory.")
        report["verdict"] = gate.verdict_line(report["checks"])
        report["usage_proof_pipeline"] = usage.summary()
        return d, report

    def slot(self, spec, seed):
        kyu, topic = int(spec[0]), spec[1]
        rng = random.Random(f"{seed}:{spec}")
        usage = Usage()
        log = dict(slot=spec, kyu=kyu, topic=topic, candidates=[], outcome=None)
        themes = rng.sample(THEMES[topic], len(THEMES[topic]))
        for round_ in range(3):
            if usage.fresh_usd > SLOT_BUDGET[kyu] or log["outcome"]:
                break
            tried = "; ".join(x["title"] for x in log["candidates"]) or "nothing yet"
            r = self.call(usage, OPUS, prompts.SYSTEM.replace("about 1,500 words", THINK[kyu]).replace("Never test parameters or compute answers in your head.", ""),
                          IDEA.format(n=2, topic=TOPICS[topic], kyu=kyu, anchor=ANCHORS[kyu], theme=themes[round_ % len(themes)], tried=tried), 24000, "proof_ideas", spec)
            for c in sorted(parse_candidates(r.text), key=lambda x: -x["interest"]):
                row = dict(title=c["title"], statement=c["statement"], interest=c["interest"])
                log["candidates"].append(row)
                if usage.fresh_usd > SLOT_BUDGET[kyu]:
                    row["skipped"] = "slot budget"
                    continue
                try:
                    d, report = self.candidate(c, kyu, topic, usage)
                except Discard as e:
                    row.update(discarded_at=e.stage, reason=e.reason)
                    continue
                PENDING.mkdir(parents=True, exist_ok=True)
                (PENDING / f"{d['id']}.json").write_text(json.dumps(dict(draft=d, report=report), indent=2, ensure_ascii=False), encoding="utf-8")
                row.update(saved=d["id"], verdict=report["verdict"])
                log["outcome"] = "accept"
                break
        log["outcome"] = log["outcome"] or "discard"
        log["usd"] = round(usage.fresh_usd, 3)
        return log


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--slots", required=True, help="comma-separated kyu and topic, such as 3G,2N")
    ap.add_argument("--run", required=True)
    ap.add_argument("--seed", type=int, default=9)
    ap.add_argument("--concurrency", type=int, default=2)
    ap.add_argument("--stop-file")
    ap.add_argument("--backend", choices=["cli", "api"], default="cli", help="cli uses the plan; api needs ANTHROPIC_API_KEY and costs money")
    a = ap.parse_args()
    backend = make_backend(a.backend, 6)
    index, has_corpus = originality.default_index()
    if not has_corpus:
        raise SystemExit("set CEVIAN_CORPUS")
    job = Job(backend, index, originality.load_threshold(), a.run)
    log_path = private_dir() / "runs" / a.run / "log.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    stop = Path(a.stop_file) if a.stop_file else None
    done = {json.loads(x)["key"] for x in log_path.read_text(encoding="utf-8").splitlines() if x.strip()} if log_path.exists() else set()
    specs = [s for s in a.slots.split(",") if s]

    def one(pair):
        i, spec = pair
        key = f"{i}:{spec}"
        if key in done or (stop and stop.exists()):
            return
        try:
            row = job.slot(spec, a.seed + i)
        except (PlanLimit, ModelError) as e:
            print(f"{key}: stopped: {str(e)[:200]}", flush=True)
            return
        row["key"] = key
        with _write:
            with log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"{key}: {row['outcome']} usd={row['usd']} " + " | ".join(f"{c['title']}: {c.get('saved') or c.get('discarded_at')}: {str(c.get('reason', c.get('verdict', '')))[:110]}" for c in row["candidates"]), flush=True)

    with ThreadPoolExecutor(a.concurrency) as pool:
        list(pool.map(one, enumerate(specs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
