# The generator

Turns a corpus analysis record into an original problem, runs it through the gate (`pipeline/verify/`) and saves what passes for human review.

```
python -m pipeline.generate --from AIME-2019-I-07 [--n 2]
python -m pipeline.generate --make-plan plan.json [--per-kyu 10] [--seed 6]
python -m pipeline.generate --plan plan.json --run NAME [--limit 5] [--stop-file path]
python -m pipeline.generate --report NAME
```

Exit codes: 0 when finished, 2 if the plan limit stopped it, 3 if the backend failed. Re-running a plan with the same `--run` resumes it. `--limit` and `--stop-file` make it easy to read the plan's usage figures between chunks.

## Setup

As for the gate (`pipeline/verify/README.md`), plus these environment variables:

| Variable | Meaning |
|---|---|
| `CEVIAN_CORPUS` | The private corpus. Required: originality means nothing without it. |
| `CEVIAN_ANALYSIS` | Analysis records: a folder of `batch_*.jsonl`, or one jsonl file. Required. |
| `CEVIAN_GENERATED` | A checkout of the private repo's `generated-map` branch. Holds `generated_map.jsonl` and `runs/<run>/log.jsonl`. Without it they go to gitignored `out/generate/`. |

## How one problem is made

1. Choose recipes at random from those that suit the record, one for each of three candidates.
2. **Ideas.** One Opus call writes three candidates: statement, solution sketch and program. The prompt carries the standard's rules, the record and the source statement, labelled for calibration only.
3. Run the free checks on all three: `lint`, `leak`, lexical originality and the program in the sandbox. What the program prints becomes the key.
4. Keep the candidate the model rates most interesting among those that passed. If none passed, the most interesting one goes to an idea repair with its reason.
5. **Write-up.** A second call writes the hints and solution from the statement, the key and the sketch. It sees no contest text. If the writer finds the key or statement wrong, it says so and the idea is repaired.
6. Run the free write-up checks, then the gate. On a fail, repair, up to two repairs in all. A fault in the solution repairs only the write-up. Anything else repairs the idea. After that, discard and log why.

Two stages because the first version asked for three full candidates at high effort: Opus used the whole 32,000-token cap three times running and wrote nothing, at about $2 of API-equivalent usage. Neither `--effort`, `MAX_THINKING_TOKENS` nor `alwaysThinkingEnabled` limits thinking through the CLI. A stated thinking budget in the system prompt does.

## What happens to a gate result

| Result | Where it goes | Counts as passing? |
|---|---|---|
| `PASS` | `review/pending/` | Yes |
| `INVESTIGATE` on difficulty, or blind solves calling it too easy | `review/pending/` | Yes. The ruler is provisional, so this is data for the reviewer |
| `INVESTIGATE` with no majority and at least 2 of 7 solvers on the key | `review/held/` | No. It may be hard rather than ambiguous, and a person has to decide |
| Any other `INVESTIGATE`, or `FAIL` | Repair | No |
| `ERROR` | Retried once, then logged without a verdict, and a re-run tries it again | No |

## Files

`review/pending/<id>.json` is `{"draft": {...}, "report": {...}}`. `draft` is in the gate's format, so it can be verified again as it stands. `report` is the gate's report. Both `review/pending/` and `review/held/` are gitignored, because they hold `inspired_by` and corpus IDs.

The private repo's `generated_map.jsonl` has one line per saved draft: `id`, `inspired_by`, `variation_recipe`, `kyu`, `topic`, `run`, `outcome`, `at`. The run log, also private, has one line per input with every attempt, recipe, check result, reason, model and cost. Never commit either to this repo.

## Privacy

- A prompt holding contest text is never cached, and neither prompts nor raw replies are logged.
- `leak` compares every public field with the source: 8 consecutive words, two or more of its numbers, or its answer.
- Reports and logs name corpus IDs, which pair a generated problem with its source, so they stay in the private repo or in gitignored folders.

## Reusing it (tasks 08 and 09)

Add a `Profile` in `config.py` with its kyus, type and answer format. `prompts.py` and the checks in `drafts.py` hold what's specific to answer problems: task 09 needs its own format, rules and free checks, and `run.classify` decides what each gate result means.

## Tests

```
python -m unittest pipeline.generate.tests.test_generate
```

These use a scripted backend and an invented source problem, so they need no model or corpus.

## Figures

The write-up also returns a tkz-euclide `<figure>` for any solution that argues from a picture, or a `<no_figure>` reason if the problem isn't topic G and the argument has no picture. `drafts.attach_figures` fills in its decimals and compiles it for free before the gate. A failure goes back to the writer as a repair, keeping the statement and key. The draft carries its `.tex` and `.svg` in `figure_sources`, and approving it in the review queue writes them to `figures/`.
