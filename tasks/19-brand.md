# 19. Name, brand and launch assets

> **Decision, 30 Oct 2026:** the name check (`docs/name-report.md`) found a live US trade mark, MATH WARS METHOD, so Kevin renamed the site **Cevian**. The brief below is kept as written for the record. Its asset work now applies to Cevian. Kevin still has to run the UK IPO search for "Cevian".

## Goal
Confirm that the name can be used, and give MathWars a complete, consistent identity for launch.

## Depends on
Nothing. This can start immediately.

## Spec
1. **The name.** Search for existing products and businesses called "MathWars" or "Math Wars", including apps, websites, games and education companies. Check the UK IPO and USPTO trademark databases and the obvious domains (`mathwars.com`, `.org`, `.io`, `.co.uk`) and social handles. Write up the findings with links, and give a recommendation of keep, keep with a modifier, or rename. If renaming, propose 8 alternatives that pass the same checks. **This is not legal advice**, and the report should say so.
2. **Identity.** Keep the current direction (the belt-rank system, the ∴ seal, Big Shoulders Display with IBM Plex) unless the name changes. Then produce:
   - The logo as SVG, in horizontal and square forms.
   - A favicon set (SVG, 32 px, 180 px Apple touch, 192/512 px PWA) and `site.webmanifest`.
   - An Open Graph image (1200×630) for the home page, plus a per-problem OG image template.
   - A one-page brand sheet at `docs/brand.md` listing colours (light and dark), type and belt colours, with usage notes.
3. **Copy.** A tagline, a one-paragraph description for the Kevinvariant link card, and social bios.

## Acceptance criteria
- The name report has sources for every claim.
- The assets are in `assets/` and wired into `index.html`, and they render correctly when shared in a link preview (test with an OG debugger).

## Out of scope
Registering domains or trademarks: that's Kevin's decision, and it costs money.
