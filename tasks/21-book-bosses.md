# 21. Final bosses from *Beyond the Incenter*

## Goal
Turn the hardest geometry problems in Kevin's book, *Beyond the Incenter: A Collection of 100 Geometry Problems for Mathematical Olympiads* (2026 edition), into Cevian' **boss fights**: a gated tier above 1 kyu that strong players work towards. The rest of the book's problems become high-quality 3–1 kyu geometry and inspirations for generated problems.

## Depends on
01 (problem format) and 10 (figures). Players are marked by self-grading until 16 (proof review) lands. Use 03's analysis method for tagging.

## Read first
- `tasks/README.md`. Rule 1 has a deliberate exception for this book (see "Rights" below).
- The public sample chapter, `cross-ratios.pdf` in the Kevinvariant repo (Chapter 4: Cross Ratios, with Problems 50 and 51). It shows the book's format: a numbered problem box with the source in italics, a figure, one or more solutions, and "Remark" boxes.
- **The full manuscript.** Ask Kevin for the LaTeX source, which is better than the PDF because statements, solutions and figures can be extracted exactly. The book's landing page is `book.html` on Kevinvariant, and it is on sale on Amazon.

## Rights
- Kevin owns his **solutions, remarks and figures**, so they can be used freely.
- Most problem **statements** come from competitions, and the book credits them (for example "China 1999" or "IMO 2014 P4"). Kevin has asked for these to be quoted as bosses. Always keep the source credit exactly as the book gives it, and also credit the book itself.
- A problem with no source credit is treated as Kevin's original. Confirm each one with him.

## Spec
1. **Extract all 100 problems** into `book/problems.jsonl`. This file can be private or public; ask Kevin. Each record has:
   - The number, chapter and section, the statement (Markdown with LaTeX) and the source credit.
   - Every solution with its title (for example "Solution 1 (Harmonic Bundles)"), every remark, and the figure source.

   Check each statement against the PDF by eye. A transcription error in a boss would be embarrassing.
2. **Analyse** each problem with the task 03 schema: techniques, configurations, crux, solution paths and kyu. Record which chapter technique it is meant to exercise. Add a difficulty signal from MOHS or the source position where one exists.
3. **Choose the bosses** with Kevin:
   - **Chapter bosses:** the hardest problem in each chapter, so that each chapter's theme (cross ratios, spiral similarity, radical axes and so on) has a boss.
   - **Final bosses:** the 3–5 hardest problems in the whole book.
   - Every other problem becomes a normal 3–1 kyu geometry problem, tagged `provenance: {kind: "classical", source: "<contest>", book: "Beyond the Incenter, Problem N"}`.

   Write the proposal as a table (number, source, chapter, kyu estimate, why it's a boss), and get Kevin's approval before building anything.
4. **Boss data.** Boss files use the problem schema with `type: "proof"` plus a field:
   ```json
   "boss": {"tier": "chapter|final", "chapter": 4, "chapter_title": "Cross Ratios", "order": 4,
            "unlock": {"min_rank": "2 kyu", "requires": ["boss-ch3"]}}
   ```
   The rubric comes from Kevin's own solution and is out of 7. Kevin approves each rubric.
5. **Figures.** Convert the book's figures to theme-aware SVG (task 10 format). If the source is TikZ, use `dvisvgm` and then recolour to `currentColor`. Keep the book's labelling exactly.
6. **The boss gauntlet** (`#bosses`):
   - A page listing chapter bosses in book order, then the final bosses. Each shows its chapter title and lock state ("Reach 2 kyu", "Beat the Chapter 3 boss").
   - A black-belt badge with a red tape, using the same belt styling as the site.
   - A boss problem page shows the statement, figure, source credit, "From *Beyond the Incenter*, Chapter N", and a link to the book.
7. **Hints and solutions.**
   - Hints come from the chapter's technique: hint 1 names the chapter's tool, and hint 2 is from a Remark box.
   - Kevin's full solution unlocks after a mark of 5 or more out of 7. Whether to show the full solution or only the first steps plus a link to buy the book is **Kevin's decision**, since it affects book sales. Build it so that either option is a config switch.
8. **Rewards.** Beating a boss awards 89 points for a chapter boss and 144 for a final boss (the next Fibonacci numbers after 1 kyu's 55), plus a profile badge. Beating every final boss grants the rank **1 dan**.
9. **Inspirations.** Make the non-boss book problems available to task 09 as inspirations for original geometry problems. These generated problems must cite the book privately in `generated_map.jsonl`, never publicly.

## Acceptance criteria
- All 100 problems are extracted, and the spot-check against the PDF finds no transcription errors in 20 random problems or in any boss.
- Kevin has approved the boss list and every boss rubric.
- The gauntlet page works: locks, unlocks, badge, points and 1 dan. Test it with a seeded profile.
- Every boss shows both its competition source and its book credit.

## Out of scope
Selling the book on Cevian, and any change to the book itself.
