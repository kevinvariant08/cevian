# Cevian

A ranked dojo for contest maths, in the spirit of Codewars. Problems are graded on a kyu ladder from 8 kyu (AMC 8) up to 1 kyu (the hardest USAMO, USEMO, Balkan MO, CMO and IMO proofs).

A [Kevinvariant](https://kevinvariant08.github.io/) project. First draft.

## What's in the draft

- **Original problems** in the style of real contests, in algebra, combinatorics, geometry and number theory. Contest problems name their source.
- **Answer problems (8–3 kyu)** are checked instantly. Answers are stored as salted FNV-1a hashes, not in plain text.
- **Proof problems (3–1 kyu)** have a LaTeX editor with live preview. After submitting, you self-grade out of 7 against a rubric. Peer review is planned.
- **Duels** against a timed ghost opponent, with an Elo rating. A wrong answer locks you out for 15 seconds.
- **Profile** with rank progress, topic and kyu breakdowns, and an activity log.
- **Leaderboard** layout, filled with sample players.

Points per solve follow the Fibonacci numbers: 2, 3, 5, 8, 13, 21, 34, 55 from 8 kyu to 1 kyu.

## How it runs

It is static files with no build step: a small `index.html` shell, `css/site.css`, native ES modules in `js/`, and one JSON file per problem in `data/problems/`. The problem list loads only `data/index.json`; each full problem loads when you open it. MathJax 3 (SVG output) loads from jsDelivr and fonts load from Google Fonts. Progress is saved in `localStorage` under `mathwars:v1`, so it stays in one browser.

To run it locally:

```bash
python -m http.server 8000
```

Then open http://localhost:8000.

## Discussion threads

Each problem has a discussion panel that stays hidden until you solve it, submit a proof or forfeit it. Forfeiting is permanent: the solution unlocks and that problem never scores. Threads are hosted by [giscus](https://giscus.app) on this repo's GitHub Discussions, one per problem id. Until `js/lib/discuss.js` has its two ids, the panel says discussion opens soon and loads nothing. To switch it on:

1. On GitHub, open the repo's **Settings → General → Features** and tick **Discussions**.
2. In the **Discussions** tab, create a category called `Problems` with the **Announcement** format, so that only you and giscus can start threads.
3. Install the giscus app at https://github.com/apps/giscus and give it access to `kevinvariant08/cevian` only.
4. At https://giscus.app, enter `kevinvariant08/cevian` as the repository, choose **Discussion title contains a specific term** for the mapping, and pick the `Problems` category.
5. From the generated script tag, copy `data-repo-id` into `repoId` and `data-category-id` into `categoryId` in `js/lib/discuss.js`. Commit and push.

The threads are public on GitHub, so the lock is a courtesy against spoilers, not secrecy.

## Not built yet

Accounts, friend duels, real leaderboards, peer review of proofs and problem submission all need a backend.

## Adding a problem

Write `data/problems/<id>.json`, hash its answer with `node scripts/hash-answer.mjs <id> <answer>`, then run `node scripts/build-index.mjs` and `node scripts/validate.mjs`. [CONTRIBUTING.md](CONTRIBUTING.md) explains each field, and [schema/problem.schema.json](schema/problem.schema.json) is the full format.

## Reviewing generated problems

```bash
npm run review
```

This opens the review queue at http://localhost:8377/tools/review.html and serves the local site from the same address. Run `npm ci` once first. The gate needs its Python setup (`pipeline/verify/README.md`), and it uses `~/mathwars-corpus` unless `CEVIAN_CORPUS` says otherwise.

| Key | Action |
|---|---|
| `a` | Approve. `INVESTIGATE` asks you to press it again. `FAIL`, `ERROR` and unverified drafts can't be approved as they stand |
| `e`, then `Ctrl+Enter` | Edit, re-run the gate, and approve if it allows |
| `r`, then `1`–`9`, `0` or `o`, then `Enter` | Reject with reasons from section 6 of the standard. `o` is Other, which needs a note |
| `s` | Skip |
| `j` / `k` | Next and previous |
| `v` | Verify a draft that has no report |

Task 06 writes drafts to `review/pending/<id>.json` as `{ "draft": …, "report": … }`. To read them from another checkout, run `npm run review -- --pending <dir>`.

- **Approve** writes `data/problems/<id>.json` with only the schema's public fields and `status: "beta"`, rebuilds `data/index.json` and runs `validate.mjs`, undoing the write if that fails. Nothing is committed: check the problem on the local site, then commit `data/`. Pushing `main` deploys it.
- **Edits** cover title, kyu, statement, hints and solution, not the answer. If an edited statement makes the blind solvers doubt the key, the edit is blocked and can't be overridden.
- **Everything private stays in `review/`,** which is gitignored: `approved/` and `rejected/` keep the full drafts, and `decisions.jsonl` keeps every decision. It is per checkout, so run the queue from one that lasts, not a temporary worktree.
- **To undo a decision,** delete the problem file if there is one, run `npm run build`, and put the `{ draft, report }` from `review/approved/` or `review/rejected/` back in `review/pending/`.
- **`tools/review.html` is public once it reaches `main`,** because Pages serves the whole repo. It holds no data and does nothing away from localhost. The server listens on 127.0.0.1 only and refuses other hostnames, other origins and private folders.

`npm run digest` prints the rejection reasons as a short paragraph for the generator's prompt. `npm run test:review` runs the tests.
