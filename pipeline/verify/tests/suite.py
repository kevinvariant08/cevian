"""The test drafts and the verdict each should get. All are invented, or reskin famous public puzzles; none comes from the corpus.

    python -m pipeline.verify.tests.suite     writes tests/drafts/*.json and tests/expected.json

An expected entry is {verdict: [allowed first words], checks: [allowed checks]}. `sim` tells the scripted
backend how models would behave; the live run ignores it.
"""
import json
from pathlib import Path

from ..answers import answer_hash

HERE = Path(__file__).resolve().parent
ALL = {}
# id: (taxonomy slug, a note on why it fits). A variant uses its base's entry.
WHY = {
    "ok-digit-product": ("place-value-representation", "the tens digit is at most nine, which limits the units digit."),
    "ok-seat-row": ("rule-of-product", "converting both positions to one numbering makes the gap a direct count."),
    "ok-three-remainders": ("crt", "conditions with coprime moduli combine into one residue class."),
    "ok-digit-sum-eight": ("casework", "after the shift, the number of largest digits splits the count into simple cases."),
    "ok-rectangle-point": ("pythagorean-theorem", "the right angles at the corners give each squared length directly."),
    "ok-odd-divisors-even-digits": ("divisor-pairing", "divisors pair up except at a square root, which leaves only squares."),
    "ok-seven-divides": ("modular-arithmetic", "the condition depends only on a residue, so a short table settles it."),
    "ok-grid-blue-red": ("complementary-counting", "the bad colourings are easier to count than the good ones."),
    "ok-shifted-divisor": ("divisor-counting", "reducing modulo the divisor leaves a constant, whose divisors can be counted."),
    "ok-letter-strings": ("recursion", "tracking the last letter gives a linear recurrence for each count."),
    "standard-answer-range": ("arithmetic-series-sum", "factoring out the common multiple leaves a standard series."),
    "ambiguous-marbles": ("favorable-over-total", "the probability is a ratio of two pair counts."),
    "ambiguous-between": ("divisibility-rules", "writing each multiple as four times a number makes the count direct."),
    "ambiguous-grid-squares": ("casework", "sorting the squares by side length splits the count into simple cases."),
    "too-easy-sum": ("place-value-representation", "tens and units add separately."),
    "too-easy-divisors": ("divisor-pairing", "each divisor pairs with its partner, so few checks are needed."),
    "too-easy-difference": ("difference-of-squares", "the two squares can be subtracted directly or through the factorisation."),
    "reskin-lockers": ("divisor-pairing", "a switch flips once per divisor, and only squares have an odd number."),
    "reskin-hanoi": ("recursion", "the moment the largest crate moves gives a recurrence."),
    "reskin-gauss": ("arithmetic-series-sum", "pairing first with last makes every pair total the same."),
    "reskin-snail": ("bounding", "the daily peak bounds the first day the mark can be reached."),
    "proof-ok": ("polynomial-factoring", "the factorisation shows three consecutive integers."),
    "proof-flawed": ("polynomial-factoring", "the factorisation shows three consecutive integers."),
    "mis-rated-hard": ("recursion", "a scan with a short memory turns the count into a transfer between states."),
}


def draft(pid, kyu, topic, statement, answer, program, solution, hints, fmt=None, expect=("PASS",), checks=None, sim=None, **extra):
    fmt = fmt or ("integer_0_999" if str(answer).isdigit() and int(answer) <= 999 else "integer")
    d = dict(id=pid, title=pid.replace("-", " ").capitalize(), kyu=kyu, topic=topic, subtopics=["casework"], type="answer", status="draft",
             statement=statement, answer_format=fmt, answer_hash=answer_hash(pid, answer), hints=hints, solution=solution,
             provenance=dict(kind="original", author="task-05-tests"), stats=dict(solves=0, attempts=0, liked=0), answer=str(answer), check_program=program)
    d.update(extra)
    ALL[pid] = dict(draft=d, expected=dict(verdict=list(expect), checks=checks), sim=sim or {})
    return d


def variant(base, pid, expect, checks=None, sim=None, remove=(), rehash=True, **changes):
    """A copy of a correct draft with one thing broken."""
    d = {**ALL[base]["draft"], "id": pid, "title": pid.replace("-", " ").capitalize(), **changes}
    for k in remove:
        d.pop(k)
    if rehash and "answer" in d and "answer_hash" not in changes and "answer_hash" not in remove:
        d["answer_hash"] = answer_hash(pid, d["answer"])
    ALL[pid] = dict(draft=d, expected=dict(verdict=list(expect), checks=checks), sim=sim or {}, base=base)


