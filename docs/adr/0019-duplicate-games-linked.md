# Duplicate Games are linked, and the record already in Nimbus wins

The same real Game can arrive from two sources, or be recorded live and imported later, which idempotency by game reference ([ADR 0018](0018-match-history-csv-import.md)) cannot catch. Imports detect probable duplicates, against live Games too, as the same Teams (after aliases) within ±1 day, since sources mix UTC and local time.

- **Exact match** (every pick identical): pre-selected as "same Game", with a confirm-all action; any can be unticked.
- **Partial match** (only some picks match, or one record lacks picks): no default, and each must be answered before the import can be confirmed.

"Same Game" links the records: the Game is counted once, both records are kept with their Source and one is active ([ADR 0027](0027-every-record-keeps-its-source.md)), and the record already in Nimbus wins, so an import never changes a live Game. "Different Games" is remembered and not asked again. The preview lists every value the existing record lacks or the new one contradicts, with a contradicting winner shown as a warning.

## Considered Options

- Merging empty fields from later sources: more useful, but needs tracking where each value came from. Not in the first release.
- No default for any match: a team that records its official Games live would face a dozen identical questions on every league import.
