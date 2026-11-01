# Kyuclid: API-credit work session

You are continuing work on Kyuclid (repo kevinvariant08/kyuclid, local checkout
C:\Users\kevin\mathwars). Start by reading tasks/README.md, docs/problem-standard.md
and tasks/16-proof-review.md. The owner is Kevin Hu.

Kevin authorises resuming the paused work now: this brief is his go-ahead.
The task for this session is Phase 1 below, then Phases 2 and 3 only if
budget remains. Build the shared API call logger first.

## Overnight mode

This is an unattended overnight run. Kevin is asleep and cannot answer.

- Never stop to ask a question. When something is ambiguous, take the most
  reasonable reading that fits the rules below, record the decision in the
  report, and carry on.
- Commit on the branch after each meaningful step, with clear messages, so
  progress survives if the run is interrupted.
- While a batch is processing, poll its status every few minutes with a
  short command (do not burn turns re-reading files). Use the waiting time
  for work that does not depend on the batch.
- If one item fails repeatedly, mark it as needing Kevin's attention in the
  report and move on rather than retrying indefinitely.
- Spend cap for this run is $40 (this replaces the $25 figure below). Write
  the report before stopping, whatever the reason.

## Budget rules (read first, follow throughout)

This session runs on a $100/month API credit pool, not Kevin's plan. Treat
spend as the main constraint.

- Driver model is Sonnet. Use Haiku for routine, high-volume calls (formatting,
  tagging, simple checks). Use Opus 5.5 at medium effort only for advanced maths
  (3 kyu and above, proofs) or hard coding problems.
- Exception: the verification gate's blind-solve model mix stays exactly as it
  is, because the difficulty scale is fitted to it. Do not change models or
  effort settings inside pipeline/verify/.
- Any job of more than ~20 independent model calls goes through the Message
  Batches API (50% cheaper), not live calls.
- Use prompt caching for repeated context: problem-standard.md, the taxonomy,
  the proof rubric, the style rules.
- Log every API call (script, model, input/output/cached tokens, estimated
  cost) to pipeline/api-ledger.jsonl and add it to .gitignore. Read the key
  only from the ANTHROPIC_API_KEY environment variable. Never write the key
  to any file, log, or commit.
- Hard stop: if logged spend for this session reaches $25, stop, write the
  report below, and end.

## Non-negotiable rules

- Never push to main. Pushing main deploys the live site. Work on a branch.
- Nothing goes live without Kevin's review.
- Contest text never enters the public repo. AoPS is off-limits.
- Publish only via review/decisions.jsonl, never by copying a folder. Older
  worktrees still contain the 21 removed problems. Check the problem count
  before any commit that touches data/.
- Solution style: concise, like a strong olympiad student. No "crux", no "key
  insight", no "Why this works". Lemma, Claim, Remark only where they help.
  Easy problems get a line or two. Geometry solutions need tkz-euclide diagrams.
- No em dashes in any user-facing text.
- Windows traps: write files with LF endings (Python write_text gives CRLF and
  can push index.html over its 5 KB limit); free port 8377 before starting the
  review server; git push may fail on DNS from Bash, so leave pushing to Kevin.

## Phase 1: finish the paused solution rewrite

Work in .claude/worktrees/all-kyus-433418 on branch claude/all-kyus-433418
(latest commit d76a14b is WIP; there is an uncommitted edit to
pipeline/generate/rewrite.py; inspect it before continuing).

1. Rewrite the remaining 92 of 96 solutions in the concise style as one batch.
2. Audit every solution (including the 4 already done) with a second batch
   using a different model from the one that wrote it. The auditor checks
   correctness and the style rules, and flags rather than silently fixes.
3. Re-run the gate test suite and confirm it passes (the earlier fix to 3
   failing tests was never re-verified).
4. Commit on the branch and queue everything for Kevin in the review page.
   Do not merge.

## Phase 2: measure the generation pipeline

Run generation plus the full verification gate on a pilot of 10 new problems
across kyus, through the Batch API where possible. Report cost per problem
by stage, and estimate how many problems per month $100 supports. Do not
start the full 300-problem run.

## Phase 3: website roadmap toward Codewars

Only if budget remains after Phases 1 and 2.

1. Write docs/roadmap.md: compare Kyuclid with Codewars feature by feature,
   and split items into (a) doable on the static site now and (b) needing
   accounts and a server (task 13). Rank by value to solvers.
2. Implement up to three of the highest-value static items on a new branch
   (examples: filtering and search by kyu and technique, richer profile stats,
   progress export and import since progress is browser-only, a proper
   problem-of-the-day). Keep the no-build, vanilla ES module structure and
   the existing design. Do not start accounts, a backend, or proof marking.

## End-of-session report

Write reports/<date>-api-session.md with: what was completed, branches and
commits, test results, items awaiting Kevin's review, total spend from the
ledger, cost per problem from Phase 2, and the recommended next step.