# ---- Correct problems. These should pass, whichever backend runs them.
draft("ok-digit-product", 8, "N", "How many two-digit positive integers have a tens digit equal to three times the units digit, where the units digit is not zero?", 3,
      "print(sum(1 for n in range(10, 100) if n % 10 != 0 and n // 10 == 3 * (n % 10)))",
      "Let the units digit be $u$, with $u \\ge 1$. The tens digit is $3u$, which must be at most $9$, so $u \\in \\{1, 2, 3\\}$. This gives $31$, $62$ and $93$, so there are $3$ such numbers.",
      ["Name the units digit, since the tens digit depends on it.", "Use the place value of each digit to list the options: the tens digit is at most $9$, which limits the units digit."])
draft("ok-seat-row", 8, "A", "A row has $20$ seats numbered $1$ to $20$ from the left. Ann sits in the seventh seat from the left and Ben sits in the fifth seat from the right. How many seats lie strictly between them?", 8,
      "seats = list(range(1, 21))\nann = seats[6]\nben = seats[-5]\nprint(sum(1 for s in seats if min(ann, ben) < s < max(ann, ben)))",
      "Ann is in seat $7$. The fifth seat from the right is seat $20 - 4 = 16$, so Ben is in seat $16$. The seats strictly between them are $8, 9, \\dots, 15$, and there are $8$ of them.",
      ["What seat number does each person have?", "Convert counting from the right into counting from the left: the first seat from the right is seat $20$."])
draft("ok-three-remainders", 7, "N", "Find the smallest positive integer that leaves remainder $2$ when divided by $5$, leaves remainder $3$ when divided by $7$, and is a multiple of $4$.", 52,
      "print(next(n for n in range(1, 10000) if n % 5 == 2 and n % 7 == 3 and n % 4 == 0))",
      "The numbers leaving remainder $3$ on division by $7$ and remainder $2$ on division by $5$ start at $17$ and repeat every $35$, since $17 = 2\\cdot 7 + 3 = 3\\cdot 5 + 2$ and $\\gcd(5,7)=1$. So the candidates are $17, 52, 87, \\dots$. The number $17$ is odd and $52 = 4\\cdot 13$, so the smallest is $52$.",
      ["Which numbers meet the conditions for $5$ and $7$?", "By the Chinese remainder theorem those numbers repeat every $35$, so test them in turn against the last condition."])
draft("ok-digit-sum-eight", 7, "C", "How many four-digit numbers use only the digits $1$, $2$ and $3$ (repeats allowed) and have digit sum $8$?", 19,
      "from itertools import product\nprint(sum(1 for t in product([1, 2, 3], repeat=4) if sum(t) == 8))",
      "Subtract $1$ from each digit: we want four values from $\\{0,1,2\\}$ with sum $4$. Sort by the number of $2$s. Two $2$s and two $0$s: $\\binom42 = 6$ ways. One $2$, two $1$s and one $0$: $4\\cdot 3 = 12$ ways. No $2$s: four $1$s, $1$ way. Three or more $2$s would exceed the sum. The total is $6 + 12 + 1 = 19$.",
      ["What happens to the sum if every digit is lowered by one?", "Use casework on how many of the lowered digits equal $2$."])
draft("ok-rectangle-point", 6, "G", "Rectangle $ABCD$ has $AB = 12$ and $BC = 5$, with vertices in that order. Point $P$ lies on side $AB$ with $AP = 4$. Find $PC^2 + PD^2$.", 130,
      "from sympy import Point\nA, B = Point(0, 0), Point(12, 0)\nC, D = Point(12, 5), Point(0, 5)\nP = Point(4, 0)\nprint(P.distance(C)**2 + P.distance(D)**2)",
      "Put $A = (0,0)$, $B = (12,0)$, $C = (12,5)$, $D = (0,5)$, so $P = (4,0)$. Then $PC^2 = 8^2 + 5^2 = 89$ and $PD^2 = 4^2 + 5^2 = 41$, by Pythagoras in the right-angled triangles $PBC$ and $PAD$. The sum is $89 + 41 = 130$.",
      ["Look at the triangles with $P$ as a vertex and a right angle at $A$ or $B$.", "Use Pythagoras in triangles $PAD$ and $PBC$ to find each squared length."])
