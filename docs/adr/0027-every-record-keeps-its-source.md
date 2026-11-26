# Every record keeps its Source, and a whole Source can be removed

Data providers may restrict what can be kept or require deletion when access ends, so a record must never lose its origin.

- Every Game record and link records its Source. Games recorded live belong to a built-in "live" Source, with official or scrim taken from the Series, so origin, linking and removal have one mechanism and no special case.
- Linked records of the same real Game are all kept as received, with exactly one active; only the active one counts. This also allows undoing a wrong "same Game" answer.
- Removing a Source removes its records. A Game known only from it disappears; where another linked record remains, the new active one is the live one first, then the earliest import. Affected Games are recomputed, after the usual impact preview.
- Removal reaches derived data: saved Scouting Reports snapshot the Source of every Game they used, and removing a Source lists the reports that used it and offers to delete or regenerate them. The report part arrives with milestone 4.
