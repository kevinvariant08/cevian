"""The generator's prompts. Replies use tags, not JSON: LaTeX and Python both break JSON escaping constantly.

Two stages, because three full candidates worked out by hand used up a 32,000-token cap with nothing written:
ideas (statement and program, for three candidates), then a write-up of the chosen one. The sandbox computes
each key for free, so the model spends its effort on the idea and not on arithmetic.
"""
import json
import re

from ..verify.sandbox import ALLOWED_IMPORTS
from .config import STANDARD, TAXONOMY
from .recipes import RECIPES

SYSTEM = ("You write original maths contest problems for Kyuclid, a site ranked from 8 kyu (beginner) to 1 kyu (IMO). "
          "A good problem gives the solver one real moment of insight, reads naturally and is exactly right. "
          "You have no tools. Output only what the format asks for. "
          "Your thinking budget is small: stop thinking after about 1,500 words and start writing. Independent checks run on everything you write and "
          "send back anything wrong, so a good first idea written down beats a perfect one still being tested. Never test parameters or compute answers in your head.")

WRITE_SYSTEM = ("You write hints and solutions for Kyuclid, a maths contest site. You have no tools. Output only what the format asks for. "
                "Your thinking budget is small: stop thinking after about 1,500 words and start writing.")

IDEA_FORMAT = """<candidate>
<title>A short title that gives nothing away: no technique, theorem or answer.</title>
<recipe>{recipes}</recipe>
<topic>One of A, C, G, N.</topic>
<statement>The statement.</statement>
<sketch>The intended solution in at most five lines: the crux and the route. No full working.</sketch>
<check_program>Python source. No markdown fence.</check_program>
<interest>Your honest rating of how interesting this is, from 1 to 10.</interest>
<interest_reason>One sentence.</interest_reason>
</candidate>"""

WRITE_FORMAT = """<subtopics>Taxonomy IDs separated by commas, the one the crux turns on first.</subtopics>
<hint>Hint 1.</hint>
<hint>Hint 2.</hint>
<hint>Hint 3 (optional).</hint>
<solution>The solution.</solution>
<figure>A tkz-euclide figure, as described above. Repeat the block for a second figure, only if the argument has two separate pictures.</figure>
<no_figure>Only if this isn't topic G and the argument doesn't use a picture: one sentence saying why.</no_figure>"""

STYLE = """THE STYLE TO AIM FOR
The problem should read and feel like a real AIME problem: a short, clean statement, no contrived story, one satisfying crux, and an integer answer from 0 to 999, encoded as $m + n$ or similar where the AIME would do that. Use the same kinds of ideas and the same difficulty curve. Sharing an idea family with AIME problems is the goal. Copying is not: never reuse a specific problem's setting, numbers or phrasing, and never write a reskin."""

LOW_STYLE = """THE STYLE TO AIM FOR
The problem should read and feel like a real problem from the early or middle part of an AMC paper: one or two short, clean sentences, a real small idea, and a single checkable answer. It is free response: there are no answer options, and it must not depend on elimination. Short does not mean trivial. A bare calculation, a formula applied once, a one-step word problem or schoolbook arithmetic is not acceptable at any kyu here: the reviewer removed the bank's old easy problems for being "too easy and poor quality". Never reuse a specific problem's setting, numbers or phrasing, and never write a reskin."""

TOPICS = {"A": "algebra", "C": "combinatorics or probability", "G": "geometry", "N": "number theory"}

# Kevin's ladder, as in js/lib/ranks.js on main.
ANCHORS = {8: "the first three quarters of an AMC 8 paper", 7: "the end of an AMC 8 paper and AMC 10 problems 1 to 10", 6: "the middle of an AMC 10 or AMC 12 paper", 5: "late AMC 12 and AIME 1 to 5", 4: "AIME 6 to 10", 3: "AIME 11 to 15 and olympiad openers"}

# Pilot evidence: of 10 drafts aimed at 5 kyu, the ruler put 6 at 3 kyu and 1 at 2 kyu, and the reviewer moved one down to 4 kyu.
LOW_NOTE = """The reviewer's calibration so far: a problem whose whole difficulty is one divisibility or perfect-square observation was moved from 5 kyu down to 6 kyu. A problem was rejected for being loose about the form of its answer (say exactly what form is wanted), for being a slog with no idea, and for being ambiguous."""

