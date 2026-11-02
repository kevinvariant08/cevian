# 20. Kevinvariant integration

## Goal
Make Cevian and Kevinvariant feel like siblings: one account, links in both directions, and no duplicated features.

## Depends on
13 (shared accounts). The basic links are already live on Kevinvariant's `main`.

## Spec
1. **Links.** Kevinvariant already links Cevian from its menu, footer, homepage and Practise and compete page. Cevian needs a matching "Kevinvariant" link in its header and footer (it has one). Make sure both use the same wording and that the cache version on Kevinvariant's `site.js` is bumped when the menu changes.
2. **One account.** After task 13, the sign-in state is shared. Show the same display name on both sites, and link "Your account" on Cevian to Kevinvariant's account page.
3. **Overlap review.** Kevinvariant has an Arena (racing a bot), Friend duel, Problem of the week, Rewards (levels, coins, badges) and a Proof marker. For each one, write down whether Cevian should link to it, absorb it or ignore it, and agree that with Kevin before building anything. At the least:
   - **Rewards.** Decide whether Cevian solves earn Kevinvariant coins. If they do, add a server-side hook in `mw_submit_answer` that calls Kevinvariant's existing coin logic. Don't create a second currency.
   - **Proof marker.** Cevian proof review (16) should share its prompt and proxy code rather than fork it.
4. **Theme.** Kevinvariant has a dark-mode toggle stored per browser. Read the same preference so that switching on one site carries over to the other.

## Acceptance criteria
- A signed-in user moves between the sites without signing in again, sees the same name, and the theme carries over.
- The overlap decisions are written in `docs/kevinvariant-overlap.md` and approved by Kevin.

## Out of scope
Merging the two codebases.
