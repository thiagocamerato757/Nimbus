# A Replay is a new Game linked to the Voided Game

A Replay creates a new Game in the same Series and preserves the Voided Game and its history. It takes the same Game number because the Voided Game does not count towards the Series length; the timeline identifies the relationship, for example, "Game 3, replay of voided Game". Keeping separate records preserves the abandoned attempt without confusing its actions with the repetition.

Lineups, Sides, Draft Positions and Patch are pre-filled from the Voided Game and remain editable. Creating the Replay requires an explicit choice between "copy the voided Game's draft" and "new draft", with no default: leagues differ on whether a remake retains picks and bans. Copied Draft Actions are editable pre-fill. The copy saves immediately despite Game Rule Violations and shows those Violations in the preview; Structural Invariants remain mandatory and no actions are silently dropped.

Player Assignments and winner start empty. A Violation that was Open in the Voided Game arrives Open. An acknowledgement is inherited only for the corresponding Violation whose rule, action and cause match the original, with a traceable reason, "carried from voided Game N", plus its original reason. A different cause or a new breach arrives Open without blocking the save. This explicit carryover preserves an official ruling within its original scope without requiring the analyst to re-enter it; it is not a silent copy of confirmations. Later changes and reversals follow ADR 0009.

A Replay can be created only for the most recent voided attempt, before the next Game starts. A Replay that is itself Voided can be replayed again under the same Game number, keeping the chain of separate linked attempts.

## Fearless follows Game numbers, not attempts

A Game produces Fearless Locks only for Games with a higher Game number in the same Series, subject to the snapshot's Lock Reach, Lock Sources and treatment of Voided Games. A Voided Game and its Replay have the same number, so neither attempt locks against another attempt of that number. When the snapshot counts Voided Games, the voided attempt still produces Locks for higher-numbered Games.

Counting a voided attempt means its Characters can be burned for following Games; it does not prevent replaying that Game. Locking its copied picks against its own Replay would defeat the purpose of the explicit copy-draft option. This is a general Game-number rule, not a Replay-specific exemption. See the Azir example in [acceptance examples](../acceptance-examples.md#voided-game-locks-apply-to-higher-game-numbers).

## Amendment (2026-11-27): numbering after a void and copied Draft Positions

After a Voided Game, the next Game is always its Replay, with either a copied draft or a new draft. No separate path starts an ordinary next Game after a void, so a Best-of-3 can go 1, 2 (voided), 2, 3. The Series Format's maximum number of Games counts non-voided Games only.

A Replay's Draft Positions remain editable, but not together with a copied draft, because the copied Draft Actions belong to the source's Draft Positions. A copied draft with different Draft Positions is rejected with "Copying the draft requires the same Draft Positions; keep them or choose new draft". The Replay setup prevents that combination before it is submitted. Sides may still change, unless the Series couples them to Draft Position.

## Amendment (2026-11-27): only the current Game can be voided

Only the current Game, which is the last one in the Series, can be voided; it can be voided from any status. Voiding an earlier Game while a later one exists is rejected with "Only the current Game can be voided; correct earlier Games by replacement". The reason is the same as for the current Game in [ADR 0008](0008-draft-state-derived-from-draft-actions.md): voiding an earlier Game would change the Series' numbering and the Fearless Locks of the Game in progress, and its Replay could no longer follow it. Revisit this only if a real case of an earlier Game abandoned after a later one started appears.

## Amendment (2026-11-27): a Replay follows the next-Game gate

A Replay is how the next Game starts after a void, so it follows the same gate as an ordinary next Game. While the Series has ended, a Replay is rejected with `series_ended`. "Ended" is derived from the current score, so a winner correction that un-decides the Series makes the Replay available again, with no special case. Since only the current Game can be voided and the next Game after a void is its Replay, "before the next Game starts" in the fourth paragraph above now means: while the Voided Game is still the current Game. The engine keeps this as one ordered gate shared by `can_start_next`, starting a Game and creating a Replay. An ended Series is checked first, so the next-Game route never asks for a Replay that the same gate would refuse.
