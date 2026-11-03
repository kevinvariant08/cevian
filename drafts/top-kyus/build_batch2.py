"""Builds the Iran 2012 residue-polynomial and ISL 2008 A5 drafts as {draft, report} JSON."""
import json, pathlib

here = pathlib.Path(__file__).parent
pend_dirs = [here.parent.parent / "review" / "pending", pathlib.Path(r"C:\Users\kevin\mathwars\review\pending")]


def emit(draft, notes, verdict):
    rub = [{"marks": m["marks"], "criterion": m["criterion"]} for m in draft["marking"]["milestones"]]
    draft["rubric"] = rub
    out = {"draft": draft, "report": {"id": draft["id"], "verdict": verdict, "checks": [], "notes": notes}}
    text = json.dumps(out, indent=2, ensure_ascii=False)
    (here / f"{draft['id']}.json").write_text(text, encoding="utf-8")
    for d in pend_dirs:
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{draft['id']}.json").write_text(text, encoding="utf-8")
    print("wrote", draft["id"])


# ---------------------------------------------------------------- Iran 2012
iran = {
    "id": "residue-polynomials",
    "title": "Residue Polynomials",
    "kyu": 2,
    "topic": "N",
    "subtopics": ["fermat-euler-theorem", "power-sum-formulas", "newton-sums"],
    "type": "proof",
    "status": "draft",
    "statement": r"""Let $p$ be an odd prime. A polynomial $f(x)=\sum_{j=0}^{n}a_jx^j$ with integer coefficients is called an $i$-residue polynomial if
$$\sum_{\substack{p-1\mid j\\ j>0}}a_j\equiv i\pmod p.$$
Prove that $f(0),f(1),\dots,f(p-1)$ form a complete residue system modulo $p$ if and only if $f(x),f(x)^2,\dots,f(x)^{p-2}$ are $0$-residue polynomials and $f(x)^{p-1}$ is a $1$-residue polynomial.""",
    "hints": [
        r"""Sum a polynomial over $x=0,1,\dots,p-1$. Which monomials $x^j$ survive modulo $p$?""",
        r"""Show $\sum_{x=0}^{p-1}x^k\equiv-1$ if $(p-1)\mid k$, $k\ge1$, and $\equiv0$ otherwise. Then $h$ is $i$-residue exactly when $\sum_x h(x)\equiv-i$, so the conditions are statements about the power sums $s_k=\sum_x f(x)^k$.""",
        r"""For the converse, count. The number $N_c$ of $x$ with $f(x)\equiv c$ satisfies $N_c\equiv\sum_x\bigl(1-(f(x)-c)^{p-1}\bigr)\pmod p$. Expand and use the power sums."""
    ],
    "solution": r"""**Lemma.** For $k\ge1$, $\sum_{x=0}^{p-1}x^k\equiv-1\pmod p$ if $(p-1)\mid k$, and $\equiv0$ otherwise.

If $(p-1)\mid k$, Fermat gives $x^k\equiv1$ for $1\le x\le p-1$, and $0^k=0$, so the sum is $p-1\equiv-1$. Otherwise let $g$ be a primitive root; then $g^k\not\equiv1$, and multiplying by $g$ permutes the nonzero residues, so $g^k\sum x^k\equiv\sum x^k$, giving $\sum x^k\equiv0$.

**Reduction.** For $h(x)=\sum_jc_jx^j$ with integer coefficients,
$$\sum_{x=0}^{p-1}h(x)=\sum_jc_j\sum_{x=0}^{p-1}x^j\equiv-\sum_{\substack{p-1\mid j\\ j>0}}c_j\pmod p,$$
since the $j=0$ term is $c_0p$. So $h$ is $i$-residue exactly when $\sum_xh(x)\equiv-i$. With $s_k=\sum_{x=0}^{p-1}f(x)^k$, the condition in the problem reads $s_k\equiv0$ for $1\le k\le p-2$ and $s_{p-1}\equiv-1$.

**Forward.** If the $f(x)$ form a complete residue system, $s_k\equiv\sum_{y=0}^{p-1}y^k$, and the lemma gives exactly these values.

**Converse.** Fix a residue $c$ and let $N_c$ be the number of $x\in\{0,\dots,p-1\}$ with $f(x)\equiv c$. By Fermat, $1-(y-c)^{p-1}$ is $\equiv1$ if $y\equiv c$ and $\equiv0$ otherwise, so, using $\sum_x1=p\equiv0$,
$$N_c\equiv\sum_{x=0}^{p-1}\bigl(1-(f(x)-c)^{p-1}\bigr)\equiv-\sum_{k=0}^{p-1}\binom{p-1}{k}(-c)^{p-1-k}s_k\pmod p.$$
Here $s_0=p\equiv0$ and $s_1,\dots,s_{p-2}\equiv0$, so only $k=p-1$ survives and $N_c\equiv-s_{p-1}\equiv1$. Since $0\le N_c\le p$, $N_c=1$ for every $c$, so the values form a complete residue system. $\blacksquare$""",
    "provenance": {
        "kind": "classical",
        "author": "Kevin Hu",
        "source": "Iran MO 2011-2012"
    },
    "marking": {
        "milestones": [
            {"id": "m1", "marks": 2, "criterion": r"""Proves the power-sum lemma: for $k\ge1$, $\sum_{x=0}^{p-1}x^k\equiv-1$ if $(p-1)\mid k$ and $\equiv0$ otherwise (by a primitive root, or by multiplying by some $a$ with $a^k\not\equiv1$). Quoting it as well known without proof earns 1."""},
            {"id": "m2", "marks": 1, "criterion": r"""Deduces that $\sum_xh(x)\equiv-\sum_{(p-1)\mid j,\,j>0}c_j$ for any integer polynomial $h$, and rewrites the conditions as $s_k\equiv0$ for $1\le k\le p-2$ and $s_{p-1}\equiv-1$, where $s_k=\sum_xf(x)^k$."""},
            {"id": "m3", "marks": 1, "criterion": r"""Proves the forward direction: a complete residue system has the same power sums as $0,1,\dots,p-1$, then applies the lemma."""},
            {"id": "m4", "marks": 1, "criterion": r"""For the converse, expresses the number $N_c$ of $x$ with $f(x)\equiv c$ modulo $p$ as $\sum_x\bigl(1-(f(x)-c)^{p-1}\bigr)$, using Fermat."""},
            {"id": "m5", "marks": 1, "criterion": r"""Expands binomially and uses the power-sum conditions, including $s_0=p\equiv0$, to get $N_c\equiv1\pmod p$."""},
            {"id": "m6", "marks": 1, "criterion": r"""Concludes $N_c=1$ for every $c$ from $0\le N_c\le p$. Concluding from $N_c\equiv1$ alone, with no bound, earns 0 here."""}
        ],
        "alternative_routes": [
            {"name": "Newton's identities", "milestones": [
                {"id": "a1", "marks": 4, "criterion": r"""The lemma, the reduction and the forward direction, as in m1-m3 (same deductions apply)."""},
                {"id": "a2", "marks": 1, "criterion": r"""Shows some $f(x)\equiv0$ (otherwise $s_{p-1}\equiv p\equiv0$), so the constant term $e_p$ of $\prod_x(t-f(x))=t^p+e_1t^{p-1}+\dots+e_p$ is $\equiv0$."""},
                {"id": "a3", "marks": 1, "criterion": r"""Uses Newton's identities $s_k+e_1s_{k-1}+\dots+ke_k=0$ to get $e_1\equiv\dots\equiv e_{p-2}\equiv0$ (as $k$ is invertible for $k\le p-2$) and $e_{p-1}\equiv-1$, so $\prod_x(t-f(x))\equiv t^p-t$."""},
                {"id": "a4", "marks": 1, "criterion": r"""Concludes: every residue $c$ is a root of $t^p-t$, so $p\mid\prod_x(c-f(x))$ and some $f(x)\equiv c$; $p$ values covering $p$ residues take each once."""}
            ]}
        ],
        "fatal_errors": [
            {"error": r"""Proves only the forward direction.""", "cap": 4},
            {"error": r"""Claims that $s_1,\dots,s_{p-1}$ determine $\prod_x(t-f(x))$ modulo $p$ by Newton's identities without showing $e_p\equiv0$ (the identity at $k=p$ has coefficient $p\equiv0$ and says nothing about $e_p$).""", "cap": 4},
            {"error": r"""Reads $f^k$ as the $k$-fold composition $f(f(\cdots))$ rather than the power $f(x)^k$.""", "cap": 2}
        ]
    },
    "stats": {"solves": 0, "attempts": 0, "liked": 0}
}