CALIBRATION = {8: """CALIBRATING 8 KYU
This is an AMC 8 opener: one or two direct steps that most entrants get right quickly, in about a minute or two. Drafts aimed here have been coming out several kyu too hard, so aim lower than feels natural. No multi-case counting, no extremal or bounding argument, no search over possibilities, no algebra beyond one simple equation. It should still reward looking before calculating, such as a neat grouping, a small deduction or a short pattern, so it isn't bare arithmetic. """ + LOW_NOTE, 7: """CALIBRATING 7 KYU
This is the end of an AMC 8 paper or AMC 10 problems 1 to 10: two to four minutes. Drafts aimed here have been coming out too hard, so aim lower than feels natural. At most one choice for the solver to make, such as how to split a count, what to name, or working backwards, and it should be nearly forced. At most two short cases, and no extremal argument that needs a proof. Below AMC 10 middle in difficulty. """ + LOW_NOTE, 6: """CALIBRATING 6 KYU
Three to six minutes. One real idea, found by the first sensible attempt, then short routine work. Harder than an opener, easier than the last five problems of an AMC 10 paper. """ + LOW_NOTE, 5: """CALIBRATING 5 KYU
Drafts aimed at 5 kyu have been coming out about two kyu too hard, so aim lower than feels natural. One crux, found by the first sensible attempt, then routine work. A strong solver finishes in 6 to 12 minutes, and the solution fits in a short paragraph or two. Do not stack a second idea, and do not make the solver run an idea backwards through a further counting or divisibility step. If a candidate needs two non-routine steps, take one out, even if it is less impressive. For the combine recipe, the second technique must be the routine part."""}

IDEA_RULES = """How your work is checked. Every point here has rejected real drafts.
- Do not work out the answer by hand. A sandbox runs your program and its output becomes the key, so spend your thought on the idea and on making the statement exact. Keep your reasoning short.
- {key_rule}
- check_program computes the actual quantity from the problem's own definitions: enumerate, search or do exact symbolic work, using exact coordinates for geometry. A judge rejects a program that evaluates a closed formula from the solution, searches a smaller case and then applies a formula, or contains the answer. It must finish within 30 seconds and print only the key on its last line, {key_form}.
- check_program may import only: {imports}. Never use random, files or the network.
- A strict critic reads the statement for anything a competent solver could read two ways. Define every object, say whether integers are positive, whether pairs are ordered, whether a set may be empty, and whether points lie on sides or on lines. Avoid informal shorthand such as "uses the letters A, B and C"; state exactly what is meant.
- Seven models then solve it blind from the statement alone. Do not rely on a figure: describe every point and condition in words.
- A judge compares it with the source problem and other published problems. It rejects any problem with the same structure and solution path, whatever the setting or numbers, and any well-known problem. A solver who knows the source must still have to think of something new.
- All text uses UK spelling. Use $...$ and $$...$$ for maths, with no custom macros."""

WRITE_RULES = """How your work is checked.
- A strict auditor reads the solution. Justify every non-routine step and every case. Routine algebra may be skipped. It must state the key in its last paragraph.
- The key comes from a program, so a solution that reaches any other number is wrong. Work it out honestly. If you find the key or the statement is wrong, reply with only <disagree>one sentence on what is wrong</disagree> instead of bending the argument.
- No hint may state the key. Each hint adds something, and the last stops one routine step short.
- All text uses UK spelling. Use $...$ and $$...$$ for maths: \\dfrac in display maths and \\frac inline, always with braces, \\cdot for products and never *, \\le and \\ge. Use only <b> and <code> as markup, and write cases as prose, never as a list.
- Never argue from a picture, and never refer to a figure or diagram, unless the problem is geometry."""

SOLUTION_STYLE = """THE STYLE OF THE SOLUTION
Write as a strong olympiad student writes up a solution: direct and concise, with no narration, no restating the problem and no signposting. Never use these or anything like them: "we only need", "note that", "it remains", "therefore each", "key idea", "key insight", "crux", "elegant", "beautiful", "the trick", "the heart of", "delicate", "why this works". No em dashes. Do not end with a summary or a comment on the idea. Use the labels Lemma, Claim, Remark or Theorem only where they actually help, usually at 3 kyu and on proofs. Rigour stays: every non-routine step and every case is justified, only shorter. State the final answer.

An example of the right voice, for an easy problem about four-digit palindromes with digit sum 14: "Write the number as $abba$. Then $2(a+b)=14$, so $a+b=7$ with $1\\le a\\le 7$, giving $7$ palindromes." """

