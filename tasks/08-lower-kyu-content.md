# 08. Extend the pipeline to 8–6 kyu

## Goal
Fill the beginner and intermediate belts (8, 7 and 6 kyu) with original problems of the right difficulty, using the same corpus → analyse → generate → verify → review pipeline. Target: **at least 60 problems per kyu** across all four topics.

## Depends on
06 (generator) and 07 (review queue). It reuses 02–05.

## Read first
- Tasks 02, 03, 05 and 06, and `docs/problem-standard.md`.

## Spec
1. **Inspirations.** Use the wave 2 corpus from task 02 and its task 03 analysis at 8–6 kyu: AMC 8, early and middle AMC 10/12, UKMT JMC/IMC/SMC, MATHCOUNTS, and the easier HMMT and ARML problems. Sample across idea families and competitions, so that 8–6 kyu doesn't feel like a single exam.
2. **Answer format.** Lower-kyu Cevian problems are **free response**, not multiple choice. When the inspiration was multiple choice, the generated problem must still have a single, checkable answer and must not depend on the options for elimination.
3. **Difficulty calibration.** Refit the task 05 difficulty mapping with 8–6 kyu corpus examples. Weaker models solve these easily, so use a smaller model, `claude-haiku-5-5`, plus solve time as the signal. Document the method.
4. Then run generation, verification and review as in tasks 06 and 07: pilot 30, wait for Kevin's go-ahead, then the full run.

## Acceptance criteria
- At least 60 approved problems at each of 8, 7 and 6 kyu, with every topic at least 10 per kyu.
- The calibration report shows estimated versus target kyu on held-out corpus problems, with at least 80% within one kyu.
- No corpus text appears in the public repo.

## Out of scope
Proof problems. 5 kyu and harder, which task 06 covers.
