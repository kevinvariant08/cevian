# 09. Build the proof-problem pipeline (3–1 kyu)

## Goal
Build a bank of original olympiad proof problems for 3, 2 and 1 kyu, inspired by the best of BMO1, BMO2, USAJMO, USAMO, EGMO, CGMO, APMO, RMM, the IMO and the IMO Shortlist. Each comes with a model solution and a seven-mark rubric. Target: **60 at 3 kyu, 40 at 2 kyu and 20 at 1 kyu** to start with. Kevin's book supplies a separate boss tier above these (task 21). Quality matters far more than quantity here: one wrong 1 kyu problem damages trust more than a hundred good 5 kyu ones.

## Depends on
02 wave 3 and 03 (the olympiad corpus, analysed), 04 (the standard, including the proof section), 06 (the generator, to reuse) and 07 (review queue).

## Read first
- `docs/problem-standard.md` §8, `tasks/README.md` and the open decision in it about famous problems.
- Kevinvariant's Proof marker (`kevinvariant08.github.io/marker.html` and its repo) for how it prompts a model to mark written solutions. Reuse what works.

## Spec
1. **Inspirations.** Use the wave 3 corpus from task 02 with its task 03 analysis. For proof problems, add a `proof_skeleton` field to the analysis: the key lemma, construction or invariant, in abstract form. Use the MOHS and ISL positions to choose the kyu.
2. **Balance.** Keep the four topics roughly even at each kyu. Geometry gets extra care, because Kevin is a geometry specialist and reviews it most closely (see task 21).
3. **Two sources of problems:**
   - **Original.** Generate with `claude-opus-5-5` from a `proof_skeleton` and a variation recipe (task 06). The output is the statement, the model solution and the rubric.
   - **Classical, if Kevin allows it.** Famous problems, restated in Cevian's own words with attribution in `provenance`, such as IMO 1988 P6 or Erdős–Ginzburg–Ziv. Each needs Kevin's explicit OK.
4. **Verification.** Answers can't be checked, so the gate is different:
   - **Truth.** Three independent attempts to *disprove* the statement: a search for counterexamples with a computer where that is possible (for example, checking number-theory claims up to 10⁶), plus a model looking for a counterexample.
   - **Solvability.** Three independent blind proof attempts. At least one must be judged complete by a separate marker using the rubric. If none succeeds, either the problem is too hard or the statement is wrong, so flag it.
   - **Solution audit.** A critic checks the model solution line by line.
   - **Rubric check.** The rubric totals 7 and awards partial credit for real milestones. Test it by marking two deliberately flawed proofs: they should score in the expected range.
   - **Originality.** As in task 05, against the proof corpus.
5. **Review.** Every proof problem needs Kevin's sign-off in the task 07 queue. Show the counterexample search, the blind attempts and their marks.

## Acceptance criteria
- 120 approved proof problems (60 / 40 / 20 across 3 / 2 / 1 kyu), or fewer if quality demands it, with the shortfall explained.
- For each one there are counterexample-search logs, at least one blind proof marked complete, and a rubric that has been tested.
- Kevin has signed off every problem individually.

## Out of scope
Submitting and peer-reviewing users' proofs on the site (task 16).
