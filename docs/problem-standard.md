# The Kyuclid problem standard

This document defines a good Kyuclid problem at each kyu. The generator (tasks 06, 08 and 09), the verification gate (05), the reviewers (07) and community authors (17) all follow it.

**Status: draft for Kevin's approval.** The rules in sections 2 to 8 are ready to use. The ladder in section 1 is only partly calibrated, because task 03 has not finished: section 1.1 says what each number rests on. Decisions still open are in section 9. Every rule has an ID, and Appendix A says how each one is checked.

No contest problem text appears here. Every example is invented for this document.

## 1. The kyu ladder

### 1.1 What the numbers rest on

The brief asks for every claim to rest on the task 03 calibration table and synthesis report. The synthesis does not exist yet, so each claim below carries a label:

| Label | Source | How far to trust it |
|---|---|---|
| **[T]** | The calibration table in `tasks/03-corpus-analysis.md`, with Kevin's rule that classic AIME papers (before 2000) start one kyu easier | Agreed starting point |
| **[F]** | The first pass of the full AIME analysis: 248 of 1,035 records as of 30 October 2026. One model, no second pass and no review yet | Measured, but unreviewed and AIME only |
| **[D]** | Derived from each contest's time per problem | Arithmetic, not measured solve data. Task 18 replaces it |
| **[P]** | Proposed here, from task 02's kyu bands and judgement about the contests | Needs Kevin's approval (decision D3) |
| **[B]** | *Beyond the Incenter*, which Kevin allowed as the reference for 2 and 1 kyu difficulty. Cited by source credit, with no statement quoted | Kevin's own ordering, but geometry only |
| **[J]** | Judgement, with no data yet | Reviewers may overrule it |

**What is missing:**

- There are no 8 kyu records, and only 8 at 7 kyu, all from classic papers.
- There is no olympiad data, because wave 3 of the corpus has not been analysed. Every proof claim is [T], [B], [P] or [J].
- MOHS is empty on every corpus record so far. The MOHS column is the task 03 table and nothing more.
- Only AIME has been analysed. The AMC and UKMT positions are not yet tested against analysis records.

**Refresh this section when the task 03 synthesis lands.** Replace [F] with reviewed figures, and test [P] against waves 2 and 3.

### 1.2 What separates the kyus

From the 248 first-pass AIME records [F]:

| Kyu | Records | Short solution | Long solution | Low computation | Medium or high computation | First listed route rated easy | Rated hard |
|---|---|---|---|---|---|---|---|
| 7 | 8 | 100% | 0% | 100% | 0% | 100% | 0% |
| 6 | 53 | 100% | 0% | 100% | 0% | 100% | 0% |
| 5 | 63 | 89% | 0% | 94% | 6% | 84% | 0% |
| 4 | 83 | 37% | 1% | 65% | 35% | 14% | 2% |
| 3 | 33 | 3% | 9% | 33% | 67% | 0% | 21% |
| 2 | 8 | 0% | 62% | 38% | 62% | 0% | 100% |

The same analyst rated difficulty and kyu, so these columns are not independent of the kyu they sit beside.

**Counting steps does not separate the kyus.** Recorded key steps on the shortest route only rise from 3.1 at 7 kyu to 4.8 at 2 kyu, and techniques per problem only from 2.9 to 4.6. So this standard does not define kyu by the number of steps. It counts **non-routine steps** instead (rule K1), which need judgement.

Where modern and classic AIME positions landed, against the starting kyu [F]:

| Position | Modern: start → result | Classic: start → result |
|---|---|---|
| 1–5 | 5 → 36 at 6 kyu, 25 at 5 kyu | 6 → 8 at 7 kyu, 13 at 6 kyu |
| 6–10 | 4 → 22 at 5 kyu, 40 at 4 kyu | 5 → 4 at 6 kyu, 10 at 5 kyu |
| 11–15 | 3 → 27 at 4 kyu, 33 at 3 kyu, 8 at 2 kyu | 4 → 6 at 5 kyu, 16 at 4 kyu |

More than half of modern AIME 1–5 landed at 6 kyu rather than 5. See decision D4.

### 1.3 Definitions

- **K1. Non-routine step.** A step that a solver one rank below would not find by applying a named procedure: they have to choose something, such as an auxiliary object, a change of viewpoint, a bijection or a case split. Algebra and arithmetic after that choice are routine.
- **K2. How hidden the crux is.**
  - **Open:** the statement says what to do.
  - **Near:** the first sensible attempt finds it.
  - **Hidden:** the natural first attempt stalls, and the solver has to step back.
  - **Deep:** nothing in the statement points at it, and it needs a new description of the problem.
- **K3. Solve time** is for a solver at that rank who solves it, without hints, on paper.
- **K4. Types.** 8–4 kyu are answer problems only. 3 kyu has both. 2 kyu, 1 kyu and bosses are proofs only. See decisions D1 and D2.
- **K5. Anchors describe difficulty, not sources.** A problem is rated by how hard it is, not by which contest inspired it. If the inspiration and the result disagree, the result wins.

### 1.4 The ladder

