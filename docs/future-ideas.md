# Future ideas

Not part of the first release.

- Copilot advice on the First Selection choice itself (Side or Draft Position).
- Players moving between Teams (transfers). For now a Player is on at most one Roster and the time of a move is not recorded.
- Scout weights Observed Pools by patch. The first release only records the patch.
- Simultaneous or hidden drafts. Excluded because they change what a Draft Action, a turn and live entry mean, and the only example found was a mode in a community tool ([ADR 0015](adr/0015-sequential-drafts-only.md)). Once revealed, such a draft is just a list of picks and bans, so a record-only mode (no live turn validation) might support it without engine changes. Not decided.
- Automatic capture of picks and bans from a live source ([ADR 0003](adr/0003-manual-draft-entry.md)).
- Filling a record's empty fields from a later duplicate source ([ADR 0019](adr/0019-duplicate-games-linked.md)).
- Converters from outside match data files to the Nimbus CSV schema.
- A Title profile editor in the app.
- Translating the interface ([ADR 0024](adr/0024-ai-output-in-english-or-portuguese.md)).
- Tuning the copilot's Shortlist ranking from the Suggestion Log.
