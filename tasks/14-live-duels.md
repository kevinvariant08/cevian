# 14. Live duels with friends

## Goal
Run real-time duels between two signed-in players on the same problem, started from an invite link, with rated results.

## Depends on
13. Look at Kevinvariant's `duel.html`, its asynchronous ghost duel, and decide with Kevin whether Cevian duels replace or complement it.

## Spec
1. **Rooms.** A `mw_duels` table holds the room ID, players, kyu, the problem ID (chosen on the server from problems neither player has solved), state, start time and result. Clients sync over Supabase Realtime channels.
2. **Flow.** Create the room, copy the invite link, the friend joins, both see a 3-2-1 countdown and then the problem appears to both at once. Submissions go through `mw_submit_answer` with `source: "duel"`. The first correct answer wins. A wrong answer brings a 15-second lockout, enforced on the server. Leaving counts as a loss after 60 seconds' absence. There is a time limit per kyu.
3. **Rating.** Elo with K = 32 (24 after 30 games) in `mw_profiles.duel_rating`. It updates on the server only.
4. **Fairness.** The problem statement is sent only when the countdown ends. Server timestamps decide who answered first, never the client clock.
5. **Optional, if time allows:** a quick-match queue that pairs players within 150 rating points.
6. Keep the ghost duel as the offline mode.

## Acceptance criteria
- Two browsers on different accounts can complete a duel. The winner, rating changes and history show for both.
- Network loss and recovery mid-duel are handled: the player reconnects to the same room.
- Cheating attempts fail and are rejected by the server: an early submission before the countdown, a forged timestamp, or a submission to someone else's room.

## Out of scope
Tournaments and matchmaking beyond the simple queue.
