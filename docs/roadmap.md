# Cevian versus Codewars: a roadmap

**Status: for Kevin.** Written during the November 2026 API-credit session, by comparing Cevian's current frontend (`js/`, `index.html`) against Codewars' feature set from memory of using it. No Codewars page was scraped or copied; this is a feature comparison, not a design copy.

## How to read the table

- **Have** means the feature already works in this repo today, confirmed by reading the code, not assumed from a task brief.
- **(a) Static** means it can be built now, in the current no-build vanilla ES module site, with no account and no server.
- **(b) Needs accounts** means it needs task 13 (accounts and server-side answer checking) first, because it requires data shared across browsers or devices: a real leaderboard, peer review, community authoring, live duels.

| Codewars feature | Cevian today | Where it would land |
|---|---|---|
| Difficulty ranks (kyu/dan) | **Have.** `js/lib/ranks.js`, belts on every row and the profile | — |
| Browse, filter and search kata by rank, tag, status | **Have.** `js/views/problems.js`: kyu, topic, subtopic, type, status chips, free-text search, four sort orders, pagination | — |
| Kata of the day | **Have.** `today()` in `js/views/home.js`, a deterministic pick by day index | — |
| Personal stats: rank progress, solved count, activity calendar, strengths by tag | **Have.** `js/views/profile.js`: rank bar, 12-week heatmap, by-kyu and by-topic bars, subtopic strength table | — |
| Recent activity log | **Have.** `S.log` in `js/lib/store.js`, shown on home and profile | — |
| Honor/rank points for solves | **Have.** `award()` in `store.js`, hint cost deducted, proof grade scaling | — |
| Training queue ("next kata for you") | **Have.** `upNext()` plus the "Show another" skip on home | — |
| Duel/race mode | **Have**, against a local ghost. `js/views/duel.js`. Codewars has no direct equivalent | — |
| Leaderboard | **Partial.** `js/views/leaderboard.js` renders a real table and ranks you against sample players, but the other rows are invented. A real one needs shared accounts | (b), task 13/15 |
| Save progress across devices | **Missing.** `store.js` only reads and writes `localStorage`. Clearing site data loses everything | (a), see below |
| Favourite / bookmark a kata to return to | **Missing.** There is no saved list distinct from solved/tried | (a), see below |
| Badges or milestones beyond the rank itself | **Missing.** The rank is the only recognition; Codewars also marks streaks and completion milestones | (a), see below |
| Kata author tools, community authoring | **Missing** | (b), task 17 |
| Discuss tab / comments per kata | **Missing** | (b), needs accounts and moderation |
| Solution voting and viewing others' solutions | **Missing**, and `stats.liked` is a static seed number, not a live vote | (b): a real vote needs a shared store so one person can't stuff it |
| Peer-reviewed proof marking | **Missing.** The proof page only self-grades against the rubric, as task 16 describes | (b), task 16, depends on 13 |
| Clans / teams | **Missing** | (b), task 15 |
| Multi-language code kata | Not applicable. Cevian is answer and proof maths, not code | — |

## What this adds to the three phase-C product tasks

Tasks 12 (frontend polish), 13 (accounts) and 15 (leaderboards and clans) already cover most of the **(b)** rows. This table's contribution is the **(a)** rows: three gaps that need no account and were not already built, found only by reading the code rather than assuming from the task briefs. `js/views/problems.js`, `profile.js` and `home.js` already deliver filtering, stats and a daily pick, so they are not listed as roadmap work below.

## Ranked by value to solvers

1. **Progress export and import.** Progress lives only in `localStorage` (`mathwars:v1`). A cleared cache, a new device or a browser reinstall loses every solve, every point and the whole streak, with no way back. This is the single biggest risk to a returning solver and the only gap the session brief names directly.
2. **Favourites.** A solver who meets a problem they want to come back to (an interesting technique, an unfinished attempt) today has to remember the title or copy the link somewhere else. A saved list, filterable from the problems page, closes that loop with no new infrastructure: it is one more map next to `solved`, `tries` and `hints` in the same `S` object.
3. **Achievements.** The rank number is the only form of recognition right now. Milestones (a streak, a clean sweep of a kyu, a first proof) reward behaviour the site already tracks (`S.activity`, `S.solved`, `S.proofs`) but never surfaces. Lower value than the first two because it adds motivation rather than fixing a gap, but it is cheap: pure computation over data already in `S`.

Other static ideas considered and set aside for now, with why:

- **A weak-subtopic practice queue.** Profile already lists strengths by subtopic with a link into a filtered problem list (`#problems?s=...`), which covers most of the value. A dedicated "practice queue" view would mostly re-sort what `upNext()` and the subtopic table already expose.
- **A problem notes scratchpad.** Plausible, but proof problems already have a full text editor with a LaTeX preview; answer problems are short enough that a scratchpad adds a feature surface for little-used value.
- **Printable or offline problem sets.** Real value for classroom use, but it is a bigger change (print stylesheet or a bundling step) than the no-build site easily carries, and it serves a smaller audience than the three above.

## Implementation notes for the three chosen items

All three live entirely in `js/lib/store.js` (state) plus the views that already read `S`, so none of them add a route, a dependency or a build step.

1. **Export/import**: a button on the profile page downloads `S` as `cevian-progress-<date>.json` (`Blob` + an `<a download>`, no server). Import reads a chosen file, validates it loosely (an object with a `solved` map) and either replaces or merges with the current state, then saves and re-renders. Because `S` already holds every feature below, exporting it also backs up favourites and anything else added to the same object.
2. **Favourites**: `S.favourites: {}`, a star toggle on the problem row and the problem page next to "Report a problem", and a `favourites` status option in the problems list filter alongside `open`/`tried`/`solved`.
3. **Achievements**: a fixed list of definitions (streak lengths, kyu sweeps, first proof, first duel win, total solved milestones), each a pure function of `S`, evaluated and rendered on the profile page under the existing heatmap section. No new storage: an achievement is "earned" the moment its condition is true, so nothing needs to be migrated for solvers who already have progress.