| Kyu | Belt | Answer anchors | Proof anchors | Non-routine steps [J] | Crux [J] | Computation | Solve time |
|---|---|---|---|---|---|---|---|
| 8 | White | AMC 8 1–10 [T]; UKMT JMC early [P] | none | 0 | Open | Mental or a line of working [J] | 1–2 min [D] |
| 7 | Yellow | AMC 8 11–20, AMC 10/12 1–10 [T]; UKMT JMC late, IMC early [P] | none | 0–1 | Open or near | Low [F] | 2–4 min [D] |
| 6 | Orange | AMC 8 21–25, AMC 10/12 11–20, classic AIME 1–5 [T]; UKMT IMC late, SMC early; HMMT November early [P] | none | 1 | Near | Low [F] | 3–6 min [D] |
| 5 | Green | AMC 10/12 21–25, modern AIME 1–5, classic AIME 6–10 [T]; UKMT SMC late; HMMT November late [P] | none | 1 | Near | Low [F] | 6–12 min [D] |
| 4 | Blue | Modern AIME 6–10, classic AIME 11–15 [T]; HMMT February early [P] | none (see D1) | 1–2 | Near or hidden | Low, sometimes medium [F] | 10–20 min [D] |
| 3 | Purple | Modern AIME 11–15 [T]; HMMT February late [P] | IMO P1/P4, ISL x1–x2, MOHS 10–15 [T]; BMO1 late, BMO2 P1, USAMO P1/P4, EGMO P1/P4, CGMO early [P] | 2 | Hidden | Medium [F] | Answer 20–40 min; proof 30–60 min [D] |
| 2 | Brown | none (see D2) | IMO P2/P5, ISL x3–x5, MOHS 20–30 [T]; BMO2 late, USAMO P2/P5, EGMO P2/P5, CGMO late [P]; book references in 1.6 [B] | 2–3, or 1 deep | Hidden or deep | Whatever the proof needs. Long is fine; a slog is not (B2) | 60–120 min [D] |
| 1 | Red | none | IMO P3/P6, ISL x6+, MOHS 35+ [T]; USAMO P3/P6, EGMO P6 [P]; book references in 1.6 [B] | 3 or more, or 1 very deep | Deep | As for 2 kyu | 2–4 hours, and many strong solvers will not finish [D, J] |
| Boss | Black (dan) | none | No contest anchor. Chosen from Kevin's book (task 21) | Set by the book | Set by the book | Set by the book | Open-ended |

**MOHS.** The table in task 03 leaves gaps (6–9, 16–19, 31–34), but MOHS ratings normally come in steps of 5, so they rarely matter. A value in a gap takes the harder kyu [J]. MOHS 0–5 is a 4 kyu calibration signal only (D1).

**Solve times [D]** start from these contest averages: AMC 8 1.6 min a problem, AMC 10/12 3 min, AIME 12 min, BMO1 35 min, BMO2 52 min, and IMO, USAMO and EGMO 90 min. Each rung's range then allows for the position within the paper.

### 1.5 Examples

All of these are invented and are teaching aids. They do not go in the bank (decision D10). Each answer was computed by a program from the definitions, and each proof example has a full written proof, kept outside this repo with the other draft fields until Kevin decides D10. Section 10 records what the gate said about them. Only the two worked examples show their hints and solutions here.

**8 kyu**
1. Stickers are sold only in packs of $6$ and packs of $11$. What is the smallest number of packs that contains exactly $100$ stickers in total? (*Answer 10.*) *Reason: nothing to discover, but the greedy first try fails, so it teaches the reader to check.*
2. A rectangular patio is made of square slabs, laid in $5$ rows of $12$ slabs each. How many of the slabs touch the edge of the patio? (*Answer 30.*) *Reason: one short count, with the corners as the only trap.*

**7 kyu**
1. A $4 \times 4$ grid has rows and columns numbered from $1$ to $4$. How many squares made of whole grid cells, of any size from $1 \times 1$ to $4 \times 4$, contain the cell in row $2$ and column $2$? (*Answer 10.*) *Reason: splitting by size is the one choice, and it is nearly forced.*
2. A machine doubles the number put into it and then subtracts $3$. A number is put in, the result is put in again, and that result is put in a third time. The final result is $43$. What number was put in first? (*Answer 8.*) *Reason: working backwards is the single idea, and an equation also works.*

**6 kyu**
1. In triangle $ABC$ the angle at $C$ is a right angle, $AC = 20$ and $BC = 21$. A circle with its centre on side $AB$ is tangent to sides $AC$ and $BC$. Find its radius. Give your answer as a fraction in lowest terms. (*Answer 420/41.*) *Reason: one idea, that the radii are heights, and then an area equation.*
2. A positive integer has rising digits if each digit is greater than the digit before it, and every single-digit number counts as having rising digits. How many positive integers with rising digits are divisible by $5$? (*Answer 16.*) *Reason: seeing that a rising number is just a subset of digits turns a search into one count.*

**5 kyu**
1. The worked example in section 4.
2. Find the largest positive integer $n$ such that
$$\sum_{k=1}^{n} \dfrac{1}{\sqrt{k} + \sqrt{k + 1}} < 20.$$
(*Answer 439.*) *Reason: the one crux is rationalising a term, which is near, and the rest follows quickly.*

**4 kyu**
1. Triangle $ABC$ has $AB = 7$, $AC = 8$ and $BC = 9$. The internal bisector of angle $A$ meets the circumcircle of $ABC$ again at $D$. Then $AD^2 = \frac{m}{n}$, where $m$ and $n$ are coprime positive integers. Find $m + n$. (*Answer 177.*) *Reason: two tools have to be combined, the equal chords and Ptolemy, and then some computation.*
2. For a positive integer $n$, let $a(n)$ be the largest integer $k$ such that $2^k$ divides $3^n - 1$. Find the remainder when $a(1) + a(2) + \dots + a(1000)$ is divided by $1000$. (*Answer 494.*) *Reason: two linked steps, a formula for $a(n)$ and then a sum that must not be listed.*

**3 kyu**
1. A subset $A$ of $\{1, 2, \dots, 30\}$ is called sparse if there are no $x, y \in A$ with $x = 2y$ or $x = 3y$. The empty set is sparse. Find the remainder when the number of sparse subsets is divided by $1000$. (*Answer 512.*) *Reason: the hidden step is seeing independent staircase-shaped grids, and counting in the largest one is real but manageable work.*
2. The worked proof in section 8.5.
3. Let $ABC$ be a triangle with $AB \ne AC$ and circumcircle $\Gamma$. Its incircle touches $BC$, $CA$ and $AB$ at $D$, $E$ and $F$, and its excircle opposite $A$ touches $BC$ at $D'$. Lines $EF$ and $BC$ meet at $J$. Let $UV$ be the diameter of $\Gamma$ perpendicular to $BC$. Prove that $J$, $D'$, $U$ and $V$ lie on a circle. *Reason: three standard facts linked through the midpoint of $BC$. It was first rated 2 kyu, and moved down after comparison with the book's 2 kyu references.*

