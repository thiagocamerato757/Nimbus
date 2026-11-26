# Draft state is derived from Draft Actions, never stored

Analysts make mistakes under time pressure and may only notice them several Games later. Locked Characters, remaining pools and turn state are therefore always recomputed from the Series' Draft Actions, any Draft Action can be corrected at any time, and every correction is kept in an edit history so changes can be seen.

Saved Scouting Reports are an explicit exception ([ADR 0025](0025-saved-reports-are-snapshots.md)).

## Amendment (2026-11-26): clearing a Draft Action

Only the most recent Draft Action of the current Game (the latest non-voided one) can be cleared, which keeps turns contiguous. If the current Game has no actions yet, there is nothing to clear. Any other action, including every action of an earlier Game, is corrected by replacing it, which is always available, so nothing is blocked and there are never two Games in Drafting or an empty pick turn in an earlier Game. Clearing goes into the edit history.