draft("ok-odd-divisors-even-digits", 6, "N", "How many positive integers at most $300$ have an odd number of positive divisors and an even digit sum?", 5,
      "from sympy import divisor_count\nprint(sum(1 for n in range(1, 301) if divisor_count(n) % 2 == 1 and sum(map(int, str(n))) % 2 == 0))",
      "A positive integer has an odd number of divisors exactly when it is a perfect square, because divisors pair up as $d, n/d$ except when $d^2 = n$. The squares up to $300$ are $1^2, \\dots, 17^2$. Their digit sums are $1,4,9,7,7,9,13,10,9,1,4,9,16,16,9,13,19$. The even ones belong to $4, 64, 121, 169, 196$, which gives $5$ numbers.",
      ["When do the divisors of a number fail to pair up?", "Pairing $d$ with $n/d$ shows only perfect squares qualify, so list the squares up to $300$ and check their digit sums."])
draft("ok-seven-divides", 6, "N", "How many integers $n$ with $1 \\le n \\le 100$ are such that $n^2 + n + 1$ is divisible by $7$?", 29,
      "print(sum(1 for n in range(1, 101) if (n*n + n + 1) % 7 == 0))",
      "Divisibility by $7$ depends only on $n$ modulo $7$. Testing $n \\equiv 0, 1, \\dots, 6$ gives $n^2 + n + 1 \\equiv 1, 3, 0, 6, 0, 3, 1$, so we need $n \\equiv 2$ or $4 \\pmod 7$. Among $1, \\dots, 98$ there are $14$ numbers in each class, giving $28$. Of the last two, $99 \\equiv 1$ fails and $100 \\equiv 2$ works. The total is $29$.",
      ["Does the value of the expression depend on all of $n$, or only on part of it?", "Use modular arithmetic: test the seven remainders, then count how often the good ones occur up to $100$."])
draft("ok-grid-blue-red", 5, "C", "Each cell of a $3 \\times 3$ grid is coloured red or blue. In how many colourings does every row contain at least one blue cell and every column contain at least one red cell?", 174,
      "from itertools import product\nc = 0\nfor g in product([0, 1], repeat=9):\n    rows = [g[0:3], g[3:6], g[6:9]]\n    if all(1 in r for r in rows) and all(any(r[i] == 0 for r in rows) for i in range(3)):\n        c += 1\nprint(c)",
      "A column that is all blue already gives every row a blue cell. So the colourings with no all-red row number $(2^3 - 1)^3 = 343$, and we must remove those with some all-blue column. Colourings with no all-blue column also number $343$ by symmetry, so $512 - 343 = 169$ colourings have an all-blue column, and every one of them has no all-red row. The answer is $343 - 169 = 174$.", ["What does an all-blue column do to the rows?", "Use complementary counting: start from colourings with no all-red row and remove those with an all-blue column."])
draft("ok-shifted-divisor", 5, "N", "How many positive integers $n$ are such that $n + 30$ divides $n^2 + 300$?", 15,
      "from sympy import divisors\n# n + 30 divides n^2 + 300 forces n + 30 to be at most about n^2 + 300, so test n directly up to a generous bound\nprint(sum(1 for n in range(1, 5000) if (n*n + 300) % (n + 30) == 0))",
      "Since $n \\equiv -30 \\pmod{n+30}$, we have $n^2 + 300 \\equiv 900 + 300 = 1200 \\pmod{n+30}$. So the condition is that $n + 30$ divides $1200$, with $n + 30 > 30$. The number $1200 = 2^4\\cdot 3\\cdot 5^2$ has $5\\cdot 2\\cdot 3 = 30$ divisors. They pair up as $d \\cdot (1200/d)$. Those at most $30$ are $1,2,3,4,5,6,8,10,12,15,16,20,24,25,30$, which is $15$ divisors, leaving $15$ above $30$. So there are $15$ values of $n$.",
      ["Compare $n$ with $n + 30$: what is $n^2 + 300$ close to?", "Reduce modulo $n + 30$: the remainder is a constant, so $n + 30$ must be one of its divisors above $30$."])