**2 kyu** (both proofs)
1. Let $a > b$ be coprime positive integers. Prove that there are infinitely many positive integers $n$ such that $n$ divides $a^n + b^n$. *Reason: the main case is one tool, but the case with $a + b$ a power of $2$ needs a second idea.*
2. Let $ABC$ be a triangle with $AB \ne AC$ and circumcircle $\Gamma$. Its incircle touches $CA$ and $AB$ at $E$ and $F$. A circle tangent to sides $AB$ and $AC$ and internally tangent to $\Gamma$ touches $\Gamma$ at $T$. The median from $A$ meets $\Gamma$ again at $R$. Prove that lines $EF$, $BC$ and $TR$ are concurrent. *Reason: it joins two distant configurations, and finding a route is the hard part. It was first rated 1 kyu, and moved down because the proof, once found, is far shorter in ideas than the book's 1 kyu references.*

**1 kyu**
1. Let $n \ge 3$ be an odd integer. There are $n$ lamps around a circle, and exactly one of them is on. In a move, you choose a lamp that is on and change the state of its two neighbours; the chosen lamp stays on. Determine, as a function of $n$, the smallest number of moves after which all $n$ lamps are on. *Reason: small cases give the formula, but the proof needs a new description of a position in which a move is a swap of particles on a line, and nothing in the statement suggests it. This is combinatorics, so the geometry references can't confirm its rating.*
2. No invented example. The reference is IMOSL 2009 G7 from the book, by source credit only, because I could not invent a geometry problem at that level (decision D9).

**Boss.** There are no invented examples here, which departs from the brief (decision D9). Bosses are not written: they are chosen from *Beyond the Incenter* with Kevin (task 21), and no invented problem can be shown to be harder than 1 kyu without real solvers.

### 1.6 Book references for 2 and 1 kyu

These are problems in *Beyond the Incenter*, named by source credit. Their statements aren't quoted, because rule 1's exception for the book covers bosses. They are geometry only, so the other three topics still rest on the labels in the ladder.

| Kyu | From the table in task 03 [T] | Proposed from the contest's position [P] |
|---|---|---|
| 3, as the floor | IMO 2015 P4, IMO 2014 P4, IMO 2024 P4, IMO 2006 P1, IMO 2003 P4, IMO 1995 P1 | USAMO 2021 P1, USAMO 2023 P1, USAMO 2009 P1, BMO2 2017 P3 |
| 2 | IMO 2012 P5, IMOSL 2009 G3, IMOSL 2011 G4, IMOSL 2025 G3 | CGMO 2018 P8, BMO2 2014 P4, USAMO 2006 P6 |
| 1 | IMOSL 2011 G6, IMOSL 2009 G7, IMOSL 2009 G8 | RMM 2017 P6 |

The book's Challenge Problems are arranged in roughly increasing order of difficulty, and they place IMOSL 2009 G3, then IMOSL 2011 G4, then IMOSL 2009 G7, then IMOSL 2009 G8. This agrees with the table, and it is the only evidence so far that doesn't come from position alone.

Two placements differ from what position alone suggests, and both are judgement [J]. The book labels BMO2 2017 P3 a "warm-down", so it sits at 3 kyu rather than among the later BMO2 problems. USAMO 2006 P6 is the last problem on its paper, but one spiral similarity carries most of it, so it sits at 2 kyu. Kevin should check both.

The length of the solutions in the book does not separate these kyus, so length is not a test: some 2 kyu solutions are longer than 1 kyu ones. The comparison has to be of how hidden the crux is.

### 1.7 The boss tier

Task 21 governs bosses. Where it differs from this standard, task 21 wins:

- **BS1.** A boss statement is quoted from the book with its source credit exactly as printed, plus the book credit. Section 7 does not apply. `provenance.kind` is `classical`.
- **BS2.** Hints follow task 21: hint 1 names the chapter's tool, and hint 2 comes from a Remark box. Section 5's H2 and H3 do not apply.
- **BS3.** The rubric comes from Kevin's solution, totals 7, and Kevin approves it.
- **BS4.** The bar for a boss: the hardest problem in its chapter, or one of the 3–5 hardest in the book, in Kevin's judgement. A chapter's hardest problem may be easier than 1 kyu, because the tier follows the book and not the ladder.
- **BS5.** Everything else here still applies to Kyuclid's own text (hints and solutions), including UK spelling. The book's title keeps its own spelling.

## 2. Statement rules

- **S1. One question.** A statement asks for exactly one thing. Multi-part problems are not allowed, and a chain of lemmas leading to a result counts as multi-part.
- **S2. Every object is defined.** Name every point, set, function and domain. Say whether integers are positive and whether a set may be empty, and whether pairs are ordered. "How many pairs" alone is a defect.
- **S3. The answer format is stated where it isn't obvious.** Required whenever the answer is a fraction ("Give your answer as a fraction in lowest terms") or is encoded (A4). Not needed for a plain integer count.
- **S4. No hidden case-splitting.** If several values are possible, the statement says so and asks for something single-valued, such as "the sum of all possible values". A problem must not rely on the solver missing a case.
- **S5. No reading tricks.** The difficulty is in the mathematics. Nothing depends on a surprising reading of "between", "all but", "at most" and so on. Where a phrase could be read two ways, use inequalities or say which is meant.
- **S6. No culturally specific knowledge.** Do not rely on knowing a sport's rules, a currency, a card deck, chess, school-year names or local dates. If the setting needs one of these, define it in full in the statement. Use plain settings and metric units.
- **S7. Standard mathematics only.** School and contest notation may be assumed. A theorem may be needed, but it isn't named in the statement. Define unusual notation.
- **S8. UK spelling** in all prose: colour, centre, neighbour, metre, factorise, incentre, circumcentre, orthocentre, excentre. IDs from the taxonomy are identifiers and stay as they are, even where they spell it `center` (D8).
- **S9. LaTeX conventions.**
  - Use `$…$` and `$$…$$`, with only the `base` and `ams` packages, and no custom macros.
  - In `$$…$$` write fractions as `\dfrac{a}{b}`. Inline, write `\frac{a}{b}`. Always use braces, so never `\frac12`.
  - Use `\cdot` for products of numbers or letters. Use `\times` only for sizes like `$4 \times 4$`. Never use `*`.
  - Use `\le` and `\ge`, `\dots`, `^\circ` and `\pmod{n}`, and `\mathbb{Z}` and so on for number sets.
  - Put every number and variable in maths mode, as in `$30$ km`. Don't use thousands separators.
