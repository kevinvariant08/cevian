"""Builds the CMO 2023 P5 draft (BTI Problem 86) as {draft, report} JSON."""
import json, pathlib

ID = "parallels-through-k"

statement = r"""Let $ABC$ be an acute triangle and let $K$ be a point on the extension of $BC$ beyond $C$. The line through $K$ parallel to $AB$ contains a point $P\ne K$ with $BP=BK$, and the line through $K$ parallel to $AC$ contains a point $Q\ne K$ with $CQ=CK$. The circumcircle of triangle $KPQ$ meets line $AK$ again at $T$. Prove that
1. $\angle BTC+\angle APB=\angle CQA$;
2. $AP\cdot BT\cdot CQ=AQ\cdot CT\cdot BP$."""

hints = [
    r"""Both parts come from two similarities that share the vertex $B$ or $C$. Build a point $D$ with $\triangle CTD\sim\triangle CQA$, so that $\angle CQA=\angle CTD$. What does part 1 then say about the angle $\angle BTD$?""",
    r"""Part 1 follows from $\triangle BTD\sim\triangle BPA$, and spiral similarities come in pairs, so it is enough to prove $\triangle BTP\sim\triangle BDA$ (and you already have $\triangle CTQ\sim\triangle CDA$). Prove it by SAS: one angle and one ratio.""",
    r"""For the angle, chase $\angle BAD=\angle CAD-\angle CAB$ using $\angle CAD=\angle CQT$, the isosceles triangles $BKP$ and $CKQ$, the cyclic $KPQT$ and the parallels, to reach $\angle BPT$. For the ratio $\frac{PT}{PB}=\frac{AD}{AB}$, use $AD=TQ\cdot\frac{AC}{QC}$, $PB=KB$, $QC=KC$, then the law of sines in $PQT$ and the ratio lemma $\frac{KC}{KB}\cdot\frac{AB}{AC}=\frac{\sin\angle KAC}{\sin\angle KAB}$. Part 2 is then the product of the ratios from the two similarities."""
]

solution = r"""Let $D$ be the point with $\triangle CTD$ directly similar to $\triangle CQA$. Then $C$ is the centre of a spiral similarity taking $T\mapsto D$, $Q\mapsto A$, so also $\triangle CTQ\sim\triangle CDA$.

**Part 1.** Since $\angle CQA=\angle CTD$, the claim is $\angle CTD-\angle BTC=\angle APB$, that is, $\angle BTD=\angle APB$. This follows from $\triangle BTD\sim\triangle BPA$, which by the same pairing is equivalent to $\triangle BTP\sim\triangle BDA$. We prove the latter by SAS.

*Angle.* Using $\angle CAD=\angle CQT$ (from $\triangle CDA\sim\triangle CTQ$), $\angle KQC=\angle CKQ$ (as $CK=CQ$), $\angle KQT=180^\circ-\angle KPT$ (cyclic $KPQT$), $\angle CAB=180^\circ-\angle PKQ$ (as $KP\parallel AB$, $KQ\parallel AC$) and $\angle PKB=\angle BPK$ (as $BK=BP$):
$$\angle BAD=\angle CAD-\angle CAB=\angle KQT-\angle KQC-\angle CAB=\angle PKQ-\angle CKQ-\angle KPT=\angle PKB-\angle KPT=\angle BPK-\angle KPT=\angle BPT.$$

*Ratio.* We need $\frac{PT}{PB}=\frac{AD}{AB}$. From $\triangle CDA\sim\triangle CTQ$, $AD=TQ\cdot\frac{AC}{QC}$; also $PB=KB$ and $QC=KC$. So the ratio condition is
$$\frac{PT}{QT}\cdot\frac{KC}{KB}\cdot\frac{AB}{AC}=1.$$
By the law of sines in $PQT$, $\frac{PT}{QT}=\frac{\sin\angle PQT}{\sin\angle QPT}$, and comparing areas of $AKC$ and $AKB$, $\frac{KC}{KB}\cdot\frac{AB}{AC}=\frac{\sin\angle KAC}{\sin\angle KAB}$. Since $KP\parallel AB$, $\angle PQT=\angle PKT=180^\circ-\angle KAB$; since $KQ\parallel AC$, $\angle QPT=\angle QKT=\angle KAC$. The product is therefore $\frac{\sin\angle KAB}{\sin\angle KAC}\cdot\frac{\sin\angle KAC}{\sin\angle KAB}=1$.

Hence $\triangle BTP\sim\triangle BDA$, so $\triangle BTD\sim\triangle BPA$, which proves part 1.

**Part 2.** From $\triangle BTD\sim\triangle BPA$, $\frac{AP}{BP}=\frac{DT}{BT}$; from $\triangle CTD\sim\triangle CQA$, $\frac{CQ}{AQ}=\frac{CT}{DT}$. Therefore
$$\frac{AP}{BP}\cdot\frac{BT}{CT}\cdot\frac{CQ}{AQ}=\frac{DT}{BT}\cdot\frac{BT}{CT}\cdot\frac{CT}{DT}=1,$$
that is, $AP\cdot BT\cdot CQ=AQ\cdot CT\cdot BP$. $\blacksquare$"""