draft("ok-letter-strings", 4, "C", "Each character of a string of length $12$ is one of the letters $A$, $B$ and $C$, and not every letter need appear. No $A$ is immediately followed by a $B$, and the first and last letters are different. Find the number of such strings, modulo $1000$.", 790,
      "from itertools import product\nallowed = [(a, b) for a in 'ABC' for b in 'ABC' if not (a == 'A' and b == 'B')]\nt = 0\nfor first in 'ABC':\n    cur = {c: (1 if c == first else 0) for c in 'ABC'}\n    for _ in range(11):\n        cur = {b: sum(cur[a] for a, bb in allowed if bb == b) for b in 'ABC'}\n    t += sum(v for c, v in cur.items() if c != first)\nprint(t % 1000)",
      "Let $M$ be the $3\\times 3$ matrix of allowed letter pairs, with rows and columns in the order $A, B, C$: every entry is $1$ except the $(A,B)$ entry. Strings of length $n$ correspond to walks of $n-1$ steps. Let $T_n$ be the number of strings of length $n$. Appending any letter gives $3T_{n-1}$ strings, and we remove those ending in $AB$, of which there are $T_{n-2}$, so $T_n = 3T_{n-1} - T_{n-2}$ with $T_1 = 3$, $T_2 = 8$. This gives $T_{12} = 121393$. Strings with equal first and last letters number $\\operatorname{tr} M^{11}$. The matrix $M$ has trace $3$, determinant $0$ and characteristic polynomial $x(x^2 - 3x + 1)$, so $t_n = \\operatorname{tr} M^n$ satisfies $t_n = 3t_{n-1} - t_{n-2}$ with $t_1 = 3$, $t_2 = 7$, which gives $t_{11} = 39603$. The count is $121393 - 39603 = 81790$, which is $790$ modulo $1000$.", ["Look at what the last letter of a string allows next.", "Use a transfer matrix on the letters: total strings come from a recurrence, and equal first and last letters from its trace."])

# ---- Wrong answer keys. The program disagrees, so no model is needed.
variant("ok-digit-product", "bad-key-digit-product", ["FAIL"], ["computational"], answer="5")
variant("ok-seven-divides", "bad-key-off-by-one", ["FAIL"], ["computational"], answer="28")
variant("ok-three-remainders", "bad-key-three-remainders", ["FAIL"], ["computational"], answer="17")

# ---- A wrong key that a matching bug in the program hides. Only blind solves and the critics can catch this.
variant("ok-seven-divides", "bad-key-buggy-program", ["FAIL", "INVESTIGATE"], ["program_judge", "blind_solves", "solution_audit"],
        sim=dict(solves=["29"] * 7, audit={"reaches_answer": True, "issues": [{"severity": "material", "issue": "misses n = 100"}]}),
        answer="28", check_program="print(sum(1 for n in range(1, 100) if (n*n + n + 1) % 7 == 0))",
        solution="Divisibility by $7$ depends only on $n$ modulo $7$. Testing the residues shows we need $n \\equiv 2$ or $4 \\pmod 7$. Among $1, \\dots, 98$ there are $14$ numbers in each class, giving $28$, and $99$ and $100$ both fail. The total is $28$.")
variant("ok-digit-sum-eight", "bad-key-buggy-count", ["FAIL", "INVESTIGATE"], ["program_judge", "blind_solves", "solution_audit"],
        sim=dict(solves=["19"] * 7, audit={"reaches_answer": True, "issues": [{"severity": "material", "issue": "misses the case with no 2s"}]}),
        answer="18", check_program="from itertools import product\nprint(sum(1 for t in product([1, 2, 3], repeat=4) if sum(t) == 8 and t != (2, 2, 2, 2)))",
        solution="Subtract $1$ from each digit: we want four values from $\\{0,1,2\\}$ with sum $4$. Two $2$s and two $0$s: $\\binom42 = 6$ ways. One $2$, two $1$s and one $0$: $4\\cdot 3 = 12$ ways. The total is $6 + 12 = 18$.")

# ---- Check programs that don't really check.
variant("ok-seven-divides", "hard-coded-literal", ["FAIL"], ["computational"], check_program="print(29)")
variant("ok-seven-divides", "hard-coded-variable", ["FAIL"], ["computational"], check_program="ans = 29\nprint(ans)")
variant("ok-seven-divides", "hard-coded-decoy-loop", ["FAIL"], ["computational"], check_program="t = 0\nfor n in range(1, 101):\n    t += n\nprint(29)")
variant("ok-seven-divides", "hard-coded-smuggled", ["FAIL"], ["program_judge"], sim=dict(program={"verdict": "hardcoded", "reason": "the loop is unused and the answer is a constant"}),
        check_program="checked = [n for n in range(1, 101)]\nans = 29\nprint(ans)")
variant("ok-shifted-divisor", "restates-the-formula", ["FAIL"], ["program_judge"], sim=dict(program={"verdict": "restates", "reason": "it only repeats the solution's divisor count"}),
        check_program="from sympy import divisor_count\nprint(divisor_count(1200) // 2)")

