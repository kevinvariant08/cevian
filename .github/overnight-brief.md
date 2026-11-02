# Kyuclid: audit run

Owner: Kevin Hu. This is an unattended run; never stop to ask questions.
Read docs/problem-standard.md first. Spend cap for this run: $10 (check
pipeline/api-ledger.jsonl). Never push and never touch main.

The previous run rewrote all 96 solutions (commit f9f5756) but its audit
results were lost, because out/ is not committed.

1. Run `python -m pipeline.generate.rewrite_batch audit` so a different model
   audits every one of the 96 solutions. It flags and never fixes. If it
   fails, fix the cause in the script and rerun; don't change models.
2. Re-run the gate tests (pipeline/verify and pipeline/generate tests, plus
   `node --test scripts/review-server.test.mjs`) and record the results.
3. Write reports/2026-11-02-audit.md and COMMIT it on this branch, containing:
   a table of every flagged solution (problem id, kyu, the auditor's issue
   in one line), the count passed and flagged, test results, and total
   spend from the ledger. Also copy the audit results into
   reports/2026-11-02-audit.jsonl and commit that too.
4. Do not edit any solution. Kevin reviews the flagged ones himself.
