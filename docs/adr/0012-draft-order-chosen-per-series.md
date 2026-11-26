# Draft Order is chosen per Series from the profile's named orders

Tournaments of one Title can use different Draft Orders, so a Title profile lists one or more named orders with a default, and each Series picks one. Each order has a stable id (for example `lol-pro-2026`) separate from its display name. Loading a profile validates every order (each turn has a Draft Position and a type, picks per Draft Position equal the team size, ids are unique), so a broken order fails at load time and never mid-Series. A Series can switch order only if every recorded Draft Action still fits it (same turn, same type), after an impact preview.

Supersedes the part of [ADR 0001](0001-title-agnostic-engine.md) saying that the profile fixes the draft order. Orders are still defined only in Title profiles.

## Considered Options

- One order per profile: a new tournament format would mean duplicating the whole profile and Character Catalog.
- Orders edited freely per Series: needs an order editor, and a long sequence typed in a hurry is easy to get wrong. This is why Draft Orders are treated differently from the two Fearless settings ([ADR 0011](0011-fearless-variant-chosen-per-series.md)).