# ---- Programs the sandbox must stop.
variant("ok-digit-product", "sandbox-network", ["FAIL"], ["computational"], check_program="import socket\ns = socket.create_connection(('example.com', 80))\nprint(4)")
variant("ok-digit-product", "sandbox-import-os", ["FAIL"], ["computational"], check_program="import os\nprint(len(os.listdir('.')))")
variant("ok-digit-product", "sandbox-file-write", ["FAIL"], ["computational"], check_program="import sys\nf = sys.modules['io'].FileIO('leak.txt', 'w')\nprint(sum(1 for n in range(10, 100) if n % 10 != 0 and n // 10 == 3 * (n % 10)))")
variant("ok-digit-product", "sandbox-timeout", ["FAIL"], ["computational"], check_program="n = 0\nwhile True:\n    n += 1\nprint(n)")
variant("ok-digit-product", "program-crashes", ["FAIL"], ["computational"], check_program="print(sum(1 / (n - 50) for n in range(10, 100)))")

# ---- Schema, hash and LaTeX.
variant("ok-digit-product", "schema-missing-solution", ["FAIL"], ["schema"], remove=["solution"])
variant("ok-digit-product", "schema-bad-kyu", ["FAIL"], ["schema"], kyu=9)
variant("ok-digit-product", "schema-unknown-field", ["FAIL"], ["schema"], difficulty_score=3)
variant("ok-digit-product", "schema-hash-mismatch", ["FAIL"], ["schema"], answer_hash="00000000")
variant("ok-digit-product", "latex-undefined-macro", ["FAIL"], ["schema"], statement="How many two-digit positive integers have digits whose product is $\\twelve$?")
variant("ok-digit-product", "latex-unclosed-dollar", ["FAIL"], ["schema"], statement="How many two-digit positive integers have a tens digit equal to $9 times the units digit?")

# ---- Standard rules.
variant("ok-grid-blue-red", "standard-us-spelling", ["FAIL"], ["standard"], statement="Each cell of a $3 \\times 3$ grid is colored red or blue. In how many colorings does every row contain at least one blue cell and every column contain at least one red cell?")
variant("ok-seven-divides", "standard-one-hint", ["FAIL"], ["standard"], hints=["Test the seven remainders."])
variant("ok-seven-divides", "standard-hint-gives-answer", ["FAIL"], ["standard"], hints=["Work modulo $7$.", "The count comes to $29$."])
variant("ok-digit-product", "standard-names-a-contest", ["FAIL"], ["standard"], statement="In the style of the AIME: how many two-digit positive integers have a tens digit equal to three times the units digit?")
draft("standard-answer-range", 4, "N", "Find the sum of the first $100$ positive multiples of $3$.", 15150,
      "print(sum(3 * k for k in range(1, 101)))", "The sum is $3(1 + 2 + \\dots + 100) = 3 \\cdot 5050 = 15150$.",
      ["Factor out the common multiplier.", "Then use the sum of the first $100$ integers."], expect=["FAIL"], checks=["standard"])

# ---- Ambiguous statements.
draft("ambiguous-marbles", 7, "C", "A bag holds $3$ red and $5$ blue marbles. Two marbles are drawn. What is the probability that they are the same colour? Give your answer as a fraction in lowest terms.", "13/28",
      "from fractions import Fraction\nfrom itertools import combinations\nb = 'RRRBBBBB'\np = list(combinations(range(8), 2))\nprint(Fraction(sum(1 for i, j in p if b[i] == b[j]), len(p)))",
      "There are $\\binom82 = 28$ pairs of marbles, of which $\\binom32 + \\binom52 = 3 + 10 = 13$ are the same colour, so the probability is $\\tfrac{13}{28}$.",
      ["Count pairs of marbles.", "Add the all-red and the all-blue pairs."], fmt="rational", expect=["FAIL", "INVESTIGATE"], checks=["well_posedness", "blind_solves"],
      sim=dict(wellposed=[{"severity": "material", "issue": "with or without replacement is not stated"}]))
draft("ambiguous-between", 8, "N", "How many multiples of $4$ are there between $12$ and $48$?", 10,
      "print(sum(1 for n in range(12, 49) if n % 4 == 0))", "The multiples are $12, 16, \\dots, 48$, that is $4\\cdot 3$ to $4 \\cdot 12$, and the multiplier runs from $3$ to $12$, so there are $10$.",
      ["List them from the smallest.", "Write each as $4$ times something."], expect=["FAIL", "INVESTIGATE"], checks=["program_judge", "well_posedness", "blind_solves", "solution_audit"],
      sim=dict(wellposed=[{"severity": "material", "issue": "between could include or exclude the endpoints"}]))
