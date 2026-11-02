# 13. Accounts and server-side answer checking

## Goal
Give Cevian real accounts, shared with Kevinvariant, and move answers and solutions off the client, so that progress syncs across devices and nobody can read answers from the page source.

## Depends on
01. This task is the foundation for 14–18 and 20.

## Read first
- In the Kevinvariant repo (`kevinvariant08/kevinvariant08.github.io`):
  - `auth-config.js`: the Supabase project URL and publishable key.
  - `account.js`, `auth.html`, `setup.sql` and `attempts.sql`: how accounts, profiles and attempts work there.
- Both sites are served from `kevinvariant08.github.io`, so they share an origin. A Supabase session created on Kevinvariant is visible to Cevian. Use the same Supabase project; don't create a second one.

## Spec
1. **Schema**, as a migration file `supabase/migrations/<date>_cevian.sql`, with every table prefixed `mw_`:
   - `mw_problems`: the public fields of each problem, without answer or solution.
   - `mw_answers`: `problem_id`, `answer_hash`, `solution_md` and `hints`. **There is no client read access.**
   - `mw_attempts`: user, problem, submitted value, correct, time, hints used, and source (`solo` | `duel`).
   - `mw_solves`, a view or table: the first correct attempt per user and problem.
   - `mw_profiles`: handle, rank points and duel rating. It is linked to the existing auth user.
   - Row-level security on every table: users read and write only their own rows, and the public reads only `mw_problems` and the leaderboard fields.
2. **Server functions**, as Postgres `security definer` functions or Supabase Edge Functions:
   - `mw_submit_answer(problem_id, value)` canonicalises the value with the **same** rules as `js/lib/answers.js` (include test vectors that both sides must agree on), compares it, records the attempt, awards points (Fibonacci by kyu, minus a quarter per hint) and returns `{correct, points, rank}`.
   - `mw_reveal_hint(problem_id)` returns the next hint and records it.
   - `mw_get_solution(problem_id)` returns the solution only if the caller has solved the problem.
3. **Seeding.** `scripts/sync-problems.mjs` upserts `data/problems/*.json` into `mw_problems` and `mw_answers` using the service-role key, read from the environment and never committed. Run it from GitHub Actions on merge to `main`, with the key held as a repo secret.
4. **Client:**
   - "Sign in with your Kevinvariant account", which reuses the Kevinvariant sign-in page and returns to Cevian.
   - Signed-out users keep the current local mode (hash checking). Once answers move to the server, remove `answer_hash` and `solution` from the public JSON. Signed-out users then see "Sign in to check answers", or else keep hashes for 8–6 kyu only, which is Kevin's decision.
   - On first sign-in, offer to import `mathwars:v1` local progress (but only solves the server can re-verify, so re-check each one).
5. **Rate limiting.** At most 30 submissions a minute per user, and a wrong-answer cooldown on the server that matches the duel rules.

## Acceptance criteria
- With a signed-in test account, solving on a laptop shows as solved on a phone.
- No answer or solution is fetchable by an anonymous or authenticated client for an unsolved problem. Prove this with a script that tries the REST endpoints directly.
- The canonicalisation test vectors pass on both the client and the server.
- Kevinvariant's existing tables and RLS are unaffected. The migration only adds `mw_` objects.

## Out of scope
Duels (14), leaderboards (15), proof review (16).
