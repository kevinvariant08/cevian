# 04. Write the Cevian problem standard

## Goal
Write one document that defines a good Cevian problem at each kyu. The generator (06, 08, 09), the verification gate (05), the reviewers (07) and community authors (17) all follow it. The current seed problems fail it, and that is the point.

## Depends on
03, which supplies the calibration data.

## Read first
- `docs/corpus-analysis.md` and `data/taxonomy.json` from task 03.
- The current problems in `data/problems/` (after task 01) or in `index.html`, to use as examples of what to avoid.

## Deliverable
`docs/problem-standard.md`, covering:

1. **The kyu ladder in detail.** For each of 8 → 1 kyu, plus the boss tier (task 21): the contest anchors (AMC/UKMT/AIME/HMMT positions for answer problems; BMO, USAMO, EGMO, CGMO, ISL positions and MOHS for proofs), the number of non-routine steps, how hidden the crux is, the computation load, the expected solve time for a solver at that rank, and two invented example problems with one-line reasons. Base every claim on the task 03 calibration table and synthesis report.
2. **Statement rules.** One question per problem. Every object is defined. The answer format is stated where it isn't obvious ("Give your answer as a fraction in lowest terms"). There is no hidden case-splitting, no reading tricks and no culturally specific knowledge. Use UK spelling. LaTeX conventions: `\dfrac` in display, `\cdot` for products and so on.
3. **Answer rules.** 5–3 kyu answers are integers from 0 to 999, as on the AIME. 8–6 kyu answers can be any integer or a simple rational. Every answer is unique, and it must not be guessable from the setup (no "the answer is 0 or 1").
4. **Solution rules.** Give the shortest complete solution first, with any alternatives after. Every step is justified. State the final answer clearly. Include a "Why this works" line naming the technique, using taxonomy IDs.
5. **Hint rules.** Two or three graded hints. Hint 1 points at the right object, and hint 2 names the technique. The last hint stops one step short of the answer.
6. **What makes a problem bad**, with examples: a number swap of a known problem, a computation slog with no idea, ambiguity, an answer that can be found by trying small cases blindly, a problem whose "trick" is the wording, or a mismatch between kyu and actual difficulty.
7. **Originality.** The thresholds task 05 enforces, in words: what "reskin" means, and why changing the setting and the numbers is not enough.
8. **Proof problems (3–1 kyu).** What a well-posed olympiad statement looks like, how to write a seven-mark rubric (partial-credit milestones, deductions), and what a model solution must include.

## Acceptance criteria
- Kevin reads it and approves it. This is a judgement call, so open the PR early.
- Each rule is checkable. Task 05 must be able to turn at least the statement, answer and originality rules into automated checks or judge prompts. List which rules are automatable in an appendix.

## Out of scope
Implementing the checks (05).
