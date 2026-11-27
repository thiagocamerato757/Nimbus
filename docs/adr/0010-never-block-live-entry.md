# Nimbus nudges and flags; it does not block live entry

The next draft is already happening on stage while the analyst is entering data, so a blocked board costs lost entries, which is worse than missing or doubtful data. Missing information (winner, Player Assignments, First Selection holder) is prompted for and can be left for later, and rule breaks can be overridden. Only Structural Invariants are absolute. Starting the next Game requires the previous one to be Voided or to have a complete draft, never a result.

## Amendment (2026-11-27): after a void, the next Game is its Replay

"Starting the next Game requires the previous one to be Voided or to have a complete draft" no longer holds for Voided Games. The next Game needs the previous one Drafted or Closed. After a Voided Game, the next Game is always its Replay, under the same number and with the same gate as an ordinary next Game ([ADR 0034](0034-replay-keeps-the-voided-game-record.md), amended 2026-11-27). Starting the next Game still never requires a result, so live entry is not blocked: a Replay is available once a Game is voided, unless the Series has ended.