- **S10. Markup.** Text fields render as paragraphs split by blank lines, with inline HTML passed through. Markdown is not rendered, whatever the schema's description says. Use `<b>` and `<code>`, and no lists.
- **S11. The statement stands without the figure.** A figure only illustrates. Every point and condition is in the words, because blind solvers and screen readers get only the words and `figure_alt`.
- **S12. No contest names or private IDs** in any public field of an original problem: title, statement, hints, solution or rubric.
- **S13. The title gives nothing away.** It doesn't name the technique, theorem or answer. The title appears on link cards and in search before anyone has tried the problem. The ID is permanent and visible in the URL, so the same applies to it.
- **S14. Neutral people.** Use neutral settings and "they" where people appear at all.

## 3. Answer rules

- **A1. By kyu.**

| Kyu | `answer_format` | Allowed answers |
|---|---|---|
| 8–6 | `integer`, `integer_0_999` or `rational` | Any integer with absolute value below $10^9$, or a simple rational (A3) |
| 5–3 | `integer_0_999` | An integer from 0 to 999 |
| 2, 1, boss | none | Proof problems |

- **A2. No `expression`.** The schema allows it, but the site's checker can't compare expressions and the blind solvers are told to give a number. So don't use it (D6).
- **A3. A simple rational** is $\frac{a}{b}$ in lowest terms with $a$ and $b$ of at most three digits each. Decimals are not used as keys. This cap has a technical reason too: the checker compares values rounded to six decimal places, and fractions under this cap never collide.
- **A4. Encoding at 5–3 kyu.** A non-integer value must be turned into an integer from 0 to 999 by one of these AIME-style forms: $m + n$ for coprime $\frac{m}{n}$; $a + b + c$ for a stated canonical form such as $\frac{a\sqrt{b}}{c}$, with its conditions in full; or the remainder modulo $1000$. The encoding must not be the hard part (D5).
- **A5. Unique.** Exactly one value satisfies the statement as written, and the check program confirms it.
- **A6. Not guessable.** The answer isn't guessable from the setup:
  - It is not 0 or 1, unless the proof that it is so is the point and a reviewer agrees.
  - It is not a number that appears in the statement.
  - It is not the obvious first calculation on the given numbers.
  - On a problem like "how many…", a solver who tries blind small cases should not be able to read it off (B4).
- **A7. Checker behaviour.** The checker accepts any equal form, so `25/4`, `6.25` and `6.250` all pass. "In lowest terms" tells the solver what to aim for; the checker doesn't enforce it. Don't write a problem where the form is what matters.

## 4. Solution rules

- **M1. Shortest complete solution first.** Other routes follow under `<b>Solution 2.</b>` and so on.
- **M2. Every step is justified.** Routine algebra may be skipped. A named theorem may be cited, but a less well-known lemma needs a proof or a one-line reason.
- **M3. The final answer is stated clearly,** at the end and in the exact form of the key, including the encoded value under A4.
- **M5. Tags.** `subtopics` use taxonomy IDs and never entries marked `legacy`.
- **M6. Independent check.** A draft's `check_program` computes the quantity from the problem's definitions, not from the solution's formula (task 05).
- **M7. No appeal to the program.** The written solution stands by itself.
- **M8. Style.** Solutions read like a strong olympiad student's write-up: direct and concise, with no narration, no restating the problem and no signposting. The words "key idea", "key insight", "crux", "elegant", "beautiful", "the trick", "the heart of", "delicate", "we only need", "note that", "it remains" and "therefore each", the phrase "why this works" and em dashes are banned in solutions, hints and rubrics. Lemma, Claim, Remark and Theorem are used only where they help.
- **M9. Length follows difficulty.** 8–7 kyu: 1 to 4 lines. 6 kyu: up to about 80 words. 5–4 kyu: up to about 150. 3 kyu and proofs: as long as rigour needs and no longer.

**Worked example (5 kyu).**

> **Consecutive product.** How many integers $n$ with $1 \le n \le 999$ are such that $n^2 + n$ is divisible by $20$?
>
> **Hint 1.** Factorise $n^2 + n$ and split $20$ into coprime parts.
>
> **Hint 2.** Since $n$ and $n + 1$ are coprime, each prime power in $20$ must divide just one of them. This is the Chinese remainder theorem at work.
>
> **Hint 3.** Combine the conditions modulo $4$ and modulo $5$ into residues modulo $20$, then count up to $999$.
>
> **Solution.** We have $n^2 + n = n(n + 1)$ with $n$ and $n + 1$ coprime. So $4$ divides it exactly when $n \equiv 0$ or $3 \pmod 4$, and $5$ divides it exactly when $n \equiv 0$ or $4 \pmod 5$. By the Chinese remainder theorem this gives four residues modulo $20$: $0, 4, 15, 19$. Now $999 = 49 \cdot 20 + 19$. The $980$ integers from $1$ to $980$ contain $49 \cdot 4 = 196$ solutions, and $981$ to $999$ have residues $1$ to $19$, which contain $3$ more. The answer is $199$.

