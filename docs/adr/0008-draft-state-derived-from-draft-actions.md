# Draft state is derived from Draft Actions, never stored

Analysts make mistakes under time pressure and may only notice them several Games later. Locked Characters, remaining pools and turn state are therefore always recomputed from the Series' Draft Actions, any Draft Action can be corrected at any time, and every correction is kept in an edit history so changes can be seen.

Saved Scouting Reports are an explicit exception ([ADR 0025](0025-saved-reports-are-snapshots.md)).

## Amendment (2026-11-26): clearing a Draft Action

Only the most recent Draft Action of the current Game (the latest non-voided one) can be cleared, which keeps turns contiguous. If the current Game has no actions yet, there is nothing to clear. Any other action, including every action of an earlier Game, is corrected by replacing it, which is always available, so nothing is blocked and there are never two Games in Drafting or an empty pick turn in an earlier Game. Clearing goes into the edit history.

## Amendment (2026-11-27): the current Game is the last Game

The current Game is the last Game in the Series, voided or not. Live entry, clearing and starting the next Game all use this single definition. If the current Game is Voided, there is nothing to clear. This replaces "the latest non-voided one" in the 2026-11-26 amendment. Every earlier Game is corrected by replacement and never cleared. As a result, clearing can never return an earlier Game to Drafting behind a later one. The PR #34 review found that case: with Game 1 Drafted and Game 2 Voided, clearing Game 1's last action left Game 1 permanently in Drafting.