draft("ambiguous-grid-squares", 7, "C", "How many squares are there on a $4 \\times 4$ grid?", 30,
      "c = 0\nfor s in range(1, 5):\n    for x in range(5 - s):\n        for y in range(5 - s):\n            c += 1\nprint(c)", "A square of side $s$ can be placed in $(5-s)^2$ ways, so the total is $16 + 9 + 4 + 1 = 30$.",
      ["Sort the squares by side length.", "A square of side $s$ has $5 - s$ positions in each direction."], expect=["FAIL", "INVESTIGATE"], checks=["well_posedness", "blind_solves", "program_judge"],
      sim=dict(wellposed=[{"severity": "material", "issue": "grid could mean 4 by 4 cells or 4 by 4 points"}]))

# ---- Too easy for the kyu.
draft("too-easy-sum", 4, "A", "Find $17 + 26$.", 43, "t = 0\nfor _ in range(17):\n    t += 1\nfor _ in range(26):\n    t += 1\nprint(t)", "Adding gives $17 + 26 = 43$.",
      ["Add the tens first.", "Then add the units."], expect=["FAIL", "INVESTIGATE"], checks=["blind_solves", "originality", "solution_audit", "well_posedness"], sim=dict(solve_tokens=40))
draft("too-easy-divisors", 3, "N", "What is the total number of factors of $12$, including $1$ and $12$ themselves?", 6, "print(sum(1 for d in range(1, 13) if 12 % d == 0))", "The divisors are $1, 2, 3, 4, 6, 12$, so there are $6$.",
      ["Which small numbers go into $12$?", "Use divisor pairing: each divisor $d$ goes with $12/d$."], expect=["FAIL", "INVESTIGATE"], checks=["blind_solves", "originality", "solution_audit", "well_posedness"], sim=dict(solve_tokens=40))
draft("too-easy-difference", 5, "A", "Find $7^2 - 3^2$.", 40, "print(sum(1 for a in range(7*7) for b in [a] if b >= 3*3))", "We have $49 - 9 = 40$.",
      ["Work out each square.", "Then subtract."], expect=["FAIL", "INVESTIGATE"], checks=["blind_solves", "program_judge", "originality", "solution_audit", "well_posedness"], sim=dict(solve_tokens=40))

# ---- Reskins of famous public puzzles. None of these sources is in the corpus.
RESKIN = dict(originality={"neighbours": [], "known": {"is_known": True, "name": "a famous puzzle", "reason": "same structure, new setting"}})
draft("reskin-lockers", 6, "N", "A hotel corridor has $400$ lamps, all off, numbered $1$ to $400$. On day $k$, for $k = 1, 2, \\dots, 400$, a caretaker flips the switch of every lamp whose number is a multiple of $k$. How many lamps are on after day $400$?", 20,
      "print(sum(1 for lamp in range(1, 401) if sum(1 for k in range(1, 401) if lamp % k == 0) % 2 == 1))",
      "A lamp is flipped once for each divisor of its number, so it ends on exactly when it has an odd number of divisors, that is, when its number is a perfect square. There are $20$ squares up to $400$.",
      ["How many times is lamp $n$ flipped?", "Use divisor pairing to find which numbers have an odd number of divisors."], expect=["FAIL"], checks=["originality"], sim=RESKIN)
draft("reskin-hanoi", 6, "C", "A warehouse robot moves a stack of $7$ crates of different sizes from bay $X$ to bay $Z$, using bay $Y$ as a holding area. Each bay holds a single stack. It moves one crate at a time, always the top crate of a stack, and a crate may never rest on a smaller crate. What is the least number of moves?", 127,
      "from collections import deque\nN = 7\nstart = (tuple(range(N, 0, -1)), (), ())\nseen = {start: 0}\nq = deque([start])\nwhile q:\n    s = q.popleft()\n    if len(s[2]) == N:\n        print(seen[s])\n        break\n    for a in range(3):\n        for b in range(3):\n            if a != b and s[a] and (not s[b] or s[b][-1] > s[a][-1]):\n                t = list(s)\n                t[b] = s[b] + (s[a][-1],)\n                t[a] = s[a][:-1]\n                t = tuple(t)\n                if t not in seen:\n                    seen[t] = seen[s] + 1\n                    q.append(t)",
      "Let $m_n$ be the least number of moves for $n$ crates. When the largest crate first leaves bay $X$, the other $n - 1$ must all be stacked on a single other bay, which takes at least $m_{n-1}$ moves. When it last arrives at bay $Z$, the others are again stacked on one bay, and at least $m_{n-1}$ more moves bring them to $Z$. With at least one move of the largest crate, $m_n \\ge 2m_{n-1} + 1$, and moving the stack, the largest crate, then the stack achieves this. Since $m_1 = 1$, we get $m_n = 2^n - 1$ and $m_7 = 127$.",
      ["Where are the other crates when the largest one moves?", "Use recursion on the number of crates, moving the smaller stack twice."], expect=["FAIL"], checks=["originality"], sim=RESKIN)
