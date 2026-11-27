# A Replay is a new Game linked to the Voided Game

A Replay creates a new Game in the same Series and preserves the Voided Game and its history. It takes the same Game number because the Voided Game does not count towards the Series length; the timeline identifies the relationship, for example, "Game 3, replay of voided Game". Keeping separate records preserves the abandoned attempt without confusing its actions with the repetition.

Lineups, Sides, Draft Positions and Patch are pre-filled from the Voided Game and remain editable. Creating the Replay requires an explicit choice between "copy the voided Game's draft" and "new draft", with no default: leagues differ on whether a remake retains picks and bans. Copied Draft Actions are editable pre-fill. The copy saves immediately despite Game Rule Violations and shows those Violations in the preview; Structural Invariants remain mandatory and no actions are silently dropped.

Player Assignments and winner start empty. A Violation that was Open in the Voided Game arrives Open. An acknowledgement is inherited only for the corresponding Violation whose rule, action and cause match the original, with a traceable reason, "carried from voided Game N", plus its original reason. A different cause or a new breach arrives Open without blocking the save. This explicit carryover preserves an official ruling within its original scope without requiring the analyst to re-enter it; it is not a silent copy of confirmations. Later changes and reversals follow ADR 0009.

A Replay can be created only for the most recent voided attempt, before the next Game starts. A Replay that is itself Voided can be replayed again under the same Game number, keeping the chain of separate linked attempts.

## Fearless follows Game numbers, not attempts

A Game produces Fearless Locks only for Games with a higher Game number in the same Series, subject to the snapshot's Lock Reach, Lock Sources and treatment of Voided Games. A Voided Game and its Replay have the same number, so neither attempt locks against another attempt of that number. When the snapshot counts Voided Games, the voided attempt still produces Locks for higher-numbered Games.

Counting a voided attempt means its Characters can be burned for following Games; it does not prevent replaying that Game. Locking its copied picks against its own Replay would defeat the purpose of the explicit copy-draft option. This is a general Game-number rule, not a Replay-specific exemption. See the Azir example in [acceptance examples](../acceptance-examples.md#voided-game-locks-apply-to-higher-game-numbers).