## 5. Hint rules

- **H1. Two or three hints,** for every problem type, in order from gentlest to strongest.
- **H2. Hint 1 points at the right object:** the quantity, auxiliary point or small case to look at. It doesn't name the technique.
- **H3. Hint 2 names the technique.** With three hints, hint 2 names it and hint 3 applies it.
- **H4. The last hint stops one step short of the answer.** After it, one routine step remains. No hint states the final answer or, on a proof, finishes the proof.
- **H5. Each hint adds something.** A hint that only restates the statement or the previous hint fails.
- **H6. Hints stand alone in order.** Hint 2 can't assume the solver worked out what hint 1 was hinting at without saying it again where needed.

## 6. What makes a problem bad

Each of these fails review, whatever the checks say.

| ID | Defect | Example | Why it's bad |
|---|---|---|---|
| **B1** | Number swap of a known problem | The seed `square-hunting`: the gate found a near-duplicate of a corpus problem, at similarity 1.00. The seed `the-13-14-15-triangle` is a well-known exercise | It teaches nothing new, and it breaks rule 2 of `tasks/README.md` |
| **B2** | A computation slog with no idea | "Find the sum of the squares of the first $40$ odd numbers, then the same for the even numbers, and subtract." | The only skill tested is accuracy. Difficulty must come from an idea |
| **B3** | Ambiguity | "How many integers are between $3$ and $10$?" | Solvers who get it right can be marked wrong. Fix it with $3 < n < 10$ |
| **B4** | Blind small cases find the answer | "Lines in general position: how many regions do $n$ lines make?" with a small $n$ | Drawing it gets the answer with no idea. Set $n$ too large to draw, and make the pattern not the obvious one |
| **B5** | The "trick" is the wording | "A farmer has $17$ sheep and all but $9$ die. How many are left?" | It rewards a reading habit, not mathematics |
| **B6** | Kyu and difficulty don't match | The seeds `factorial-sandwich` (rated 3 kyu; the gate estimated 6) and `round-table-no-neighbours` (rated 4 kyu; the gate estimated 7) | The rank loses its meaning. This evidence is weak: it comes from the same provisional ruler that queries three of this document's own examples (section 10), and these seeds are well-known problems, which makes them look easier. Reviewers decide |
| **B7** | A one-step exercise presented as a problem | The seed `divisor-census`, or `zeros-of-2026` | Fine as a textbook drill, but below even 8 kyu's bar if it is only a formula |
| **B8** | Quoted contest text | The seeds `floor-staircase`, `factorial-sandwich`, `prime-power-desert`, `vieta-leap` | These quote contest problems, which rule 1 forbids. Task 11 removes them |
| **B9** | A title that gives it away | The seeds `vieta-leap` and `nesbitts-guard` | It removes the crux before the solver starts (S13) |
| **B10** | Too loose about the answer | The seed `circle-in-the-square`: "A fraction or a decimal is fine." | It should state one target form (S3) |

The full list of why each seed fails is in `pipeline/verify/SEED_VERDICTS.md` on the task 05 branch.

## 7. Originality

**O1. What a reskin is.** A reskin keeps the same mathematical structure and solution path and changes only the setting, names or numbers. Sharing a technique is not a reskin. This is the same definition the task 05 judge uses.

**O2. Why changing the setting and numbers is not enough.** A solver who knows the original solves the reskin in the same way, without a new thought. Turning a sum about a staircase into a sum about laps of a track changes the story, not the problem. A new problem has to change what the solver has to *do*: ask for what was given, move the idea to a different object, combine it with a second idea, or make a different route the natural one. Those are the variation recipes in task 06.

**O3. What the gate enforces**, in words:

1. **Near-copies fail automatically.** If a draft's wording is more similar to any corpus or bank problem than the fitted limit, it fails with no judge involved. The limit is in `pipeline/verify/similarity.json` and is refitted as the corpus grows, so it isn't repeated here. It sits above the most similar honest pair of problems sharing a technique, so it catches copies, not reskins.
2. **A judge examines the nearest problems.** It looks at the five nearest problems plus the draft's own inspiration. Any reskin verdict fails.
3. **Known problems fail.** The same judge asks whether the draft is, up to setting and numbers, a specific published contest problem, a named classic or a well-known puzzle. Several seeds fail this way (`domino-corridor`, `the-13-14-15-triangle`). A generic technique exercise with no recognisable source passes.

**O4. Set `inspired_by` on every generated draft.** Word matching misses a reskin in a new setting, so that field is what guarantees the judge sees the source.

**O5. The inspiration stays private.** The mapping lives in the private corpus repo, never in a public field.

**O6. What the gate can't do.** Reviewers must watch for these:

- A routine exercise in a story passes the gate, as the fixture `reskin-gauss` shows. Reviewers reject these as stale under B7.
- The judge isn't fully repeatable on borderline cases. A verdict that flips between runs counts as a reskin.
- At 8–6 kyu, simple problems have few possible structures, and the judge can be strict. Sharing a one-step structure with a contest problem is not, by itself, a reskin at those kyus (D7). Task 08 should measure how often this rejects honest drafts.

**O7. Classical problems** are outside this section. Only book problems and problems Kevin has individually allowed may be `classical`. See the open decisions in `tasks/README.md`.

## 8. Proof problems (3–1 kyu)

### 8.1 A well-posed olympiad statement

- **P1. One claim.** "Prove that…" or "Determine all…". For "determine", the answer is unique and its form is clear.
- **P2. "Determine" includes both directions.** The model solution shows the answer works and that nothing else does.
- **P3. True, and tested.** The statement is checked for counterexamples, by computer where possible and for geometry on exact or high-precision random configurations (task 09).
- **P4. No degenerate cases left to chance.** Conditions like $AB \ne AC$ or "acute" are there because the statement needs them. Say whether points lie on sides or on lines. Don't add a condition the proof doesn't need, because it hints at the proof.
- **P5. Natural.** The statement reads as one idea, not as a problem bolted together. A solver should want to know why it is true.
- **P6. All routes are fair.** Coordinates and other computational approaches are allowed, and the rubric must be able to credit them.