LENGTHS = {8: "1 to 4 lines, often one sentence plus the arithmetic", 7: "1 to 4 lines, often one sentence plus the arithmetic", 6: "at most about 80 words",
           5: "at most about 150 words", 4: "at most about 150 words", 3: "as long as rigour needs and no longer", 2: "as long as rigour needs and no longer", 1: "as long as rigour needs and no longer"}


def length_guide(kyu):
    return f"LENGTH\nThis is {kyu} kyu, so: {LENGTHS[kyu]}. Length follows difficulty. An easy problem has a short solution, and not every problem needs a long paragraph."


FIGURE_RULES = r"""THE FIGURE
Every solution to a geometry problem needs a figure, and so does any other solution that argues from a picture, such as complex numbers as points or a coordinate argument. It must look like a careful figure in an olympiad book. Write real tkz-euclide in exactly this shape, and adapt only the content:

%! alt One or two sentences saying what the figure shows, for a reader who can't see it. Name points and lengths.
%! after_paragraph 2
%! scale 1/27
\input{preamble}
\begin{document}
\begin{tikzpicture}
%! let R = 195/2
\tkzDefPoint(0,0){O} %! O = (0, 0)
\tkzDefPoint(0,0){A} %! A = polar(O, R, 90)
\tkzDefPoint(0,0){M} %! M = mid(X, Y)
%! fact on_circle(A, O, R)
%! fact dist(X, P) == 64
%! example dist(C, A) == 144
\tkzFillPolygon[color=figtint](B,P,Q,C)
\tkzDrawCircle(O,A)
\tkzDrawSegment[aux](O,A)
\tkzDrawPolygon(A,B,C)
\tkzDrawSegment[key](X,Y)
\tkzMarkRightAngle[size=.2,mk](A,M,Y)
\tkzMarkSegments[mark=|,size=2.5pt,mk](A,B B,E)
\tkzMarkAngle[size=.8,arc=l,mark=none,mk](B,A,C)
\tkzDrawPoints(O,A,B,C)
\tkzLabelPoint[above,lbl](A){$A$}
\tkzLabelSegment[below,pos=.5,len](X,P){$64$}
\tkzLabelAngle[pos=1.3](B,A,C){$40^\circ$}
\end{tikzpicture}
\end{document}

Rules. Each one is enforced by a program that rejects the draft.
- Every point is one \tkzDefPoint(0,0){P} line with its exact value after %! P = on the same line. Leave the (0,0): a program fills in the decimals. Never compute a decimal yourself. Don't use any other tkz command that defines or computes a point (\tkzDefMidPoint, \tkzInterLL, \tkzDrawCircle[circum] and so on), \usepackage, \def, \foreach or \input of anything else.
- Exact values may use numbers, + - * / **, sqrt, sin, cos, tan, asin, acos, atan, atan2, sind, cosd, tand, pi, abs, dist(A,B), angle(A,B,C) in degrees, area(A,B,...), x(P), y(P), inradius(A,B,C), circumradius(A,B,C), and these for points: (a, b), mid(A,B), lerp(A,B,t), foot(P,A,B), reflect(P,A,B), rotate(P,O,degrees), polar(O,r,degrees), meet(A,B,C,D), circumcentre(A,B,C), incentre(A,B,C), shift(P,dx,dy). Use the problem's own lengths as coordinates. If the problem has a family of cases, draw one good case.
- Each %! fact is checked to 1e-9: collinear(P,A,B), on_segment(P,A,B), on_circle(P,O,r), concyclic(A,B,C,D,...), perp(A,B,C,D), parallel(A,B,C,D), tangent(O,r,A,B), tangent_circles(O1,r1,O2,r2), midpoint(M,A,B), equal(a,b), or a comparison such as dist(A,B) == 5 or angle(A,B,C) >= 120. State every length, tangency and concyclicity the solution relies on. A number after == must appear in the statement or solution. If it is true only of the case you drew, write %! example instead of %! fact.
- %! scale turns the problem's units into centimetres. Make the drawing about 7.5 cm across. It must fit in 9.5 cm by 10.5 cm with its labels.
- Colours: draw only with the preamble's styles aux (dashed construction lines), key (the one object the argument turns on), mk (marks), lbl (point labels) and len (lengths), and the fills figtint and figaccenttint. Mark equal lengths, right angles and tangency where they help the reader.
- No label may touch another label, a line or a point. Choose each label's side so it sits in empty space.
- after_paragraph is how many solution paragraphs come above the figure."""