# A routine sum in a story. The live judge passes it as having no specific source, which is the known limit of the check (see README).
draft("reskin-gauss", 7, "A", "A runner's training plan adds one lap each day: $1$ lap on day $1$, $2$ laps on day $2$, and so on. How many laps has the runner done in total after $40$ days?", 820,
      "print(sum(range(1, 41)))", "Pair day $k$ with day $41 - k$: each pair totals $41$ laps and there are $20$ pairs, so the total is $820$.",
      ["Compare the first day with the last.", "Use the arithmetic series trick: pair days so each pair has the same total."], expect=["PASS", "FAIL", "INVESTIGATE"])
draft("reskin-snail", 7, "A", "A hiker on a $26$ km mountain trail gains $5$ km each day and slides back $4$ km each night. Starting at the bottom on day $1$, on which day does the hiker first reach the $26$ km mark?", 22,
      "pos, day = 0, 0\nwhile True:\n    day += 1\n    pos += 5\n    if pos >= 26:\n        print(day)\n        break\n    pos -= 4",
      "Each full day and night gains $1$ km. After $21$ days and nights the hiker is at $21$ km, and on day $22$ the hiker climbs $5$ km to reach $26$ km. Before that the daily peak is at most $25$ km, so day $22$ is the first time.",
      ["Where is the hiker each morning?", "Bound the daily peak: it is the morning position plus $5$, and the final day has no slide back."], expect=["FAIL"], checks=["originality"], sim=RESKIN)
variant("ok-digit-product", "near-copy-of-bank-digit-weight", ["FAIL"], ["originality_lexical", "originality"], sim=RESKIN, kyu=6, statement="How many positive integers less than $10^{18}$ have decimal digits that sum to $3$ and are divisible by $37$?", answer="216",
        check_program="from itertools import combinations_with_replacement as c\nprint(len({sum(10 ** i for i in p) for p in c(range(18), 3) if sum(10 ** i for i in p) % 37 == 0}))", solution="Powers of $10$ have residues $1$, $10$ and $26$ modulo $37$ in turn, and a sum of three powers is divisible by $37$ exactly when the three positions are distinct modulo $3$. With $6$ positions in each class there are $6^3 = 216$ such numbers.")
variant("ok-digit-product", "near-copy-of-bank-triples", ["FAIL"], ["originality_lexical", "originality"], sim=RESKIN, kyu=6, statement="How many triples of integers $(a,b,c)$ satisfy $1 \le a < b < c \le 80$ and $$a^2+b^2+c^2-ab-bc-ca=1027?$$", answer="180",
        check_program="print(sum(1 for a in range(1, 81) for b in range(a + 1, 81) for c in range(b + 1, 81) if a * a + b * b + c * c - a * b - b * c - c * a == 1027))", solution="With $x = b - a$ and $y = c - b$ the condition is $x^2 + xy + y^2 = 1027$. Counting the positive solutions, each weighted by the room left for $a$, gives the answer.")

# ---- Right answers with wrong reasoning.
variant("ok-shifted-divisor", "flawed-solution-unjustified", ["FAIL"], ["solution_audit"], sim=dict(audit={"reaches_answer": True, "issues": [{"severity": "material", "issue": "the count is asserted with no argument"}]}),
        solution="Trying a few values shows that the pattern gives half of the $30$ divisors of a related number, so the answer is $15$.")
variant("ok-three-remainders", "flawed-solution-false-step", ["FAIL"], ["solution_audit"], sim=dict(audit={"reaches_answer": True, "issues": [{"severity": "material", "issue": "the Chinese remainder step is misapplied"}]}),
        solution="By the Chinese remainder theorem the three conditions have a unique solution modulo $5 + 7 + 4 = 16$. Adding the remainders gives $2 + 3 + 0 = 5$, and $5 + 3 \\cdot 16 + (-1) = 52$, so the answer is $52$.")