### 8.2 The model solution must include

- **P7.** A complete, rigorous proof with all cases, written so that a competent reader needs no filling-in.
- **P9.** A short Remark giving another route, where one exists.
- **P10.** Lemmas that aren't standard are proved in full. Standard theorems are cited by name.

### 8.3 The seven-mark rubric

- **P12. Totals 7.** Each line has marks from 1 to 7.
- **P13. Marks follow milestones.** Each line is a mathematical achievement a marker can see in a script, not a section of the model solution. Marks go to the hardest ideas, so the crux gets the most.
- **P14. Route-independent.** Lines are worded by what has been achieved. Add "or an equivalent" where other routes exist.
- **P15. Answers alone earn little.** On "determine" problems, the correct answer without proof earns at most 1. Stating or checking small cases earns nothing unless a line says so.
- **P16. Deductions go inside the line they apply to,** because the schema has only `marks` and `criterion`: "Deduct 1 if the case $X = C$ is missing." Allow at most one deduction per line, and never take a line below 0 (D11).
- **P17. Common errors are named** as deductions: a missed case, assuming a configuration, circular use of the claim.
- **P18. Tested.** The rubric is tried on two deliberately flawed proofs, which should score in the expected range (task 09).
- **P19. Calibrated to these bands.** 7 is complete; 6 is complete with a small gap; 3–5 is real progress past the crux or close to it; 1–2 is useful but well short of it; 0 is nothing useful.

### 8.4 Hints on proofs

Rules H1 to H6 apply. "One step short" (H4) means one routine step short of a complete proof *idea*; the writing-up still remains.

### 8.5 Worked example (3 kyu)

> **A parallelogram and two tangents.** Let $ABC$ be an acute triangle with circumcircle $\Gamma$. Point $X$ lies on line $AC$ with $XA = XB$, and point $Y$ lies on line $AB$ with $YA = YC$. Let $P$ be the point for which $AXPY$ is a parallelogram. Prove that lines $PB$ and $PC$ are tangent to $\Gamma$.
>
> **Hint 1.** Do not start from $P$. Start from the point where the tangents at $B$ and $C$ meet, and call it $T$.
>
> **Hint 2.** Angle-chase with directed angles to show that $T$, the circumcentre $O$, $B$, $C$ and $X$ all lie on one circle.
>
> **Hint 3.** That circle has diameter $OT$, so $\angle OXT$ is a right angle. Use this together with the fact that $OX$ is perpendicular to $AB$.
>
> **Solution.** Let $O$ be the circumcentre and let $T$ be the meeting point of the tangents to $\Gamma$ at $B$ and $C$, which exists because angle $A$ is not right. Since $\angle OBT = \angle OCT = 90^\circ$, points $B$ and $C$ lie on the circle $\omega$ with diameter $OT$.
>
> Use angles between lines, taken modulo $180^\circ$. First suppose $X \ne C$. Triangle $XAB$ is isosceles, so $\angle(XB, XC) = \angle(XB, XA) = 2\angle(AB, AC)$, and also $\angle(OB, OC) = 2\angle(AB, AC)$. Hence $X$ lies on $\omega$. Since $XA = XB$, point $X$ is on the perpendicular bisector of $AB$, so $OX \perp AB$. Note $X \ne O$, because $O$ is strictly inside an acute triangle and so not on line $AC$. As $X$ is on the circle with diameter $OT$, either $X = T$ or $XT \perp OX$, and in both cases the line through $X$ parallel to $AB$ passes through $T$. If $X = C$, then $CA = CB$, so the tangent at $C$ is parallel to $AB$, and again the line through $X$ parallel to $AB$ passes through $T$.
>
> In the same way, the line through $Y$ parallel to $AC$ passes through $T$. The point $P$ is the intersection of the line through $X$ parallel to $AB$ and the line through $Y$ parallel to $AC$, and these two lines are not parallel. So $P = T$, and $PB$ and $PC$ are tangent to $\Gamma$.

| Marks | Criterion |
|---|---|
| 1 | Introduces $T$, the meeting point of the tangents, and aims to show $P = T$, or an equivalent reformulation. |
| 3 | Proves that $X$ lies on the circle through $B$, $O$, $C$ and $T$, or an equivalent. Deduct 1 if only one position of $X$ is handled and the argument does not extend to the other. |
| 2 | Deduces that the line through $X$ parallel to $AB$ passes through $T$. |
| 1 | Applies the same argument to $Y$ and concludes that $P = T$. |

A complete proof by another route, including coordinates or complex numbers, earns 7.

## 9. Open decisions for Kevin

Each has a default that this document already uses, so nothing is blocked. Changing one means changing the rule named.