iran_notes = [
    "Source: Iran Mathematical Olympiad 2011-2012. The kevinvariant marking file (marking/problems/iran-2012-residue-polynomials.md) does not give the round or problem number; please add it before publishing.",
    "Solution: Kevin's second solution (counting with an indicator), checked line by line and correct; the lemma uses the 'multiply by g' form from his marked full-marks example instead of the geometric-series form, which avoids dividing by g^k - 1. Kevin's first solution (Newton's identities) is also correct and is kept as the alternative route in the rubric.",
    "Rubric: the 10-mark kevinvariant scheme rescaled to 7. Route B conclusion marks (2+2+2 there) became 1+1+1; the two-mark Route A conclusion folded into a4. Caps and fatal errors follow the kevinvariant file.",
    "Independent audit (Opus, medium): solution and rubric CORRECT, no issues.",
    "Kyu 2: the counting finish is short once seen, but the reduction to power sums and the e_p trap in the Newton route put it above 3 kyu. Not run through the gate.",
]
emit(iran, iran_notes, "UNVERIFIED: Kevin's solution, checked by hand; independently audited")

# ---------------------------------------------------------------- ISL 2008 A5
isl = {
    "id": "four-cyclic-ratios",
    "title": "Four Cyclic Ratios",
    "kyu": 2,
    "topic": "A",
    "subtopics": ["am-gm", "polynomial-factoring", "bounding"],
    "type": "proof",
    "status": "draft",
    "statement": r"""Let $a,b,c,d$ be positive real numbers with $abcd=1$ and
$$a+b+c+d>\frac ab+\frac bc+\frac cd+\frac da.$$
Prove that
$$a+b+c+d<\frac ba+\frac cb+\frac dc+\frac ad.$$""",
    "hints": [
        r"""Neither cyclic sum is symmetric, but their total is much nicer. It is enough to show $2(a+b+c+d)\le\left(\frac ab+\frac bc+\frac cd+\frac da\right)+\left(\frac ba+\frac cb+\frac dc+\frac ad\right)$.""",
        r"""Group the eight fractions by denominator: $\frac{a+c}{b}+\frac{b+d}{c}+\frac{c+a}{d}+\frac{d+b}{a}$. Using $abcd=1$ this factors as $(a+c)(b+d)(ac+bd)$.""",
        r"""After dividing by $(a+c)(b+d)$ you need $ac+bd\ge\frac2{a+c}+\frac2{b+d}$. Bound each fraction by AM-GM and set $x=\sqrt{ac}$, so $\sqrt{bd}=\frac1x$."""
    ],
    "solution": r"""Let $S=a+b+c+d$, $X=\frac ab+\frac bc+\frac cd+\frac da$ and $Y=\frac ba+\frac cb+\frac dc+\frac ad$. We show $X+Y\ge2S$; then $S>X$ gives $Y\ge2S-X>S$.

Grouping by denominator and using $abcd=1$,
$$X+Y=\frac{a+c}{b}+\frac{b+d}{c}+\frac{c+a}{d}+\frac{d+b}{a}=(a+c)\Bigl(\frac1b+\frac1d\Bigr)+(b+d)\Bigl(\frac1a+\frac1c\Bigr)$$
$$=(a+c)(b+d)\Bigl(\frac1{bd}+\frac1{ac}\Bigr)=(a+c)(b+d)(ac+bd).$$
Since $2S=(a+c)(b+d)\bigl(\frac2{b+d}+\frac2{a+c}\bigr)$, it suffices to prove
$$ac+bd\ge\frac2{a+c}+\frac2{b+d}.$$
By AM-GM, $a+c\ge2\sqrt{ac}$ and $b+d\ge2\sqrt{bd}$, so the right side is at most $\frac1{\sqrt{ac}}+\frac1{\sqrt{bd}}=\sqrt{bd}+\sqrt{ac}$, using $abcd=1$. Let $x=\sqrt{ac}$, so $\sqrt{bd}=\frac1x$, and put $u=x+\frac1x\ge2$. Then
$$ac+bd-\sqrt{ac}-\sqrt{bd}=x^2+\frac1{x^2}-x-\frac1x=u^2-u-2=(u-2)(u+1)\ge0.$$
Hence $X+Y\ge2S$, and the result follows. $\blacksquare$""",
    "provenance": {
        "kind": "classical",
        "author": "Kevin Hu",
        "source": "IMO Shortlist 2008 A5",
        "book": "Inequalities in Mathematical Olympiads, Kevin Hu (2026), Section 1.4, Problem 3"
    },
    "marking": {
        "milestones": [
            {"id": "m1", "marks": 2, "criterion": r"""Reduces the problem to $X+Y\ge2S$ (with $S=a+b+c+d$ and $X$, $Y$ the two cyclic sums), or to another inequality that holds without the hypothesis and, combined with $S>X$, gives $S<Y$; the deduction must be stated."""},
            {"id": "m2", "marks": 2, "criterion": r"""Shows $X+Y=(a+c)(b+d)(ac+bd)$ using $abcd=1$, or an equivalent factorisation that reduces $X+Y\ge2S$ to $ac+bd\ge\frac2{a+c}+\frac2{b+d}$."""},
            {"id": "m3", "marks": 3, "criterion": r"""Proves $ac+bd\ge\frac2{a+c}+\frac2{b+d}$, for example by AM-GM on $a+c$ and $b+d$, then $x^2+x^{-2}\ge x+x^{-1}$ for $x=\sqrt{ac}$. Award 1 for the AM-GM step reducing to $ac+bd\ge\sqrt{ac}+\sqrt{bd}$ alone."""}
        ],
        "alternative_routes": [
            {"name": "Weighted AM-GM (official)", "milestones": [
                {"id": "a1", "marks": 2, "criterion": r"""Uses $abcd=1$ to write $a=\sqrt[4]{\frac{a^3}{bcd}}$ (and cyclically), so that both sides of a target inequality have degree $0$."""},
                {"id": "a2", "marks": 3, "criterion": r"""Proves by AM-GM bounds such as $4a\le2\cdot\frac ad+\frac dc+\frac ab$ (from $a=\sqrt[4]{(a/d)^2(d/c)(a/b)}$) whose cyclic sum gives $4S\le3Y+X$; the mirror bound $4S\le3X+Y$ also works."""},
                {"id": "a3", "marks": 2, "criterion": r"""Combines $4S\le3Y+X$ with $S>X$ to conclude $S<Y$."""}
            ]}
        ],
        "fatal_errors": [
            {"error": r"""Assumes an ordering of $a,b,c,d$ (or symmetry) that the cyclic expressions do not allow.""", "cap": 2},
            {"error": r"""Proves only $X+Y\ge2S$ or another unconditional inequality without deducing $S<Y$ from the hypothesis $S>X$, or derives only $S\le Y$ with no strictness.""", "cap": 5},
            {"error": r"""Applies AM-GM in the wrong direction, e.g. uses $\frac1{a+c}\ge\frac1{2\sqrt{ac}}$.""", "cap": 2}
        ]
    },
    "stats": {"solves": 0, "attempts": 0, "liked": 0}
}

