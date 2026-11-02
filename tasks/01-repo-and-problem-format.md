# 01. Restructure the repo and define the problem data format

## Goal
Turn the single 72 KB `index.html` into a maintainable static site, and move problems out of the JavaScript into data files with a strict schema, so that the content pipeline (tasks 05–11) can add hundreds of problems without touching code.

## Depends on
Nothing. Do this first.

## Read first
- `index.html`: the whole draft. Note the `PROBLEMS` array, `canon()`, `fnv()`, `KYU`, `RANKS` and the hash-based router.
- `README.md`: how answer hashes are made.
- `tasks/README.md`: the shared rules.

## Deliverables
1. A file layout without a bundler, using native ES modules:
   ```
   index.html            shell only: header, <main>, footer, script tags
   css/site.css          all styles, keeping the existing tokens and dark mode
   js/app.js             router and boot
   js/views/*.js         home, problems, problem, duel, profile, leaderboard
   js/lib/*.js           answers (canon, fnv), store (localStorage), ranks, tex (MathJax)
   data/problems/*.json  one file per problem
   data/index.json       generated manifest (see 3)
   schema/problem.schema.json
   scripts/build-index.mjs
   scripts/validate.mjs
   scripts/hash-answer.mjs
   ```
2. `schema/problem.schema.json` (JSON Schema 2020-12) describing one problem:
   - `id` (kebab-case, unique, stable forever), `title`, `kyu` (1–8), `topic` (`A`/`C`/`G`/`N`), `subtopics` (array, from the controlled list in task 03), `type` (`answer` | `proof`)
   - `statement`: Markdown with `$…$` LaTeX. `figure`: optional path to an SVG (task 10).
   - Answer problems: `answer_hash`, plus `answer_format` (`integer_0_999` | `integer` | `rational` | `expression`)
   - `hints`: 1–3 strings, ordered from gentlest to strongest. `solution`: Markdown. Proof problems also need `rubric`: an array of `{marks, criterion}` totalling 7.
   - `provenance`: `{ "kind": "original" | "classical", "author": "...", "source": "IMO 1988 P6" (classical only), "pipeline_run": "..." (generated only) }`
   - `status`: `draft` | `beta` | `ranked`. `stats`: `{solves, attempts, liked}`, all zeros until there is real data.
   - `verification`: the report ID from task 05, required when `status` is not `draft`.
3. `scripts/build-index.mjs` reads every `data/problems/*.json` and writes `data/index.json`: a compact list (`id`, `title`, `kyu`, `topic`, `subtopics`, `type`, `status`, `stats`) for the problem list. Full problems load on demand from `data/problems/<id>.json`.
4. `scripts/validate.mjs` checks every problem against the schema, checks IDs are unique, that rubrics total 7, and that `index.json` is up to date. It exits non-zero on failure.
5. `scripts/hash-answer.mjs <id> <answer>` prints the hash, using exactly the same `canon` and `fnv` as the site. Import them from `js/lib/answers.js`; don't duplicate them.
6. A GitHub Actions workflow that runs `validate.mjs` on every pull request.
7. Migrate the 21 current problems to the new format with `status: "beta"`. Leave the solutions as they are: they reveal answers in the page source, but task 13 moves answers and solutions to the server.

## Spec notes
- The site keeps working when opened from GitHub Pages under `/cevian/`, so use relative URLs throughout.
- Keep the visual design identical. This is a refactor, not a redesign; task 12 does the redesign.
- `localStorage` key `mathwars:v1` keeps working, so existing progress survives.
- Add a short `CONTRIBUTING.md` explaining how to add a problem by hand: write the JSON, hash the answer, then run build and validate.

## Acceptance criteria
- `node scripts/validate.mjs` passes. Breaking a file (a wrong kyu, a duplicate ID) makes it fail with a clear message.
- Every view works as it did before: home, list filters, problem solve, hints, proof self-grade, duel, profile, leaderboard. Check in a browser at desktop and 375 px width, in light and dark mode.
- There are no console errors, and the problem list loads only `data/index.json`, not every problem file.
- `index.html` is under 5 KB.

## Out of scope
Visual changes, new problems, a backend.