| # | Question | Default used here | Why it needs you |
|---|---|---|---|
| **D1** | Can proofs appear below 3 kyu? | No. MOHS 0–5 and easy UKMT or BMO1 problems only calibrate 4 kyu (K4) | The brief says proofs are 3–1 kyu, but task 03 puts MOHS 0–5 at 4 kyu and task 02 has UKMT olympiads at 5–3 |
| **D2** | Can answer problems be 2 kyu? | No. The hardest answer problems stay at 3 kyu (K4, A1) | The first pass already rates 8 AIME problems at 2 kyu, and the brief's answer rules stop at 3 kyu |
| **D3** | Do you accept the contest anchors marked [P], including the book references in that column of 1.6? | Yes, as a draft, until waves 2 and 3 test them | The task 03 table has no UKMT, HMMT, BMO, USAMO, EGMO or CGMO rows, though the brief asks for them |
| **D4** | Should 5 kyu's AIME anchor move? | Keep AIME 1–5 at 5 kyu and recheck after the second pass | 59% of modern AIME 1–5 landed at 6 kyu in the first pass. If that holds, task 06's "5–3 kyu from AIME" needs rethinking |
| **D5** | Allow AIME-style encoded answers at 5–3 kyu? | Yes (A4) | The brief's 0–999 rule would otherwise rule out every non-integer answer at those kyus |
| **D6** | What happens to `answer_format: "expression"`? | Unused, left in the schema (A2) | Removing it is a schema change for task 01's owner |
| **D7** | How strict is originality at 8–6 kyu? | A shared one-step structure is not by itself a reskin (O6) | The gate's judge currently rejects these. Stricter rules could make 8 kyu very hard to fill |
| **D8** | "Incentre" or "incenter"? | UK in prose. Taxonomy IDs and the book's title keep their spelling (S8) | Your book and the taxonomy use the US form, and the brand sheet asks for UK |
| **D9** | Do bosses and 1 kyu geometry need invented examples? | No. Both use book problems instead, which departs from the brief (section 1.5) | Bosses are chosen from your book. No invented problem here reached the book's 1 kyu geometry. You may prefer to name other references |
| **D10** | May the examples here enter the bank? | No. They're published here with their answers | Otherwise they would need new wording and the gate |
| **D11** | Should the schema get a separate deductions field? | No. They go inside `criterion` (P16) | Task 16's marker would find a separate field easier to apply. It's a schema change |
| **D12** | Is the title rule right? | Yes (S13). IDs are permanent, so it only applies to new problems | It's an addition to the brief, and some community authors may find it restrictive |
| **D13** | Are the examples at the right kyu? | Yes, as the author's estimate. The gate rates three of them easier (section 10). I moved two geometry proofs down one kyu against the book's references (1.6), which are my reading of them and not yours. The proofs are unmeasured and have not been compared with an olympiad corpus | Only you, or real solvers, can judge. Your acceptance of the ladder depends on these |

The decisions already listed in `tasks/README.md` remain open: showing inspirations (the default here is no, see O5), famous problems outside the book (default: not used, see O7) and how much of a book solution a beaten boss shows.

## 10. The examples through the gate

Every example went through the real gate (task 05 branch at `8d13ea6`, with the private corpus) so that the standard's own examples meet it. It used 260 model calls on Kevin's plan, about $3.27 at API list prices. That measures usage; no money was spent.

| Kyu | Example | Verdict | Blind solves | Estimated kyu |
|---|---|---|---|---|
| 8 | Sticker packs | PASS | 7/7 | 7 |
| 8 | Patio border | PASS | 7/7 | 8 |
| 7 | Squares through a cell | PASS | 7/7 | 7 |
| 7 | Number machine | PASS | 7/7 | 7 |
| 6 | Circle on the hypotenuse | PASS | 7/7 | 7 |
| 6 | Rising digits | PASS | 7/7 | 7 |
| 5 | Consecutive product | PASS | 7/7 | 6 |
| 5 | A sum below twenty | INVESTIGATE: difficulty | 7/7 | 7 |
| 4 | Bisector to the circle | INVESTIGATE: difficulty | 7/7 | 6 |
| 4 | Powers of two in powers of three | INVESTIGATE: difficulty | 7/7 | 6 |
| 3 | No doubles and no triples | PASS | 6/7 | 3 |
| 3 | A parallelogram and two tangents (proof) | PASS | n/a | n/a |
| 3 | Four points and a diameter (proof) | PASS | n/a | n/a |
| 2 | Infinitely many divisors (proof) | PASS | n/a | n/a |
| 2 | Three lines and a side (proof) | PASS | n/a | n/a |
| 1 | Lamps to all on (proof) | PASS | n/a | n/a |

**What this does and doesn't show.**

- **The three INVESTIGATE results are not failures,** but they may be right. The gate rates all three two kyus easier than the target. Its ruler is provisional and weak in this range, since models also solve nearly all real AIME problems 7/7. A reviewer should still look at these first.
- **Originality was only tested against what the corpus holds.** The gate's corpus so far has AMC, AIME and AHSME and no olympiads, so the proofs were compared with olympiad problems only through the judge's memory. They could still match a real olympiad problem.
- **Proofs skip the blind solves and the difficulty check,** so a PASS there means only that the critics, solution audit and originality judge found nothing. Task 09's truth checks did not run. Separately: the lamp answer was confirmed by exhaustive search for odd $n \le 19$ and the construction by replaying its moves for odd $n \le 41$, and the three geometry statements were checked numerically on random triangles.
- **The gate rejected seven earlier examples, and that was useful.** Five of my first answer problems were judged reskins or known problems, one was ambiguous about single-digit numbers, and one proof had a real error in its construction, now fixed. All were written by hand, in good faith, without looking at the corpus. Tasks 06 and 08 should expect the same at low kyu, where familiar structures are hard to avoid (D7).

## Appendix A. Which rules can be checked, and how

- **Auto** is a regex or a calculation, with no model call.
- **Judge** needs a model prompt.
- **Human** is for the reviewer in task 07.

"Gate" says what the task 05 branch (`claude/task-05-gate-018b5b`, `pipeline/verify/`) does today. Gaps are for task 05 to close. This standard doesn't implement checks.

