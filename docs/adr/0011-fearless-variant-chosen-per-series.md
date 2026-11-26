# Fearless variant is chosen per Series

Scrims and tournaments of the same Title use different Fearless rules, and scrims invent their own, so the variant cannot be fixed by the Title profile. Each Series chooses it as two settings, lock reach (none, picking Team, both Teams) and lock sources (picks, or picks and bans), and any valid combination is allowed. The Title profile only provides named presets (Off, Soft, Hard) and a default; any other combination is labelled Custom. Changing the variant or another rule setting on an existing Series first shows an impact summary (Violations created or cleared, Players whose Remaining Pool changes), then everything is recomputed.

Supersedes the part of [ADR 0001](0001-title-agnostic-engine.md) saying that the Fearless variant comes from the Title profile. The rest of 0001 stands.

## Considered Options

- The variant comes only from the Title profile: one rule per Title is wrong for some tournaments and scrims.
- The profile whitelists the allowed variants: blocks invented scrim formats that the engine already supports.

## Amendment (2026-11-26): picking Team with bans is not valid

Lock reach "picking Team" together with lock sources "picks and bans" is rejected with a clear error when a Custom variant is validated. No known format uses it, and inventing which Team a ban locks the Character for risks getting it wrong. Reach "both Teams" with bans stays allowed, since the lock is unambiguous. Revisit when a real format needs it.
