# MVP scope

The first spec covers the MVP: milestones 1 to 3 of the first release. Milestones 4, 5 and 6 get their own specs.

## Milestones

1. **Walking skeleton:** load the League of Legends profile, create a Series, enter one Game's draft by hand and see Fearless Locks applied in Game 2, through the real UI and API.
2. **Draft board and data:** the rest of the rules engine and draft board (test-only second profile, corrections, overrides, timeline), CSV imports, Rosters, Character Pools and opponent statistics.
3. **Copilot:** code Shortlist and LLM enrichment. The core idea counts as proven here.
   - **First ticket, before building the Copilot:** a prototype (`/prototype`) measuring whether the prepared-suggestions model (Claude Haiku 5.5, and a local model if one is available) answers within the turn budget with a realistic copilot prompt. The ticket states the turn budget it measures against, and the result is recorded.

Imports, pools, statistics and the copilot are added around a path that already works.

## Statistics

In the MVP: bans by and against, presence, pick rate, win rate, pick priority, Role priority, splits by Draft Position and Game number in the Series, Observed Pools and Observed Role Usage ([ADR 0022](adr/0022-scout-statistics-and-scope.md)).

## Language

The per-language mechanism (templates, number-word lists, digit check, untranslated-term list) is in the MVP, shipping one complete language: English, so docs, templates and tests share one language. Brazilian Portuguese follows right after, as a small ticket that only adds data files.

## Later in the first release

- Scouting Report and "Ask the report" (milestone 4), including saved-report snapshots
- Side splits and the First Selection statistic (milestone 4, with the Scouting Report)
- Countdown timer (milestone 4 or later); it only informs and proves nothing about the core idea
- Opponent pool forecasting (milestone 5)
- External data API import (milestone 6)

## Out of the first release

See [future-ideas.md](future-ideas.md), plus the Deadlock profile, plan export, and accounts and multiple users.