def _section(text, start, end):
    i = text.index(start)
    return text[i:text.index(end, i + 1)]


def _standard():
    return STANDARD.read_text(encoding="utf-8")


def idea_rules(kyu):
    """The standard's own words, so a change there reaches the generator with no edit here."""
    text = _standard()
    lines = _section(text, "### 1.4 The ladder", "### 1.5 Examples").splitlines()
    ladder = next(x for x in lines if x.startswith(f"| {kyu} |"))
    header = next(x for x in lines if x.startswith("| Kyu | Belt |"))
    return "\n\n".join([_section(text, "### 1.3 Definitions", "### 1.4 The ladder"), f"The target rung:\n{header}\n{ladder}",
                        _section(text, "## 2. Statement rules", "## 4. Solution rules"), _section(text, "## 6. What makes a problem bad", "## 8. Proof problems")])


def write_rules():
    return _section(_standard(), "## 4. Solution rules", "## 6. What makes a problem bad")


def taxonomy_ids():
    t = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    return ", ".join(x["id"] for x in t["techniques"] + t["configurations"] if x.get("status") != "legacy")


def describe_record(record):
    paths = "\n".join(f"- {p.get('name')} ({p.get('difficulty_of_path')}): {'; '.join(p.get('key_steps') or [])}" for p in (record.get("solution_paths") or []) + (record.get("solution_paths_second_pass") or []))
    return (f"Core idea: {record.get('core_idea')}\nCrux: {record.get('crux')}\nTechniques: {', '.join(record.get('techniques') or [])}\n"
            f"Solution routes:\n{paths}\nTraps: {'; '.join(record.get('traps') or [])}\nNote on using it: {record.get('generation_note') or 'none'}")


def _topic_rules(topic):
    """The bank needs every topic at every kyu, and left alone the model drifts into number theory."""
    rule = f"THE TOPIC\nEvery candidate must be {TOPICS[topic]}, whatever the recipe says: the main work of solving it must belong to that topic. Set <topic> to {topic}."
    if topic != "G":
        rule += " Any model you use must not be geometric, and the solution must never argue from a picture."
    return [rule]


def _key_rules(kyu):
    if kyu >= 6:
        return dict(key_rule="The key must be an integer of absolute value below $10^9$, or a fraction with at most three digits above and below, and must not be 0 or 1 or appear as a number in the statement. If it is a fraction the statement must end: Give your answer as a fraction in lowest terms. Prefer an integer. There is no encoding: ask for the quantity itself.",
                    key_form="as a plain integer or as a/b in lowest terms")
    return dict(key_rule="The key must be an integer from 2 to 999 and must not appear as a number in the statement. Choose the statement's parameters, or ask for a remainder modulo $1000$ or an encoding such as $m + n$ (rule A4), so that this holds. Do not make the encoding the hard part.",
                key_form="as a plain integer")


def _idea_context(inp, kyu, digest):
    parts = [
        f"Write for {kyu} kyu, in the style and at the level of {ANCHORS[kyu]}. Its difficulty must come from an idea, not from arithmetic.",
        LOW_STYLE if kyu >= 6 else STYLE,
        *_topic_rules(inp.record["topic"]),
        *([CALIBRATION[kyu]] if kyu in CALIBRATION else []),
        f"THE KYUCLID STANDARD\n{idea_rules(kyu)}",
        IDEA_RULES.format(imports=", ".join(sorted(ALLOWED_IMPORTS)), **_key_rules(kyu)),
        f"THE IDEA TO TEACH\n{describe_record(inp.record)}",
        ("THE SOURCE PROBLEM, for calibration only. It shows how hard the target is. Do not reuse its setting, objects, numbers or phrasing, "
         f"and never mention it.\n<<<\n{inp.statement}\n>>>"),
    ]
    if digest:
        parts.append(f"WHAT THE HUMAN REVIEWER HAS BEEN REJECTING\n{digest}")
    return parts


