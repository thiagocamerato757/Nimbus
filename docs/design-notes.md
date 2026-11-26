# Design notes

Behaviour agreed during design that is neither a glossary term ([CONTEXT.md](../CONTEXT.md)) nor an architecture decision ([adr/](adr/)). Input for the spec, together with [mvp-scope.md](mvp-scope.md), [acceptance-examples.md](acceptance-examples.md) and [open-questions.md](open-questions.md).

## Series and Games

- A Series may be between any two Teams, with Our Team optionally marked. If neither is marked, the Copilot asks which Team to advise.
- A Series Format is Best-of (odd number) or Fixed-length (any number). Voided Games do not count towards it.
- The analyst records winners by hand. Winner is a correctable field, separate from Game Status. Starting the next Game from a Drafted one prompts for it (either Team, or "later").
- While results are pending, a Best-of Series is not declared over. Its score shows "result pending".
- A finished Series can still be corrected. A corrected winner never deletes Games; warn if Games exist past the deciding one.
- Patch is optional on a Series and can be overridden per Game. No MVP feature uses it.

## Game lifecycle

- A Game goes Drafting → Drafted → Closed, and can be Voided from any status.
- Drafted means every turn is filled or, for bans, skipped.
- Closed requires **all** Player Assignments **and** a winner.
- The next Game can start once the previous one is Drafted (or Closed) or Voided. Neither missing Player Assignments nor a missing winner blocks it.

## Draft

- A ban turn may be skipped; a pick turn may not. A ban lasts for its Game only unless the lock sources include bans.
- Locks apply as soon as a pick is recorded. They follow the Character, never the Player, and substitutions or swaps do not change them.
- The locked-ban rule applies only when the Character is already locked for the opponent of the banning Team.
- A Violation's acknowledgement covers one specific conflict (rule, action and cause): if any of them changes and a rule is still broken, it is Open again; if all match exactly again, the acknowledgement applies again.
- Only the most recent Draft Action of the current (latest non-voided) Game can be cleared; if it has none, there is nothing to clear. Anything else is corrected by replacement. Clearing goes into the edit history.
- The Copilot warns about Open Violations only.
- Retired Characters are not offered for new entries; a correction can still pick one deliberately.
- The Disabled List is set at Series creation (pre-filled from the Workspace list) and editable with an impact preview.

## Lineups and pools

- Each Game has its own Lineup per Team, pre-filled from the previous Game. It may be incomplete during the draft, and a complete Lineup is needed before every pick can be assigned.
- Player Assignments go only to Players in that Game's Lineup, one Character each.
- Remaining and Available Now are both shown; the Copilot reasons on Available Now.
- An Observed Pool is shown as an estimate, with counts and recency (for example "played 7 of last 10 games").

## First Selection

- The pre-filled holder can always be changed. With no winner recorded, nothing is pre-filled.
