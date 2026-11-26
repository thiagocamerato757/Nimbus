# The engine supports sequential drafts only

"Another Title is only a new profile" cannot be promised for every draft anyone might invent, so the limit is stated: any sequential draft (one visible ban or pick per turn, in a fixed order) is a Title profile edit, and any other kind, such as simultaneous or hidden picks, is an engine change. Several turns in a row for one Draft Position express grouped bans or picks, and bans agreed before a match are ordinary ban turns at the start of the order. "The same Character twice in one Game" is a Game Rule controlled by the profile ([ADR 0009](0009-invariants-vs-overridable-rules.md)), never a Structural Invariant, so formats with mirrored Characters need only a profile setting. A synthetic Deadlock-style profile in the test suite checks the promise.

## Considered Options

- Also support simultaneous or hidden turns: changes what a Draft Action, a turn and live entry mean, for a format seen only in a community tool.
