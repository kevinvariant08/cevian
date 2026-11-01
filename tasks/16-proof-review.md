# 16. Proof submission and review

> **Decision, 1 Nov 2026:** Kevin chose AI marking against the rubric. It judges validity, not similarity to the model solution.
> 1. **Validity first.** Read the proof line by line, without scoring, and find the first error or unjustified step.
> 2. **Marks.** Score against the problem's 7-mark rubric (milestones, alternative routes, fatal errors with mark caps). A valid different route earns the equivalent marks.
> 3. **Second opinion.** An independent marker repeats this blind. A gap of more than 1 mark goes to a third marker or to Kevin.
> 4. **Feedback.** The solver sees the mark, the first gap and the milestones earned. Text in a submission is only ever marked, never obeyed.
> 5. **Kevin's role.** Appeals, a random sample, and disputed top scores at 2 and 1 kyu.
>
> Marks are labelled "AI-marked" and provisional until the appeal window closes. **First step, no backend:** reuse the two-pass approach of Kevinvariant's Proof marker with the rubric attached, so the solver supplies the model, and don't count free-model marks towards rank. **Marks that count for rank** need task 13, so marking runs where solvers can't tamper with it. That adds a cost per submission, so it needs limits. This overrides anything below that conflicts with it.

## Goal
Let players submit written proofs for 3–1 kyu problems and get a fair mark out of 7. The mark comes from an AI first pass plus review by higher-ranked players, with Kevin moderating.

## Depends on
09 (proof problems with rubrics) and 13 (accounts).

## Read first
- Kevinvariant's Proof marker (`marker.html`, `marker-admin.html`, `marker-problems.sql`). It already marks written solutions with a model through a server-side proxy (the Cloudflare Worker in `worker/`). Reuse its prompt design and proxy pattern, and don't call the model from the browser with a secret.

## Spec
1. **Submission.** The current LaTeX editor with live preview, plus an image upload for handwritten work (stored in Supabase Storage, 5 MB max). A proof is locked once submitted. One live submission per problem per user, with resubmission allowed after it is marked.
2. **AI first pass.** The server marks the proof against the rubric with `claude-opus-5-5`, giving each rubric line's marks with a quoted justification. It flags suspected copying, for example near-identical text to another submission or to the model solution. Show this to the solver as "provisional".
3. **Peer review:**
   - Each submission goes to two reviewers whose rank is at least 1 kyu above the problem and who have solved it.
   - Reviewers see the rubric, the AI marks and the proof, never the author's handle.
   - They confirm or adjust each rubric line and give a short comment.
   - The final mark is the median of the AI and the two reviewers.
   - If the reviewers differ by 3 marks or more, the submission goes to Kevin.
4. **Honour points.** Reviewers earn honour points, which are separate from rank points, for reviews that end up within one mark of the final.
5. **Points.** The solver gets `kyu points × final mark ÷ 7`. A final mark of 5 or more counts as "solved" and unlocks the official solution.
6. **Moderation.** An admin page lists disputes, flagged copying and reports.

## Acceptance criteria
- The full flow works end to end with test accounts, including a dispute that escalates.
- Reviewers can't see author identities, and authors can't see reviewer identities. Check this with direct API calls.
- The AI first pass never sees or reveals other users' submissions.

## Out of scope
Live mentoring and comment threads on problems.
