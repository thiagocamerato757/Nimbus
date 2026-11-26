# Structural invariants are absolute; game rules can be overridden

Nimbus records what happened on stage, which can contradict the rules it knows because of a league ruling, a wrong earlier entry or a wrong profile. Structural invariants (one Draft Action per turn, the turn exists in the Draft Order, the Character exists in the Character Catalog) can never be overridden. Game rules from the Series' rule settings (taken from the Title profile, [ADR 0013](0013-series-snapshots-rule-settings.md)) reject a live entry but can be overridden with a reason (category and optional note), and corrections are always saved. The resulting Violations are derived, never block or auto-change anything, and are either Open or Acknowledged. The copilot never has an override.

## Considered Options

- Always reject illegal states: corrections would have to be made downstream first.
- Always accept and flag: live typos would go unnoticed.
