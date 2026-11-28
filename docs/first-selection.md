# Recording First Selection

Issue [#14](https://github.com/thiagocamerato757/Nimbus/issues/14), US-002, BS-012.

Each Game stores optional `first_selection_holder` (`A`, `B` or null) and
`first_selection_choice` (`side`, `draft_position` or null). Choice records which
choice the holder exercised; the Team's recorded Side/Draft Position gives its
result. Neither field is required, and either can be corrected or cleared through
`POST /api/series/{series}/games/{game}/first-selection` or the timeline form.
Holder and choice go together (amended 2026-11-27). A save that keeps the same
holder keeps the stored choice. A save that changes the holder clears the stored
choice, because it belonged to the other Team. Unsent fields are kept unless that
would leave them inconsistent. The UI always sends holder and choice exactly as
displayed. A choice always belongs to a holder: Start Game, Replay and edits
reject a choice without a holder (`choice_without_holder`), through one engine
rule (`record_first_selection`). This is a Structural Invariant (ADR-0009,
amended): an edit is rejected only when it would create such a choice, and
database migration 10 clears any stored one, logging each. The choice field is
disabled until a holder is selected and is cleared when the holder changes.
Those edits do not create or change Draft Actions, winners or Player Assignments.
Turn ownership always follows the recorded Draft Positions.

Rules profiles accept `default_first_selection_holder`: `none` (the backward
compatible default), `loser`, `winner`, or `alternate`. For a new Game, the previous
Game means the nonvoid attempt of exactly the preceding logical Game number.
A missing/pending result means no holder prefill for every policy. `alternate`
also needs that Game's recorded holder. Game 1 has no guessed holder.
The prefill is computed for display only (amended 2026-11-27). The server never
applies it: every setup or Replay request carries the holder the analyst saw, and
an omitted holder records none. The pre-filled holder can always be changed.
Choice starts empty.

The setup and Replay forms take the First Selection pre-fill once, when they open
(amended 2026-11-28). Only the analyst's own change or Apply moves the holder. A
later result changes no field: the form offers the new pre-fill, and Apply changes
the holder and clears the choice. If "Record winner and start" produces a
different pre-fill, the draft does not start; the analyst applies the offer or
presses Start again. This logic is one reducer, `frontend/src/firstSelectionForm.ts`,
shared by the setup, Replay and timeline forms.

A Replay computes its default from the previous lower-number Game, never its
same-number voided source's result or holder. Its choice starts empty. Its
Lineups, Sides, Draft Positions and Patch retain the agreed editable prefill;
copying Draft Actions still requires the explicit copy/new-draft choice.

Profiles with `sides_coupled: true` must explicitly name `first_pick_side` from
their two `sides`. A missing or unknown mapping fails profile loading. Setup and
Replay reject an inconsistent Side/Draft Position atomically. The UI displays
the corresponding Draft Position when Side changes. Uncoupled profiles keep
both choices independent. New Series snapshot Side names, coupling, explicit
first-pick Side and holder policy (ADR-0013); editing the profile affects new
Series. Older snapshots that predate these settings retain the former
independent/no-prefill behavior; their Side names use the loaded profile.

Database migration 9 adds nullable metadata columns, preserving existing Game
facts. Existing schema-8 databases receive a verified automatic backup first.
Migration 10 clears a choice stored without a holder and logs each one, after a
verified automatic backup.

## League rulebook investigation (2026-11-27)

The generic League of Legends profile explicitly uses `none`. This is Nimbus's
neutral prefill setting, **not** a claim that a league awards no First Selection.
A Title profile does not identify a specific league, event, stage or seeding.

Riot's [official 2026 season announcement](https://lolesports.com/en-GB/news/season-start-2026-lol-esports)
explains that a holder chooses Side or Draft Position and the opponent chooses
the remaining option. It does not establish one universal holder allocation.

Riot's [Competitive Operations library](https://competitiveops.riotgames.com/en-US/library?GAME=lol)
links the [2026 NACL Rulebook, version 26.6, August 2026](https://cdn.sanity.io/files/dsfx7636/news_live/60f17a7a37ed1d1a380c80f78e029e636dca87e1.pdf).
Section 2.3.3.1 (printed page 10) assigns Game 1 First Selection randomly with
balanced allocations, and subsequent Bo3 Games to the previous loser.
Section 2.6.5.1 (printed pages 17–18) specifies bracket-dependent first-Game
allocation and the previous loser for subsequent Games. This verifies a
league-specific `loser` policy, not a universal LoL policy. A deployment using
that competition can configure `loser`; `winner` and `alternate` are supported
configuration mechanisms, not assertions about NACL or any other league.
No automatic seed/coinflip allocation or league-policy enforcement is added.
