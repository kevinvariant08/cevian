# 02. Build the private contest corpus

## Goal
Collect the best existing competition problems, from AMC 8 up to the IMO, with official answers, solutions and difficulty data, as clean machine-readable records. This corpus is what Cevian learns from: task 03 analyses it, and tasks 06, 08 and 09 generate original problems inspired by it. It is for private analysis only and is never published.

## Depends on
Nothing. The waves below run in order, and wave 1 is the pilot.

## Read first
- `tasks/README.md`, especially rule 1: contest texts stay private.

## Which competitions

Collect the last **15 years** (2012–2026) unless a row says otherwise. Each row's kyu band is the starting guess that task 03 refines.

### Wave 1: the pilot
| Competition | Type | Kyu band | Notes |
|---|---|---|---|
| AIME, every year 1983–2026 | answer, 0–999 | 5–3 | About 1,035 problems from the Random Math Wiki (wiki.randommath.com/aime). Its `robots.txt` allows crawling, and its pages credit the MAA. There is one paper a year until 1999, then I and II; 2025 and 2026 have AIME I only. Tag each record with `era` (`classic` before 2000, `modern` from 2000). Proves the pipeline end to end. |

### Wave 2: answer-based contests (8–3 kyu)
| Competition | Type | Kyu band | Notes |
|---|---|---|---|
| AMC 8 | multiple choice | 8–6 | Record the options and the correct value. |
| AMC 10 A/B, AMC 12 A/B | multiple choice | 7–4 | Same. |
| UKMT JMC, IMC, SMC | multiple choice | 8–5 | Last 10 years. Ask Kevin for papers if there is no clean source. |
| HMMT February and November | short answer | 6–3 | Individual rounds (Algebra/NT, Combinatorics, Geometry, General) and Guts. |
| ARML individual and relay | short answer | 6–4 | Last 10 years. |
| PUMaC, CMIMC, SMT (Stanford) | short answer | 6–3 | Last 10 years. Only include individual subject tests. |
| MATHCOUNTS State and National | short answer | 8–6 | Last 10 years, if a clean source exists. |

### Wave 3: olympiads (proof, 3–1 kyu)
| Competition | Kyu band | Notes |
|---|---|---|
| UKMT JMO, Cayley, Hamilton, Maclaurin | 5–3 | Proof-style, but approachable. |
| BMO1, BMO2 | 4–2 | |
| USAJMO, USAMO | 3–1 | |
| USA TSTST and TST | 2–1 | |
| EGMO | 3–1 | |
| CGMO (China Girls MO) | 3–1 | |
| APMO, Balkan MO, Baltic Way | 3–2 | |
| RMM (Romanian Masters) | 2–1 | |
| IMO | 3–1 | |
| IMO Shortlist (ISL) | 3–1 | The richest source. Keep the official labels (A1–A8, C1–C9, G1–G8, N1–N8). |
| All-Russian MO, China MO, Iran TST | 2–1 | Last 10 years. These are often hard to source cleanly, so collect only where a reliable English text exists. |
| Sharygin Geometry Olympiad | 4–1 | Geometry only. Correspondence round and final. |

Putnam and other university contests are out of scope.

## Where it lives
- The **private** repository `kevinvariant08/mathwars-corpus`. Ask Kevin to create it if you can't. Never put corpus files in the public `cevian` repo.
- Layout:
  ```
  raw/<exam>/<year>/...          cached source pages and PDFs, each fetched once
  corpus/<exam>.jsonl            one problem per line
  corpus/SOURCES.md              where each file came from, when, and under what terms
  scripts/fetch_<source>.py
  scripts/parse_<source>.py
  scripts/check_corpus.py
  ```

## Record format
One shared format for every exam:
```json
{"id":"ISL-2019-G7","exam":"ISL","year":2019,"paper":null,"number":"G7",
 "type":"answer|proof|multiple_choice",
 "statement_md":"... $LaTeX$ ...","choices":null,
 "answer":"057","answer_value":57,
 "has_figure":true,"figure_source":"asy code, image URL or null",
 "solutions":[{"source":"official|AoPS user <name>|...","url":"...","text_md":"..."}],
 "difficulty":{"position":"G7","mohs":40,"aops_votes":null},
 "source_url":"...","fetched_at":"2026-10-30T12:00:00Z"}
```

## Spec
1. **Sources, in order of preference:**
   - Official sites and PDFs: imo-official.org, the EGMO site, UKMT and BMO past papers, the MAA, HMMT and ARML archives.
   - **The Random Math Wiki** (wiki.randommath.com) for the AIME, AMC 8, AMC 10, AMC 12 and AHSME. Its `robots.txt` allows crawling. Its AMC 12 index skips 2019 and 2020.
   - PDFs Kevin owns.
   - **Not AoPS** for now. Its wiki is behind a Cloudflare bot check, and its `robots.txt` says `ai-train=no`. Kevin is asking AoPS for permission; until they say yes, don't fetch AoPS pages. This matters most for wave 3, where olympiad solutions mostly live on AoPS.

   For every source, read its terms of use and `robots.txt` first. If automated fetching isn't allowed, stop and ask Kevin for the papers instead. Fetch politely: at most 1 request every 2 seconds, with a descriptive User-Agent, caching everything in `raw/` so each page is fetched only once.
2. **Solutions.** Keep the official solution and **up to three** high-quality alternative solutions. Prefer ones that use a different method, and record their authors. Task 03 needs several solution paths to understand a problem properly.
3. **Difficulty data.** Record whatever exists:
   - The problem's position in its paper.
   - The ISL label.
   - Evan Chen's MOHS rating (Math Olympiad Hardness Scale) for the USAMO, IMO and similar contests, cited from his published ratings.
   - Official statistics where published, such as IMO score distributions by problem from imo-official.org, and HMMT solve rates.
4. **Parsing.**
   - Statements become Markdown with `$…$` LaTeX.
   - Turn rendered-LaTeX images back into LaTeX.
   - Keep Asymptote code verbatim in `figure_source`.
   - Multiple-choice options go in `choices`.
5. **`check_corpus.py`** checks:
   - The count per exam, year and paper against the official count, with any gaps listed.
   - Answers are in range for each exam.
   - IDs are unique.
   - There are no empty statements and no leftover HTML.
   - LaTeX parses (a dry run in Node).
   - The coverage of difficulty data per exam.

   It writes a summary table to `corpus/SOURCES.md`.
6. **Spot-check.** Compare 20 random problems per wave by eye with the source, and record the results.
7. **Deduplicate across exams.** Shortlist problems reappear in national olympiads, and AMC 10 and 12 share problems. Link duplicates with a `same_as` field rather than storing them twice.

## Acceptance criteria
- **Wave 1:** the complete AIME set, with the checks and spot-check passing. Stop here for Kevin to review before waves 2 and 3.
- **Waves 2 and 3:** every listed competition is either collected or has its gap explained (no clean source, terms forbid it, and so on).
- Nothing from the corpus appears in the public `cevian` repo. Check with `git grep` for distinctive phrases from 10 problems.

## Out of scope
Analysis (task 03), generation (tasks 06, 08, 09), and Kevin's own book (task 21).