isl_notes = [
    "Source: IMO Shortlist 2008 A5, as Problem 3 in Kevin's 'Inequalities in Mathematical Olympiads' (2026 edition, Section 1.4, p. 8-10).",
    "Solution: Kevin's Solution 1, checked line by line and correct. The document's '2(a+b+c+d) <= sum_sym a/b' is written here as X + Y >= 2S, and the step 'RHS >= LHS_max' is written as an explicit AM-GM bound. The official homogenisation solution (his Solution 2) is in the rubric as the alternative route.",
    "Kyu 2 per Kevin. The document has only four problems with content (chapters 2-12 are empty headings); Problems 1 (abc = 1, sum 1/(a+b+1) <= 1), 2 (sum 1/(1+2a) >= 1) and 4 (unsourced, M sum i a_i) are 5-3 kyu, so none was added at 2-1 kyu.",
    "Independent audit (Opus, medium): solution CORRECT. It caught a false sample bound in alternative-route milestone a2, now fixed to 4a <= 2(a/d) + d/c + a/b.",
    "Note for Kevin: Problem 2 in the document says a, b, c in R; it needs a, b, c > 0 (a = b = -1, c = 1 breaks it).",
]
emit(isl, isl_notes, "UNVERIFIED: Kevin's solution, checked by hand; independently audited")