| Rule | Check | How | Gate today |
|---|---|---|---|
| K4 | Auto | Proof only at 3–1 kyu; answer only at 8–3 kyu | **Gap.** A proof at 5 kyu or an answer at 2 kyu passes |
| K1, K2, K3, K5 | Judge, human | Difficulty estimate plus review | Partly: `difficulty` for 8–3 kyu only, provisional. Treat it as "warm-up or not" until the full fit |
| S1 | Judge, with an Auto lint | No "(a)", "(b)"; at most one question mark | **Gap.** Not named in the `WELL_POSED` prompt |
| S2 | Judge | Well-posedness critic | Covered: `well_posedness` |
| S3 | Auto | `rational` format or encoded answer needs a format sentence in the statement | **Gap** |
| S4 | Judge | Critic | Partly. "Hidden cases" isn't named in the prompt |
| S5 | Judge | Critic | Partly: "genuine alternative reading". Reading tricks aren't named |
| S6 | Judge | Critic | **Gap.** Not named in the prompt |
| S7 | Judge | Critic | Partly |
| S8 | Auto | Word list on prose, with maths and `<code>` removed | Partly. See gaps 1 to 3 below |
| S9 | Auto | Lint for `*`, bare `\frac12`, `\frac` inside `$$…$$`, `\leq` | **Gap.** The MathJax dry run only checks it compiles |
| S10 | Auto | No Markdown bold, backticks or list markers | **Gap** |
| S11 | Judge | Blind solves see only words and `figure_alt` | Covered in effect by `blind_solves` |
| S12 | Auto | Contest-name and ID regex | Partly. Statement, solution and hints only; not title or rubric |
| S13 | Auto, human | Title and new IDs contain no taxonomy ID or theorem name | **Gap** |
| S14 | Human | Review | None needed |
| A1 | Auto | Format and range by kyu | Partly. Range at 5–3 kyu is checked; format against kyu isn't, and neither is the limit of $10^9$ |
| A2 | Auto | Reject `expression` | **Gap.** The range check is skipped when the answer isn't numeric |
| A3 | Auto | Parse and test digit counts | **Gap** |
| A4 | Judge | Encoding isn't the hard part | **Gap** |
| A5 | Auto, judge | Check program plus blind solves and critic | Covered: `computational`, `blind_solves`, `well_posedness` |
| A6 | Auto, judge | Answer 0 or 1 fails; answer appears in the statement fails; guessability judged | Partly. 0 or 1 is only a warning, and the others are missing |
| A7 | None | A fact about the checker | |
| M1, M2 | Judge | Solution audit | Covered: `solution_audit` |
| M3 | Auto | Key appears in the solution's last paragraphs | Partly. A warning, and it searches the whole solution |
| M8 | Auto | Banned-word regex on solution, hints and rubric | Covered: `standard` |
| M9 | Human | Length by kyu, also in the write prompts | None needed |
| M5 | Auto | Subtopics in taxonomy, none `legacy` | Partly. `validate.mjs` checks membership once the taxonomy lands, not `legacy` |
| M6 | Judge | Program judge | Covered: `program_judge` |
| M7 | Judge | Audit | Covered in effect |
| H1 | Auto | Two or three hints | Partly. Only answer problems are checked |
| H2, H3, H5, H6 | Judge | New hint judge | **Gap.** No model looks at the hints |
| H4 | Auto, judge | Literal answer not in hints; judge for "one step short" | Partly. The literal check skips one-digit answers, and there's no judge |
| B1 | Judge | Originality | Covered: `originality` |
| B2 | Judge, human | New prompt, plus token use from blind solves | **Gap** |
| B3 | Judge | Critic | Covered: `well_posedness` |
| B4 | Judge, human | Could a blind small-case pattern give it? | **Gap** |
| B5 | Judge | Critic | Partly |
| B6 | Judge | Difficulty | Partly, as for K1 |
| B7 | Judge, human | Review | **Gap,** as `reskin-gauss` shows |
| B8 | Auto, judge | Classical with a contest source fails | Covered: `originality` |
| B9 | As S13 | | **Gap** |
| B10 | As S3 | | **Gap** |
| O1, O3 | Auto, judge | Threshold, then judge | Covered: `originality_lexical`, `originality` |
| O4 | Auto | `inspired_by` present on generated drafts | **Gap.** Optional in the gate; task 06 must always set it |
| O5 | Auto | Private ID absent from public text | Covered: `standard`, and the corpus-text scan |
| O6 | Human | Review | Known limits, documented in the gate's README |
| P1–P6 | Judge | Critic and task 09's gate | Partly. Proofs get `well_posedness`, `solution_audit` and `originality`; truth testing is task 09's |
| P7–P10 | Judge | Audit | Partly: `solution_audit`. P9 isn't checked |
| P12 | Auto | Total is 7 | Covered: `validate.mjs` |
| P13–P19 | Judge, human | Task 09's rubric check | Task 09 |
| BS1–BS5 | Human | Kevin | Task 21 |

### Gaps worth fixing first

1. **The spelling check splits taxonomy IDs on hyphens.** `standard.py` removes maths but not `<code>`, so a bare ID such as `perpendicular-from-center-to-chord` fails on "center". Remove `<code>…</code>` before checking.
2. **The word list misses the geometry terms.** Add incenter, circumcenter, orthocenter and excenter. It must then allow the book's title.
3. **The scan misses some fields.** `title`, `rubric[].criterion` and `figure_alt` aren't checked for spelling or contest names.
4. **Kyu and type aren't cross-checked** (K4, A1).
5. **Hints on proofs aren't counted** (H1), and no judge reads any hint (H2–H6).
6. **`WELL_POSED` doesn't name** one question, hidden cases, reading tricks or cultural knowledge. Adding them is one sentence.
7. **Answer checks are weak:** 0 or 1 only warns, and an answer that appears in the statement isn't noticed (A6).

## Appendix B. Evidence

- **Calibration table and era rule:** `tasks/03-corpus-analysis.md`, and the task 03 first-pass prompt.
- **First-pass statistics:** computed from `corpus/analysis_runs/full/pass1/` in the private corpus analysis, 248 records, 30 October 2026. They are aggregates only.
- **Taxonomy:** version 1.0.0, approved by Kevin on 30 October 2026. It is at commit `32e43c0` on the task 03 session's local branch, not yet pushed when this was written. All IDs in this document are in it.
- **Gate:** `claude/task-05-gate-018b5b` at commit `8d13ea6`, not yet merged.
- **Book:** the manuscript of *Beyond the Incenter*, 2026 edition, read on 30 October 2026. It isn't in this repo. References are by source credit, because the book's numbering is not used here.
