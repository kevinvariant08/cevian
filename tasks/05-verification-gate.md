# 05. Build the verification gate

## Goal
Build a command-line tool that every new problem must pass before a human sees it, so that wrong answers, ambiguous statements, mis-rated difficulty and disguised copies of contest problems never reach the bank. This is the most important piece of the content pipeline: it is the reason generated problems can be trusted.

## Depends on
01, for the problem schema. It uses the 03 corpus for novelty checks when that is available, and works without it until then.

## Read first
- `schema/problem.schema.json`, `tasks/README.md` and `docs/problem-standard.md` (once task 04 lands).

## Deliverables
`pipeline/verify/` in this repo. The code is public; it calls the private corpus through a path set in an environment variable, `CEVIAN_CORPUS`.

```
python -m pipeline.verify draft.json [--report out/report.json]
```

A draft is a problem JSON (task 01 schema) with three extra fields: `answer` (plain), `check_program` (Python source) and `inspired_by` (corpus ID, private).

### Checks, in order (stop at the first hard failure)
1. **Schema.** The draft validates, and the LaTeX renders (a MathJax dry run).
2. **Computational truth.** Run `check_program` in a sandbox with no network, a 60-second time limit and only `sympy`/`numpy`/the standard library available. It must compute the answer **independently of the written solution**: by brute force, exact enumeration or a symbolic computation, not by restating the formula. Its output must equal `answer`. A judge prompt also checks that the program really searches or computes rather than hard-coding the answer. Geometry may use exact coordinates with sympy.
3. **Blind solves.** Run five independent solves with `claude-sonnet-5-5`, given the statement only, with no solution, hints or answer, plus two with a model from a different family. Record each answer and the number of reasoning tokens used.
   - **Pass** if at least 4 of the 7 agree with `answer`.
   - **Investigate** if the majority answer differs from `answer` and agrees with itself. That points to a wrong key or an ambiguous statement.
   - **Too easy** if all 7 solve it with very few tokens and the target kyu is 5 or higher.
4. **Well-posedness review.** A `claude-opus-5-5` critic gets the statement and solution and lists any ambiguity, missing condition, alternative reading or unstated assumption. Any finding is a fail, unless it is marked cosmetic.
5. **Solution audit.** A critic checks that every step of the written solution is justified and that it reaches `answer`.
6. **Difficulty estimate.** Map the blind-solve rate and token use to a kyu, using thresholds fitted on the task 03 corpus: run steps 3 and 6 on 60 corpus problems of known kyu and fit the mapping. Fail if the estimate is more than one kyu from the target.
7. **Originality.**
   - Embed the statement and the abstract `core_idea`. Compare against every corpus record and every problem already in the bank.
   - Have a judge examine the five nearest neighbours: "Is the new problem a reskin of this one, meaning the same structure with a changed setting or numbers?"
   - Any reskin verdict fails. A similarity threshold above which it fails automatically is fitted by testing deliberate reskins (make 20) against genuinely different problems on the same technique (make 20).
8. **Standard rules.** Check the automatable rules from `docs/problem-standard.md`: answer range, hint count and order, UK spelling and so on.

### Outputs
- `out/report.json`, which holds each check's result, the evidence, model IDs, token counts and cost.
- A one-line verdict: `PASS`, `FAIL <check>: <reason>` or `INVESTIGATE`.
- A `--batch dir/` mode that runs many drafts in parallel, with a concurrency limit and a cost summary.

## Acceptance criteria
- A test suite of about 40 drafts with known verdicts, made by you, passes. It should include:
  - Correct problems.
  - Problems with a wrong answer key.
  - An ambiguous statement.
  - A `check_program` that hard-codes its answer.
  - A reskin of a famous problem.
  - A problem that is too easy for its kyu.
- Running it on the 21 current seed problems gives a reasoned verdict for each. Some should fail on originality, and that is expected.
- One problem costs less than an agreed amount: report the actual figure, and Kevin sets the limit.

## Out of scope
Generating problems (06). The review UI (07).