# ---- Bad hints, which only a critic can see.
variant("ok-three-remainders", "bad-hints-restate", ["FAIL"], ["solution_audit"], sim=dict(audit={"reaches_answer": True, "issues": [{"severity": "material", "issue": "Hint 1: it only restates the statement"}]}),
        hints=["Find the smallest positive integer meeting the three conditions.", "Remember that it must be a multiple of $4$ and meet the other two conditions."])
variant("ok-seat-row", "bad-hints-give-answer", ["FAIL"], ["solution_audit"], sim=dict(audit={"reaches_answer": True, "issues": [{"severity": "material", "issue": "Hint 2: it states the final answer"}]}),
        hints=["What seat number does each person have?", "They are in seats $7$ and $16$, so the count is $8$."])

# ---- Proof problems take their own path.
PROOF = dict(type="proof", rubric=[dict(marks=2, criterion="Factorises the expression or reduces to residues."), dict(marks=5, criterion="Shows divisibility by both $2$ and $3$.")])
def proof(pid, statement, solution, expect, checks=None, sim=None, **extra):
    d = dict(id=pid, title=pid.replace("-", " ").capitalize(), kyu=3, topic="N", subtopics=["casework"], status="draft", statement=statement, hints=["Look at the factors of the expression.", "Factorise it: a product of three consecutive integers appears, which settles divisibility by $2$ and by $3$."],
             solution=solution, provenance=dict(kind="original", author="task-05-tests"), stats=dict(solves=0, attempts=0, liked=0), **PROOF)
    d.update(extra)
    ALL[pid] = dict(draft=d, expected=dict(verdict=list(expect), checks=checks), sim=sim or {})


proof("proof-ok", "Prove that for every integer $n$ the number $n^5 + 5n^3 - 6n$ is divisible by $6$.",
      "Write $n^5 + 5n^3 - 6n = n(n^2 - 1)(n^2 + 6) $, which holds because $(n^2-1)(n^2+6) = n^4 + 5n^2 - 6$. The product $(n-1)n(n+1)$ of three consecutive integers is divisible by both $2$ and $3$, hence by $6$, and it divides the expression. So the expression is divisible by $6$.", ["PASS"])
proof("proof-flawed", "Prove that for every integer $n$ the number $n^5 + 5n^3 - 6n$ is divisible by $6$.",
      "Checking $n = 1$ gives $0$ and $n = 2$ gives $60$, and both are divisible by $6$. So the claim holds for every integer $n$.", ["FAIL"], ["solution_audit"],
      sim=dict(audit={"reaches_answer": False, "issues": [{"severity": "material", "issue": "two cases do not prove it for all n"}]}))

# ---- Classical provenance.
variant("ok-digit-product", "classical-contest-source", ["FAIL"], ["originality"], provenance=dict(kind="classical", author="task-05-tests", source="AIME 1900, Problem 1"))
variant("ok-digit-product", "classical-theorem-source", ["INVESTIGATE"], ["originality"], provenance=dict(kind="classical", author="task-05-tests", source="A classical theorem"))

# ---- Mis-rated: hard, but labelled as a warm-up.
draft("mis-rated-hard", 8, "C", "Find the number of subsets of $\\{1, 2, \\dots, 16\\}$ containing no two elements that differ by $3$ or by $5$, modulo $1000$.", 324,
      "c = 0\nfor m in range(1 << 16):\n    if not (m & (m >> 3)) and not (m & (m >> 5)):\n        c += 1\nprint(c % 1000)", "Scan the numbers from $1$ to $16$ in order, remembering which of the last five were chosen. A transfer over these $32$ states gives $1324$ subsets, which is $324$ modulo $1000$.",
      ["Encode a subset as a binary string.", "Scan left to right, remembering the last five positions."], expect=["INVESTIGATE", "FAIL"], checks=["difficulty", "blind_solves", "solution_audit"],
      sim=dict(solves=["1", "2", "3", "4", "5", "6", "7"], solve_tokens=9000))


def main():
    out = HERE / "drafts"
    out.mkdir(exist_ok=True)
    for old in out.glob("*.json"):
        old.unlink()
    for pid, e in ALL.items():
        d = e["draft"]
        slug = (WHY.get(pid) or WHY.get(e.get("base")) or ("casework",))[0]
        d["subtopics"] = [slug]
        (out / f"{pid}.json").write_text(json.dumps(e["draft"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    expected = {pid: dict(e["expected"], sim=e["sim"]) for pid, e in ALL.items()}
    (HERE / "expected.json").write_text(json.dumps(expected, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(ALL)} drafts")


if __name__ == "__main__":
    main()
