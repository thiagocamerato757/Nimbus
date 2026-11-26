---
status: accepted, partially superseded by ADR-0011 (Fearless variant) and ADR-0012 (draft order)
---

# The engine is title-agnostic; rules come from Title profiles

Nimbus starts with League of Legends and will add Deadlock, whose tournaments each define their own draft format. Team size, draft order, Character Catalog and Fearless variant therefore come from a Title profile (a data file) and never from code, so that adding a Title means adding a profile rather than changing the engine.

**Partially superseded:** the Fearless variant is now chosen per Series ([ADR 0011](0011-fearless-variant-chosen-per-series.md)), and so is the Draft Order, from those the profile names ([ADR 0012](0012-draft-order-chosen-per-series.md)).
