# Match history is imported from Nimbus's own two-file CSV schema

Match history comes as a `games` file (one row per Game) and a `draft_actions` file (one row per ban or pick), linked by a game reference. This works for any team size and states a Game's details once. Converters from outside sources can come later.

- `games`: game reference, date and both Team names are required; Series reference and Game number, each Team's Side and Draft Position, winner, patch, tournament and Fearless variant are optional.
- `draft_actions`: game reference, Team, ban or pick and Character are required; order, Player and Role are optional.

A Game's Fearless variant gives past picks their lock context. It is taken from the row, else from a Workspace mapping of tournament to variant, else it is unknown. Games sharing a Series reference but resolving to different variants raise an import warning that needs confirmation.

History may be incomplete and is not checked against a Draft Order or Game Rules; a statistic that needs a missing field leaves that Game out and reports how many Games it used. Observed Role Usage takes the Role from the row, falling back to the Player's usual Role. Games recorded live in Nimbus count too.

Importing is idempotent: a game reference, scoped by a source name, identifies a Game, so re-importing updates it and replaces its draft actions as a set, reporting new, updated and unchanged Games. Unknown Team and Player names are mapped to an existing or new entity and remembered as aliases. Nothing is written until the analyst confirms a preview, and nothing is written half-way.

The unit of rejection is the Game: any unreadable row, including an invalid value in an optional field, rejects that whole Game, and a previously imported version of it stays as it was. Missing optional fields are never errors, and a Game with no action rows is accepted. An unknown Character name can be mapped in the preview, and name mappings are kept in the Workspace, so the app never rewrites the catalog file. The result offers a download of only the rejected Games' rows with a reason per row, to fix and re-import.

The preview also lists warnings that need confirmation but reject nothing: the same Character more than once in a Game, a Team with more picks than the team size, different Fearless variants within one Series reference, and two Games with the same Teams, date and picks under different references. Fewer picks than the team size is not a warning.

## Considered Options

- One row per Game with a column per ban and pick: the columns would change with each Title's draft.
- One file repeating Game details on every action row: the copies can contradict each other.
- Reject only the bad row: a partial Game looks complete, silently skews counts, and on re-import could replace a good version with a partial one.
- Reject the whole file: one typo would block every other Game.