def ideas(inp, kyu, recipes, partner=None, digest=""):
    lines = [f"- {name}: {RECIPES[name]}" for name in recipes]
    if "combine" in recipes and partner:
        lines.append(f"The second technique for combine: {partner}. It rarely appears with this idea at this kyu.")
    if "change-route" in recipes:
        lines.append("For change-route, use a route other than the first one listed above.")
    n = len(recipes)
    return "\n\n".join(_idea_context(inp, kyu, digest) + [
        f"YOUR TASK\nWrite {n} candidates, one for each recipe below. A pure number swap, or the same story with renamed objects, is never acceptable.\n" + "\n".join(lines),
        "OUTPUT\n" + IDEA_FORMAT.format(recipes=" or ".join(recipes)) + f"\nRepeat that block {n} times, with nothing else around it.",
    ])


def idea_repair(inp, kyu, previous, failure, digest=""):
    shown = "\n".join(f"<{k}>{previous[k]}</{k}>" for k in ("title", "statement", "sketch", "check_program"))
    return "\n\n".join(_idea_context(inp, kyu, digest) + [
        f"YOUR EARLIER CANDIDATE, using the recipe {previous['recipe']}\n{shown}",
        (f"WHY IT WAS REJECTED\n{failure}\n\nFix the cause, not the symptom. If the statement and program disagree, correct whichever is wrong. "
         "If it was too close to another problem, change what the solver has to do: changing the setting or the numbers will fail again."),
        "OUTPUT\n" + IDEA_FORMAT.format(recipes=previous["recipe"]) + "\nWrite that block once, with nothing else around it.",
    ])


def write_up(idea, kyu, key, record, earlier=None, failure=None):
    """Has no contest text in it: the source isn't needed here, so it can't be copied here."""
    parts = [
        f"A {kyu} kyu problem has been chosen. Write its hints and solution.",
        f"THE KYUCLID STANDARD\n{write_rules()}",
        WRITE_RULES,
        SOLUTION_STYLE,
        length_guide(kyu),
        FIGURE_RULES,
        f"TAXONOMY IDS, the only tags allowed\n{taxonomy_ids()}",
        f"THE PROBLEM\n{idea['statement']}\n\nTHE KEY, computed by a program: {key}\n\nTHE PROGRAM\n{idea['check_program']}\n\nTHE AUTHOR'S SKETCH\n{idea.get('sketch', '')}",
    ]
    if earlier and failure:
        parts.append(f"YOUR EARLIER WRITE-UP\n{earlier}\n\nWHY IT WAS REJECTED\n{failure}\n\nFix the cause. Send every part again, including the whole figure.")
    parts.append("OUTPUT\n" + WRITE_FORMAT + "\nNothing else around it.")
    return "\n\n".join(parts)


def _tag(block, name):
    m = re.search(rf"<{name}>(.*?)</{name}>", block, re.S)
    return m.group(1).strip() if m else ""


def parse_ideas(text):
    """Returns the candidates that have every required part. A truncated last block is simply dropped."""
    out = []
    for block in re.findall(r"<candidate>(.*?)</candidate>", text, re.S):
        c = {k: _tag(block, k) for k in ("title", "recipe", "topic", "statement", "sketch", "check_program", "interest_reason")}
        c["check_program"] = re.sub(r"^```\w*\n|\n?```$", "", c["check_program"])
        m = re.search(r"\d+(\.\d+)?", _tag(block, "interest"))
        c["interest"] = float(m.group()) if m else 0.0
        if all(c[k] for k in ("title", "statement", "check_program")):
            out.append(c)
    return out


def parse_write_up(text):
    """Returns the write-up's fields, or a dict with only disagree, or None if it's incomplete."""
    disagree = _tag(text, "disagree")
    if disagree:
        return dict(disagree=disagree)
    w = dict(subtopics=[s.strip() for s in _tag(text, "subtopics").split(",") if s.strip()], solution=_tag(text, "solution"),
             hints=[h.strip() for h in re.findall(r"<hint>(.*?)</hint>", text, re.S) if h.strip()],
             figures=[f.strip() + "\n" for f in re.findall(r"<figure>(.*?)</figure>", text, re.S) if f.strip()], no_figure=_tag(text, "no_figure"))
    return w if w["solution"] and w["hints"] and w["subtopics"] else None