milestones = [
    {"id": "m1", "marks": 1, "criterion": r"""Introduces the auxiliary point $D$ with $\triangle CTD\sim\triangle CQA$ (directly similar), notes the paired similarity $\triangle CTQ\sim\triangle CDA$, and reduces part 1 to $\angle BTD=\angle APB$, or to $\triangle BTD\sim\triangle BPA$, or an equivalent reduction."""},
    {"id": "m2", "marks": 2, "criterion": r"""Proves the angle equality $\angle BAD=\angle BPT$ (or the corresponding angle for an equivalent similarity) by a correct chase using the isosceles triangles $BKP$, $CKQ$, the cyclic quadrilateral $KPQT$ and the parallels."""},
    {"id": "m3", "marks": 2, "criterion": r"""Proves the ratio condition $\frac{PT}{PB}=\frac{AD}{AB}$, for example by reducing it to $\frac{PT}{QT}\cdot\frac{KC}{KB}\cdot\frac{AB}{AC}=1$ and evaluating with the law of sines and the ratio lemma, and concludes $\triangle BTP\sim\triangle BDA$, hence part 1. Award 1 for a correct reduction without the evaluation."""},
    {"id": "m4", "marks": 2, "criterion": r"""Proves part 2, for example by multiplying the length ratios from $\triangle BTD\sim\triangle BPA$ and $\triangle CTD\sim\triangle CQA$. Part 2 proved on its own by any valid method earns these 2 marks."""}
]

alternative_routes = [
    {"name": "Trigonometric or complex computation", "milestones": [
        {"id": "a1", "marks": 2, "criterion": r"""Parametrises the configuration (for example by the angles of $ABC$ and $BK$, or complex coordinates) and locates $P$, $Q$ and $T$ explicitly, including a correct description of $T$ on line $AK$."""},
        {"id": "a2", "marks": 3, "criterion": r"""Proves part 1 by computing the three angles, or their tangents or directions, and verifying the identity."""},
        {"id": "a3", "marks": 2, "criterion": r"""Proves part 2 by computing the six lengths or their ratios and verifying the identity."""}
    ]}
]

fatal_errors = [
    {"error": r"""Takes $D$ with $\triangle CTD$ oppositely similar to $\triangle CQA$, or otherwise uses the paired similarity $\triangle CTQ\sim\triangle CDA$ without a spiral similarity that justifies it.""", "cap": 3},
    {"error": r"""Proves part 1 only for a special position of $K$ or a special triangle (for example isosceles $ABC$), or checks it numerically.""", "cap": 1},
    {"error": r"""Assumes $T$ is the second intersection of $AK$ with a different circle, or treats $P$ or $Q$ as $K$ itself.""", "cap": 1}
]

draft = {
    "id": ID,
    "title": "Parallels Through K",
    "kyu": 2,
    "topic": "G",
    "subtopics": ["spiral-similarity", "similar-triangles", "angle-chasing", "law-of-sines"],
    "type": "proof",
    "status": "draft",
    "statement": statement,
    "hints": hints,
    "solution": solution,
    "rubric": [{"marks": m["marks"], "criterion": m["criterion"]} for m in milestones],
    "provenance": {
        "kind": "classical",
        "author": "Kevin Hu",
        "source": "CMO 2023 P5 (China)",
        "book": "Beyond the Incenter, Kevin Hu (2026), Chapter 6 (Geometric Transformations), Problem 86"
    },
    "marking": {"milestones": milestones, "alternative_routes": alternative_routes, "fatal_errors": fatal_errors},
    "stats": {"solves": 0, "attempts": 0, "liked": 0}
}

notes = [
    "Source: China Mathematical Olympiad 2023 Problem 5 (the book writes 'CMO 2023 P5'), as Problem 86 in Beyond the Incenter, Chapter 6 (book p. 178-180). Please confirm the CMO here is the Chinese MO, not the Canadian MO, before publishing.",
    "Statement: the book says 'construct lines KP and KQ parallel to AB and AC such that BK = BP and CK = CQ'. The draft adds P != K and Q != K, since K itself satisfies BK = BP on the first line.",
    "Verdict on Kevin's solution: correct. Every step checks: the spiral-similarity pairing, the angle chase to angle BAD = angle BPT, the ratio reduction with the law of sines and the ratio lemma, and the telescoping product for part 2.",
    "Gap 1 (minor): D is defined by 'triangle CTD ~ triangle CQA' without saying directly similar; the pairing to triangle CTQ ~ triangle CDA needs the same orientation. Draft says 'directly similar'.",
    "Gap 2 (minor): undirected angles throughout, so the chase (e.g. angle BAD = angle CAD - angle CAB, angle CTD - angle BTC = angle BTD) is proved for the diagram's configuration only. Acceptable at olympiad level for this problem, but directed angles would make it airtight.",
    "Gap 3 (wording): the book says part 1 'is equivalent to' the similarity; only the sufficient direction is needed and the draft says 'follows from'.",
    "Kyu 2 (CMO P5 is day 2 P2). Not run through the gate and no independent audit by a second model, due to the 30-minute limit. No tkz-euclide figure yet: port the book's Problem 86 figure into pipeline/figures/.",
]

report = {"id": ID, "verdict": "UNVERIFIED: book solution, checked by hand only; not run through the gate", "checks": [], "notes": notes}

out = {"draft": draft, "report": report}
here = pathlib.Path(__file__).parent
(here / f"{ID}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
pend = here.parent.parent / "review" / "pending"
pend.mkdir(parents=True, exist_ok=True)
(pend / f"{ID}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print("wrote", ID)
