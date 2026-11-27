# Structural invariants are absolute; game rules can be overridden

Nimbus records what happened on stage, which can contradict the rules it knows because of a league ruling, a wrong earlier entry or a wrong profile. Structural invariants (one Draft Action per turn, the turn exists in the Draft Order, the Character exists in the Character Catalog) can never be overridden. Game rules from the Series' rule settings (taken from the Title profile, [ADR 0013](0013-series-snapshots-rule-settings.md)) reject a live entry but can be overridden with a reason (category and optional note), and corrections are always saved. The resulting Violations are derived, never block or auto-change anything, and are either Open or Acknowledged. The copilot never has an override.

## Considered Options

- Always reject illegal states: corrections would have to be made downstream first.
- Always accept and flag: live typos would go unnoticed.

## Amendment (2026-11-26): what an acknowledgement covers

An acknowledgement stores a fingerprint of the rule, the action and the cause. The Violation is Acknowledged while they match it, and Open if any of them differs and a rule is still broken. If all three match exactly again, for example after a correction is reversed, the acknowledgement applies again. A correction followed by its reversal therefore restores the same derived state.

## Amendment (2026-11-27): duplicate occurrence and correction feedback

When the Series' rules prohibit the same Character more than once in a Game, every occurrence after the first in Draft Order carries the duplicate Violation, regardless of which action was edited or when it was entered. The first occurrence does not carry that duplicate Violation. Saving a correction that creates a Violation on another action immediately explains the affected action, for example, "This correction makes turn 10 a duplicate", so the analyst can connect the edit to the untouched action now flagged.
