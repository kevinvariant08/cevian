# 03. Analyse the contest corpus thoroughly

## Goal
Understand every corpus problem well enough to teach from it: what it is really about, every route to a solution, where solvers go wrong, and exactly how hard it is. Then find the patterns across the whole corpus. Generation (06, 08, 09) imitates the ideas recorded here, the problem standard (04) calibrates against them, and the verification gate (05) uses them to reject copies.

This is the task that decides whether Cevian problems feel like real contest mathematics, so depth matters more than speed.

## Depends on
02. Run it per wave: the AIME first as a pilot, then the answer-based contests, then the olympiads.

## Read first
- `tasks/README.md` (rules) and `tasks/02-contest-corpus.md` (record format).
- `mathwars-corpus/corpus/*.jsonl`.

## Deliverables

### 1. A controlled vocabulary: `cevian/data/taxonomy.json` (public, no problem text)
- Topics: `A`, `C`, `G`, `N`.
- **Techniques**, about 120–200 of them, each with a one-line definition and its parent topic. Examples: `vieta`, `telescoping`, `roots-of-unity-filter`, `inclusion-exclusion`, `bijection`, `double-counting`, `invariant`, `monovariant`, `extremal-principle`, `expected-value-linearity`, `pigeonhole`, `power-of-a-point`, `radical-axis`, `spiral-similarity`, `harmonic-bundles`, `inversion`, `complex-bash`, `barycentric-bash`, `trig-ceva`, `lte`, `zsigmondy`, `crt`, `orders-mod-n`, `quadratic-residues`, `vieta-jumping`, `smoothing`, `sos`, `tangent-line-trick`, `functional-equation-substitution`, `cauchy-fe`.
- **Geometry configurations** as a separate list, for example `incenter-excenter-lemma`, `mixtilinear-incircle`, `nine-point-circle`, `complete-quadrilateral`, `miquel-point`, `symmedian`, `orthocenter-reflection`.

Build both bottom-up from the corpus, then merge near-duplicates. Get Kevin's approval before the full run, since he is a geometry specialist (see task 21).

### 2. A per-problem analysis: `mathwars-corpus/corpus/<exam>_analysis.jsonl` (private)
```json
{"id":"ISL-2019-G7",
 "topic":"G","techniques":["spiral-similarity","radical-axis"],"configurations":["miquel-point"],
 "core_idea":"An abstract one-to-three sentence description, with no numbers or story from the problem.",
 "solution_paths":[
   {"name":"synthetic via spiral similarity","key_steps":["...","..."],"difficulty_of_path":"hard"},
   {"name":"complex numbers","key_steps":["..."],"difficulty_of_path":"medium but long"}],
 "crux":"The single step that makes the problem hard.",
 "traps":["The natural first attempt X fails because ..."],
 "prerequisites":["power-of-a-point"],
 "solution_length":"short|medium|long","computation_load":"low|medium|high",
 "kyu":2,"kyu_reason":"ISL G7; MOHS 40; one deep crux plus a long finish",
 "generation_potential":"high|medium|low","generation_note":"Why this idea can (or can't) be transplanted."}
```
- `core_idea` and `crux` must be abstract enough to describe a **family** of problems, not this one.
- Write `solution_paths` from **all** the solutions collected in task 02, not only the official one. Different routes are what let generation vary a problem.
- `generation_potential` flags ideas that are too tied to one specific setting to reuse.

### 3. Kyu calibration from difficulty data
Start each problem's kyu from its contest position, then adjust using MOHS and the official statistics:

| Signal | 8 | 7 | 6 | 5 | 4 | 3 | 2 | 1 |
|---|---|---|---|---|---|---|---|---|
| AMC 8 position | 1–10 | 11–20 | 21–25 | | | | | |
| AMC 10/12 position | | 1–10 | 11–20 | 21–25 | | | | |
| AIME position | | | | 1–5 | 6–10 | 11–15 | | |
| MOHS | | | | | 0–5 | 10–15 | 20–30 | 35+ |
| IMO / ISL | | | | | | P1/P4, ISL x1–x2 | P2/P5, ISL x3–x5 | P3/P6, ISL x6+ |

Adjust by at most one kyu from the starting value, and give a reason. Record disagreements between signals, since they are useful for task 05's difficulty model.

### 4. The analysis method
1. Run `claude-opus-5-5` with structured output against the taxonomy. Give it the statement and **every** collected solution.
2. Run a second pass with a different model on 15% of records. For olympiad geometry, run it on **all** records, because configuration tagging is error-prone. Record and resolve disagreements.
3. Have Kevin review the 30 records with the largest disagreements, plus 20 at random.

### 5. Cross-corpus synthesis: `cevian/docs/corpus-analysis.md` (public, no problem text)
- Topic and technique frequency by kyu band, and how it changes over the 15 years.
- What separates adjacent kyus in concrete terms: the number of non-routine steps, how hidden the crux is, the computation load, and whether there is more than one viable path.
- **Idea families:** clusters of problems that share a `core_idea`, with sizes and kyu spread. Generation should sample across families, not repeat the biggest ones.
- **Gaps:** techniques and configurations that appear rarely, where generation must take care.
- **A geometry deep-dive:** the most common configurations at each kyu. This is input for task 21's boss ladder.

## Acceptance criteria
- Every corpus problem has a valid analysis record that matches the taxonomy.
- Kevin accepts at least 85% of the 50 records he reviews.
- Disagreement between the second-model check and the first pass is under 10% on topic and under 25% on techniques, with every disagreement resolved.
- The synthesis report exists and contains no problem text.

## Out of scope
Generating problems.
